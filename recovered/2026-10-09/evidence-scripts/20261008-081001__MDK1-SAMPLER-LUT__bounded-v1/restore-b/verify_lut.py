"""Original LUT span and LUT-generator mechanism tests in isolated x86 memory.
No full game, native code execution, host APIs, GPU or production renderer.
All loops, writes and instruction counts are explicitly bounded.
"""
from datetime import datetime,timezone
from collections import Counter
import itertools,json,struct
import unicorn
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK,STOP
from static_probe import ROOT,load,offset,PIN,sha
LUT,DEST,ROOTNODE,LEAVES,TINT=0x10001000,0x10002000,0x10010000,0x10020000,0x10030000
SPAN_BLOCKS=[(0x412a55,0x412aab),(0x412acf,0x412b25),(0x412b84,0x412bda),(0x412c09,0x412c5f)]

def check_span(code_range,table,data,pad):
    begin,end=code_range;n=len(data)
    if len(table)!=256 or n>600 or not 0<=pad<=16:raise ValueError('SPAN_BUDGET')
    u=machine();u.mem_write(LUT,table);guard=bytes([0xA5])*16
    initial=guard+bytes([0x5a])*pad+data+guard;ptr=DEST+16+pad
    u.mem_write(DEST,initial)
    for r,v in [(UC_X86_REG_ESI,LUT),(UC_X86_REG_EDI,ptr),(UC_X86_REG_ECX,n),(UC_X86_REG_ESP,STACK),(UC_X86_REG_EBP,0)]:u.reg_write(r,v)
    state={'done':False,'writes':0,'instructions':0}
    def code(uc,addr,size,_):
        state['instructions']+=1
        if addr==end:state['done']=True;uc.emu_stop();return
        if not begin<=addr<end:raise ValueError('SPAN_PC_ESCAPE')
    def write(uc,access,addr,size,value,_):
        if STACK<=addr and addr+size<=STACK+0x60:return
        if not ptr<=addr or addr+size>ptr+n:raise ValueError('SPAN_WRITE_ESCAPE')
        state['writes']+=size
    u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
    u.emu_start(begin,end+1,timeout=200000,count=15000)
    if not state['done']:raise ValueError('SPAN_NO_COMPLETION')
    actual=bytes(u.mem_read(DEST,len(initial)))
    expected=initial[:16+pad]+bytes(table[x] for x in data)+guard
    if actual!=expected or state['writes']!=n:raise ValueError('LUT_SPAN_DIFFERENCE')
    if bytes(u.mem_read(LUT,256))!=table:raise ValueError('LUT_MUTATED')
    return state['instructions']

def tree(u,palette,missing=(),leaf_base=0):
    if len(palette)!=256:raise ValueError('PALETTE_LENGTH')
    u.mem_write(ROOTNODE,bytes([128,128,128,0])+bytes(36))
    for i in range(8):
        addr=LEAVES+i*40
        u.mem_write(addr,bytes([0,0,0,7])+struct.pack('<I',leaf_base+i)+bytes(32))
        w32(u,ROOTNODE+8+4*i,0 if i in missing else addr)
    u.mem_write(ROOTNODE+40,b''.join(bytes(rgb)+b'\0' for rgb in palette))

