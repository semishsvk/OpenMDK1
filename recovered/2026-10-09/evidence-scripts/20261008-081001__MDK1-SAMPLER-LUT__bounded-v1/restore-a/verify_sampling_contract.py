"""Tie source material descriptors to tested original address/dispatch mechanisms.
No pixel visibility claim; UV transforms and live variant choice remain gates.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK,STOP
from verify_material_plan_v2 import model_descriptor
from geometry_contract import SOURCE,PINS,sha,u32
from static_probe import ROOT,load,offset,PIN
DESC,VERT=0x10010000,0x10020000
TEX=0x20000000


def guarded_run(uc,start,end,allow,write_ranges):
    state={'done':False,'instructions':0}
    def code(u,addr,size,_):
        state['instructions']+=1
        if addr==end:state['done']=True;u.emu_stop();return
        if not any(a<=addr and addr+size<=b for a,b in allow):raise ValueError('ADDRESS_TEST_PC_ESCAPE')
    def write(u,access,addr,size,value,_):
        if not any(a<=addr and addr+size<=b for a,b in write_ranges):raise ValueError('ADDRESS_TEST_WRITE_ESCAPE:'+hex(addr))
    ch=uc.hook_add(UC_HOOK_CODE,code);wh=uc.hook_add(UC_HOOK_MEM_WRITE,write)
    try:uc.emu_start(start,end+1,timeout=200000,count=1000)
    finally:uc.hook_del(ch);uc.hook_del(wh)
    if not state['done']:raise ValueError('ADDRESS_TEST_NOT_FINISHED')
    return state['instructions']


def install_table(u,variant):
    exe,sections=load();ptr=0x49bcb4 if variant else 0x49bce4
    expected=exe[offset(sections,ptr,48):offset(sections,ptr,48)+48]
    w32(u,STACK,STOP);u.reg_write(UC_X86_REG_EAX,variant);u.reg_write(UC_X86_REG_ESP,STACK)
    guarded_run(u,0x46da6c,STOP,[(0x46da6c,0x46daa9)],[(STACK-128,STACK+8),(0x54dc00,0x54dc30)])
    if bytes(u.mem_read(0x54dc00,48))!=expected:raise ValueError('CALLBACK_TABLE_NOT_SOURCE_IDENTICAL')
    return struct.unpack('<12I',expected)


def routing(variant,flags,perspective,alternate=0):
    u=machine();table=install_table(u,variant);w32(u,DESC+12,flags)
    u.reg_write(UC_X86_REG_EBP,STACK);u.reg_write(UC_X86_REG_EAX,DESC);w32(u,STACK+8,VERT)
    if perspective:
        # Valid x87 precondition for the original scratch store; this does not model
        # preceding perspective interpolation. Execute the pinned FLDZ instruction only.
        u.emu_start(0x409aae,0x409ab0,count=1)
        w32(u,0x5414b8,alternate)
        guarded_run(u,0x46deb6,0x46dedb,[(0x46deb6,0x46dedb)],[(0x54ec88,0x54ec8c)])
        observed=u.reg_read(UC_X86_REG_EBX);expected=table[(flags&3)|(4 if alternate else 0)]
    else:
        guarded_run(u,0x46e53b,0x46e54e,[(0x46e53b,0x46e54e)],[(STACK-40,STACK-36)])
        observed=r32(u,STACK-40);expected=table[8+(flags&3)]
    if observed!=expected:raise ValueError('ORIGINAL_CALLBACK_ROUTING_MISMATCH')
    return observed


def address(desc,u_fixed,v_fixed):
    uc=machine();uc.mem_write(DESC,desc);w32(uc,DESC+36,TEX)
    w32(uc,STACK-44,u_fixed);w32(uc,STACK-36,v_fixed)
    uc.reg_write(UC_X86_REG_ESI,DESC);uc.reg_write(UC_X86_REG_EDI,VERT);uc.reg_write(UC_X86_REG_EBP,STACK)
    uc.mem_write(VERT+12,struct.pack('<f',0.))
    guarded_run(uc,0x46e75e,0x46e7a7,[(0x46e75e,0x46e7a7)],
        [(STACK-12,STACK-8),(0x54ebdc,0x54ebe0),(0x54ebd4,0x54ebd8),(0x54ebe0,0x54ebe4)])
    shift,wmask,hmask=struct.unpack_from('<I',desc)[0],u32(desc,16),u32(desc,20)
    expected=((u_fixed>>16)&wmask)+((v_fixed>>(16-shift))&hmask)
    if r32(uc,0x54ebd4)!=TEX+expected or r32(uc,0x54ebe0)!=(wmask|hmask) or r32(uc,0x54ebdc)!=TEX:
        raise ValueError('ORIGINAL_ADDRESS_SETUP_MISMATCH')
    return expected


def main():
    baseline_path=ROOT/'baseline-material-sourceir.json'
    if sha(baseline_path.read_bytes())!='b597a9f27d5e03b34117d02d893a6e8b456406c8d413a2dd73276e96db32e783':raise ValueError('BASELINE_IR_CHANGED')
    ir=json.loads(baseline_path.read_bytes());raw={n:(SOURCE/n).read_bytes() for n in PINS}
    if any(sha(raw[n])!=p for n,p in PINS.items()):raise ValueError('CORPUS_CHANGED')
    mto=raw['LEVEL3O.MTO'];blobs={'LEVEL3S.MTI':raw['LEVEL3S.MTI'][4:]}
    for i in range(u32(mto,20)):
        q=24+i*12;start=u32(mto,q+8);end=u32(mto,q+20) if i+1<u32(mto,20) else len(mto)
        name=mto[q:q+8].split(b'\0')[0].decode('ascii')
        blobs[name+'.MAT']=mto[start+20:end]
    refcounts=Counter((r['material_provider'],r['material_ordinal']) for r in ir['records'] if r['kind']=='TEXTURE_REFERENCE')
    materials=[m for values in ir['materials'].values() for m in values if (m['provider'],m['ordinal']) in refcounts]
    if len(materials)!=67:raise ValueError('ACTIVE_DESCRIPTOR_SET_CHANGED')
    cases=[];profiles=[];flagcounts=Counter();shape_counts=Counter()
    tables={variant:install_table(machine(),variant) for variant in (0,1)}
    for variant in (0,1):
        for flags in [0,1,2,3,4,7,0x10002,0xffffffff]:
            for perspective,alternate in [(False,0),(True,0),(True,1)]:
                target=routing(variant,flags,perspective,alternate)
                cases.append({'case':'routing','variant':variant,'flags':flags,'perspective':perspective,'alternate':alternate,'target':hex(target),'pass':True})
    for m in materials:
        descriptor,model=model_descriptor(blobs[m['provider']],m['ordinal'])
        if model['first_plane_sha256']!=m['first_plane_sha256']:raise ValueError('MATERIAL_PAYLOAD_CHANGED')
        width,height=m['width'],m['height'];flags=m['runtime_flags'];refs=refcounts[(m['provider'],m['ordinal'])]
        flagcounts[flags]+=refs;shape_counts[(width,height,flags)]+=1
        coordinates=[(0,0),(65535,65535),(-1,-1),(-65536,-65536),(width*65536,0),
          ((width-1)*65536,0),(0,height*65536),(0,(height-1)*65536),
          ((width+3)*65536+123,(height+2)*65536+456),(-3*65536+123,-2*65536+456)]
        outside=0
        for u,v in coordinates:
            result=address(descriptor,u,v)
            if result>=width*height:outside+=1
            cases.append({'case':'descriptor_address','provider':m['provider'],'ordinal':m['ordinal'],
                'u_fixed':u,'v_fixed':v,'offset':result,'within_payload':result<width*height,'pass':True})
        profiles.append({'provider':m['provider'],'ordinal':m['ordinal'],'name':m['name'],'references':refs,
           'width':width,'height':height,'runtime_flags':flags,'affine_keyed':bool(flags&1),
           'affine_per_sample_mask':bool(flags&2),'is_height_power_of_two':not height&(height-1),
           'width_mask':u32(descriptor,16),'height_mask_shifted':u32(descriptor,20),
           'unconstrained_test_coordinates_outside_payload':outside,
           'affine_callback_by_variant':{str(v):hex(tables[v][8+(flags&3)]) for v in tables},
           'scope':'Descriptor and kernel routing verified; allowed runtime UV domain not yet established.'})
    # A negative example against treating a bitmask as conventional independent U/V wrap.
    wrap_counterexample={'width':8,'height':8,'initial_u':7,'du':1,
       'combined_linear_offsets':[7,8,9],'independent_uv_repeat_offsets':[7,0,1]}
    if flagcounts!=Counter({0:sum(refcounts.values())-flagcounts[2],2:flagcounts[2]}):raise ValueError('NEW_MATERIAL_FLAG_CLASS')
    if not all(sha((SOURCE/n).read_bytes())==p for n,p in PINS.items()):raise ValueError('CORPUS_CHANGED_DURING_TEST')
    report={'schema':'OpenMDK1.SamplingMaterialContract.v1','status':'PASS','tests':len(cases)+2,
       'routing_cases':48,'address_cases':len(cases)-48,'table_copy_cases':2,'cases':cases,
       'active_material_descriptors':len(materials),'active_texture_references':sum(refcounts.values()),
       'reference_counts_by_flags':dict(flagcounts),'active_nonpower_height_descriptors':sum(not p['is_height_power_of_two'] for p in profiles),
       'active_keyed_descriptors':sum(p['affine_keyed'] for p in profiles),
       'active_wrapped_descriptors':sum(p['affine_per_sample_mask'] for p in profiles),
       'profiles':profiles,'callback_tables':{str(v):[hex(x) for x in table] for v,table in tables.items()},
       'address_rule':'((u_16_16 >> 16) & width_mask) + ((v_16_16 >> (16-width_shift)) & height_mask_shifted)',
       'wrapped_sampling_rule':'Combined linear-address mask in the selected kernel; not independent U/V clamp or modulo height.',
       'counterexample_to_generic_repeat':wrap_counterexample,
       'envelope_warning':'Non-power-of-two source heights are retained. A rounded address mask alone does not establish a safe arbitrary UV domain; out-of-payload mathematical fixtures are classified, not read or treated as valid content.',
       'game_runtime_executed':False,'production_promotion':False,'fidelity_verified':False,
       'source_exe_sha256':PIN,'source_corpus_sha256':PINS,'baseline_sourceir_unchanged':True,
       'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'sampling-material-contract.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k not in {'cases','profiles'}},indent=2))
    print('REPORT_SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
