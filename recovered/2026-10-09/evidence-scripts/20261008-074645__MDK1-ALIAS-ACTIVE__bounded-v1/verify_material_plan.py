"""Iteration 3: actual source descriptor construction and evidence-only binding IR.
Original loader runs only in synthetic memory with bounded allocation/zero-fill
stubs. No original OS/library code, rasterizer, native game or production writes.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,math,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STOP,STACK
from geometry_contract import corpus,initialized_flags,SOURCE,PINS,take,u32,name,sha
from static_probe import ROOT
BLOB,DESCS,COUNT_PTR,ARRAY_PTR,ALLOC=0x20000000,0x30000000,0x10002000,0x10003000,0x100f0000

def model_descriptor(blob,ordinal):
    q=20+ordinal*24;rec=take(blob,q,24);kind=u32(rec,8);d=bytearray(52);d[40:48]=rec[:8]
    if kind==0xffffffff:
        struct.pack_into('<I',d,8,u32(rec,12));struct.pack_into('<I',d,12,0xffffffff)
        return bytes(d),{'name':name(rec[:8]),'kind':'NONPAYLOAD_CONSTANT','constant':u32(rec,12),'record_offset':q}
    rel=u32(rec,20)
    if (kind>>16)&3:
        header=take(blob,rel,8);extra=struct.unpack_from('<H',header)[0];w,h=struct.unpack_from('<HH',header,4);header_size=8
    else:
        extra=0;w,h=struct.unpack('<HH',take(blob,rel,4));header_size=4
    if not 0<w<=4096 or not 0<h<=4096:raise ValueError('DIMENSION_BUDGET')
    # Ensure a bounded addressable plane, without claiming animation/blend semantics.
    pixels=take(blob,rel+header_size,w*h)
    exponent=min(12,(w-1).bit_length());wmask=(1<<exponent)-1
    if h==w:hmask=wmask<<exponent
    else:
        bucket=next((v for v in (16,32,64,128,256,512,1024) if h<=v),1024)
        hmask=(bucket-1)<<exponent
    values=(exponent,w,h,(kind&65535)|(extra<<16),wmask,hmask,(~wmask)&0xffffffff)
    struct.pack_into('<7I',d,0,*values);d[28:36]=rec[12:20];struct.pack_into('<I',d,36,BLOB+rel+header_size)
    return bytes(d),{'name':name(rec[:8]),'kind':'TEXTURE_DESCRIPTOR','record_offset':q,
        'width':w,'height':h,'runtime_flags':values[3],'header_bytes':header_size,
        'payload_offset':rel+header_size,'first_plane_sha256':sha(pixels),
        'uv_parameter_raw_hex':rec[12:20].hex(),'raster_semantics_verified':False}

def original_descriptors(blob):
    n=u32(blob,16)
    if not 1<=n<=1024 or len(blob)>4*1024*1024:raise ValueError('DESCRIPTOR_SOURCE_BUDGET')
    u=machine();u.mem_map(BLOB,(len(blob)+4095)&~4095);u.mem_write(BLOB,blob)
    u.mem_map(DESCS,0x10000)
    for reg,value in [(UC_X86_REG_EAX,BLOB),(UC_X86_REG_EDX,COUNT_PTR),(UC_X86_REG_EBX,ARRAY_PTR),
                      (UC_X86_REG_ECX,ALLOC),(UC_X86_REG_ESP,STACK)]:u.reg_write(reg,value)
    w32(u,STACK,STOP);state={'returned':False,'instructions':0,'allocations':0,'zero_fills':0}
    def ret(uc):
        sp=uc.reg_read(UC_X86_REG_ESP);uc.reg_write(UC_X86_REG_EIP,r32(uc,sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
    def hook(uc,addr,size,_):
        state['instructions']+=1
        if addr==STOP:state['returned']=True;uc.emu_stop();return
        if addr==ALLOC:
            if uc.reg_read(UC_X86_REG_EAX)!=n*52 or state['allocations']:raise ValueError('ALLOCATION_CONTRACT')
            state['allocations']+=1;uc.reg_write(UC_X86_REG_EAX,DESCS);ret(uc);return
        if addr==0x47d20a:
            if (uc.reg_read(UC_X86_REG_EAX),uc.reg_read(UC_X86_REG_EDX),uc.reg_read(UC_X86_REG_EBX))!=(DESCS,0,n*52):raise ValueError('ZEROFILL_CONTRACT')
            state['zero_fills']+=1;uc.mem_write(DESCS,bytes(n*52));ret(uc);return
        if not 0x41a1e0<=addr<0x41a46c:raise ValueError('UNEXPECTED_LOADER_ADDRESS:'+hex(addr))
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x41a1e0,STOP+1,timeout=1500000,count=300000)
    if not state['returned'] or r32(u,COUNT_PTR)!=n or r32(u,ARRAY_PTR)!=DESCS:raise ValueError('LOADER_OUTPUT_INCOMPLETE')
    return bytes(u.mem_read(DESCS,52*n)),state

def main():
    parts,_=corpus();m=(SOURCE/'LEVEL3S.MTI').read_bytes();b=(SOURCE/'LEVEL3O.MTO').read_bytes()
    providers=[{'id':'LEVEL3S.MTI','blob':m[4:],'source_file':'LEVEL3S.MTI','base_offset':4}]
    for i,part in enumerate(parts):
        start=u32(b,32+12*i);end=u32(b,44+12*i) if i+1<len(parts) else len(b)
        providers.append({'id':part['name']+'.MAT','blob':b[start+20:end],'source_file':'LEVEL3O.MTO','base_offset':start+20})
    checks=[];catalog={}
    for p in providers:
        count=u32(p['blob'],16);pairs=[model_descriptor(p['blob'],i) for i in range(count)]
        expected=b''.join(x for x,_ in pairs);observed,state=original_descriptors(p['blob'])
        if observed!=expected:raise ValueError('ORIGINAL_DESCRIPTOR_MISMATCH:'+p['id'])
        checks.append({'test':p['id']+'_descriptor_bytes','pass':True,'descriptors':count,
             'bytes_compared':len(expected),'instructions':state['instructions'],'stub_counts':{'allocation':state['allocations'],'zero_fill':state['zero_fills']}})
        catalog[p['id']]=[]
        for i,(_,record) in enumerate(pairs):
            record.update(provider=p['id'],ordinal=i,source_file=p['source_file'],source_file_sha256=PINS[p['source_file']],
                raw_record_offset=p['base_offset']+record['record_offset'],runtime_descriptor_sha256=sha(observed[i*52:i*52+52]))
            if 'payload_offset' in record:record['raw_payload_offset']=p['base_offset']+record['payload_offset']
            catalog[p['id']].append(record)
    totals=Counter();records=[]
    def resolve(candidates,n):return next((x for x in candidates if x['name']==n),None)
    for part in parts:
        primary=catalog['LEVEL3S.MTI'];secondary=catalog[part['name']+'.MAT']
        for t in part['triangles']:
            eligible=not initialized_flags(t['flag32']&255)&16
            row={'hmo':part['name'],'source_record':t['index'],'raw_file_offset':t['raw_file_offset'],
                'raw_f3':t['f3'],'raw_flags':t['flag32'],'post_init_flags_low_byte':initialized_flags(t['flag32']&255),
                'eligible_at_prefilter':eligible,'zero_area':t['zero_area']}
            totals['raw_records']+=1
            if not eligible:
                row['kind']='INACTIVE_AT_INITIALIZED_PREFILTER';totals['inactive_records']+=1
                # Preserve, do not erase or automatically turn it into a missing texture.
            elif t['f3']<0:
                row['kind']='NEGATIVE_RENDER_CODE';row['render_code']=t['f3'];totals['negative_render_codes']+=1
            else:
                material=resolve(primary,t['name']) or resolve(secondary,t['name'])
                if material is None or material['kind']!='TEXTURE_DESCRIPTOR':raise ValueError('ACTIVE_NONPAYLOAD_OR_UNRESOLVED_MATERIAL')
                row.update(kind='TEXTURE_REFERENCE',material_provider=material['provider'],material_ordinal=material['ordinal'],
                    material_name=material['name'],source_payload_sha256=material['first_plane_sha256'])
                totals['texture_references']+=1
                totals['primary_texture_references' if material['provider']=='LEVEL3S.MTI' else 'secondary_texture_references']+=1
                if t['f3']==0:totals['texture_references_with_zero_index']+=1
            records.append(row)
    if totals['raw_records']!=7205 or totals['texture_references']+totals['negative_render_codes']+totals['inactive_records']!=7205:raise ValueError('CLASSIFICATION_PARTITION')
    if not all(sha((SOURCE/n).read_bytes())==h for n,h in PINS.items()):raise ValueError('SOURCE_CHANGED')
    ir={'schema':'OpenMDK1.MaterialBindingSourceIR.v1','scope':'EVIDENCE_ONLY_NOT_RUNTIME_BINDING',
       'source_sha256':PINS,'authority':'CORPUS_BYTES_AND_ORIGINAL_INSTRUCTION_MICROTEST',
       'initialization_contract':'zero group-state masks; bit2 promotes bits 0x30, draw prefilter tests 0x10',
       'provider_order':['LEVEL3S.MTI','current_HMO.MAT'],'materials':catalog,'records':records,
       'multiplicity_preserved':True,'raw_records_dropped':0,'pixel_fidelity_verified':False,
       'visibility_policy':'Per-camera BSP range selection and clipping are separate. eligible_at_prefilter is not visible.'}
    irpath=ROOT/'material-binding-sourceir.json'
    with irpath.open('x',encoding='utf-8') as f:json.dump(ir,f,sort_keys=True,separators=(',',':'))
    report={'schema':'OpenMDK1.MaterialPlanVerification.v1','status':'PASS','tests':len(checks)+2,
       'checks':checks+[{'test':'7205_record_partition','pass':True},{'test':'all_eligible_nonnegative_refs_have_source_payload','pass':True}],
       'counts':dict(totals),'providers':len(providers),'descriptors_verified':sum(len(x) for x in catalog.values()),
       'sourceir_sha256':sha(irpath.read_bytes()),'sourceir_bytes':irpath.stat().st_size,
       'runtime_descriptor_comparison':'All 52 bytes per descriptor compared at a fixed synthetic source base, including names, pointer offsets, dimensions, masks, raw UV parameters and nonpayload constants.',
       'stubs':'Only exact-size synthetic allocation and exact-range zero-fill, checked per call.',
       'game_runtime_executed':False,'production_binding_installed':False,'pixel_fidelity_verified':False,
       'remaining':['Real camera/visibility and dynamic-state validation.','Texture sampler/wrapping, LUT pixel operations and render order fidelity.','Production renderer binding requires admission and original-runtime comparison.'],
       'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'material-plan-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
    print('REPORT_SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