def generator(palette,tint,weight):
    if not 0<=weight<=256 or len(tint)!=3:raise ValueError('WEIGHT_BUDGET')
    u=machine();tree(u,palette);u.mem_write(TINT,bytes(tint));u.mem_write(LUT,bytes(256))
    w32(u,STACK,STOP)
    for r,v in [(UC_X86_REG_EAX,ROOTNODE),(UC_X86_REG_EDX,TINT),(UC_X86_REG_EBX,weight),(UC_X86_REG_ECX,LUT),(UC_X86_REG_ESP,STACK)]:u.reg_write(r,v)
    state={'done':False,'count':0,'queries':[]}
    def code(uc,addr,size,_):
        state['count']+=1
        if addr==STOP:state['done']=True;uc.emu_stop();return
        if addr==0x406e24:state['queries'].append(tuple(uc.mem_read(uc.reg_read(UC_X86_REG_EDX),3)))
        if not (0x406d84<=addr<0x406e21 or 0x406e24<=addr<0x406ec2):raise ValueError('LUT_GENERATOR_PC_ESCAPE')
    def write(uc,access,addr,size,value,_):
        if STACK-256<=addr and addr+size<=STACK+8:return
        if not LUT<=addr or addr+size>LUT+256:raise ValueError('LUT_GENERATOR_WRITE_ESCAPE')
    u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
    u.emu_start(0x406d84,STOP+1,timeout=1200000,count=80000)
    if not state['done'] or len(state['queries'])!=256:raise ValueError('LUT_GENERATOR_INCOMPLETE')
    expected_rgb=[tuple((p*(256-weight)+t*weight)//256 for p,t in zip(rgb,tint)) for rgb in palette]
    expected=bytes(sum((c>=128)<<k for k,c in enumerate(rgb)) for rgb in expected_rgb)
    observed=bytes(u.mem_read(LUT,256))
    if observed!=expected or state['queries']!=expected_rgb:raise ValueError('LUT_GENERATION_MODEL_MISMATCH')
    return {'weight':weight,'tint':tint,'rgb_queries':256,'instructions':state['count'],'table_sha256':sha(observed)}

def lookup(rgb,missing,mask_order):
    u=machine();tree(u,[(0,0,0)]*256,missing);u.mem_write(TINT,bytes(rgb));w32(u,STACK,STOP)
    for r,v in [(UC_X86_REG_EAX,ROOTNODE),(UC_X86_REG_EDX,TINT),(UC_X86_REG_ESP,STACK)]:u.reg_write(r,v)
    state={'done':False}
    def hook(uc,addr,size,_):
        if addr==STOP:state['done']=True;uc.emu_stop();return
        if not 0x406e24<=addr<0x406ea8:raise ValueError('LOOKUP_NO_ALLOWED_LEAF')
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x406e24,STOP+1,timeout=200000,count=600)
    if not state['done']:raise ValueError('LOOKUP_INCOMPLETE')
    octant=sum((c>=128)<<k for k,c in enumerate(rgb))
    expected=next(i for i in [octant]+[octant^m for m in mask_order] if i not in missing)
    if u.reg_read(UC_X86_REG_EAX)!=expected:raise ValueError('LOOKUP_MODEL_MISMATCH')
    return expected

def main():
    checks=[];tested_values=set();span_counts=Counter()
    tables=[bytes(range(256)),bytes(reversed(range(256))),bytes((i*73+19)&255 for i in range(256)),bytes([0])*256,bytes(i//4 for i in range(256))]
    lengths=[0,1,2,3,4,5,7,8,15,31,32,33,255,256,257,511]
    for bi,block in enumerate(SPAN_BLOCKS):
        for ti,table in enumerate(tables):
            for n in lengths:
                for pad in (0,3):
                    data=bytes(i&255 for i in range(n));tested_values.update(data)
                    count=check_span(block,table,data,pad);span_counts[hex(block[0])]+=1
                    checks.append({'case':f'span{bi}-table{ti}-n{n}-pad{pad}','pass':True,'instructions':count})
    palette=[(i,(i*53+7)&255,255-i) for i in range(256)]
    generated=[]
    for tint in [(0,0,0),(255,255,255),(13,127,241),(128,128,128)]:
        for weight in (0,1,64,127,128,255,256):
            observation=generator(palette,tint,weight);generated.append(observation)
            checks.append({'case':f'generator-{tint}-{weight}','pass':True})
    b,sections=load();at=offset(sections,0x499f04,7);order=list(b[at:at+7])
    if order!=[1,2,4,3,5,6,7]:raise ValueError('LOOKUP_FALLBACK_ORDER_CHANGED')
    for rgb in itertools.product((0,127,128,255),repeat=3):
        octant=sum((c>=128)<<k for k,c in enumerate(rgb))
        for missing in [(),(octant,),(octant,octant^1,octant^2)]:
            lookup(rgb,missing,order);checks.append({'case':f'lookup-{rgb}-missing{missing}','pass':True})
    # This is a falsification of generic nearest-RGB replacement, not the live palette tree.
    # Complete octant tree uses branch identity. Numeric index does not encode RGB distance.
    report={'schema':'OpenMDK1.LUTPixelMechanism.v1','status':'PASS','tests':len(checks),'checks':checks,
        'span_cases':sum(span_counts.values()),'span_blocks':dict(span_counts),'all_256_input_indices_tested':len(tested_values)==256,
        'generator_cases':len(generated),'generator_observations':generated,'lookup_cases':192,
        'rules':{'covered_destination':'output_index = lookup_table[existing_destination_index]',
            'table_generation_rgb':'floor((palette_component*(256-weight) + tint_component*weight)/256)',
            'palette_lookup':'original octant-tree traversal using >= component thresholds; deterministic XOR fallback order when a selected branch is absent',
            'fallback_masks':order,'palette_index_quantization':'not established as Euclidean nearest-color search'},
        'source_exe_sha256':PIN,'unicorn_version':unicorn.__version__,'native_game_executed':False,
        'production_renderer_modified':False,'fidelity_verified':False,
        'limits':['Synthetic supplied tables and color trees test the mechanism; actual LEVEL3 tint/state/palette-tree instances are not sealed here.',
            'Span endpoints are direct entry fixtures; triangle coverage/clipping not part of this gate.',
            'This is index-space destination remapping, not proof that a generic GPU alpha blend reproduces original pixels.'],
        'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'lut-mechanism-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k not in {'checks','generator_observations'}},indent=2))
    print('REPORT_SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
