"""Bounded original-instruction microtests plus read-only LEVEL3 crosswalk.
Not a game runtime, renderer or native worker: only whitelisted x86 instruction
ranges run in Unicorn with synthetic memory. No OS calls or source writes.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,struct
import unicorn
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import *
from static_probe import load,offset,ROOT,PIN,SOURCE,sha

MTO=Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO')
MTI=MTO.with_name('LEVEL3S.MTI')
MTO_PIN='6f33536701f57a404f8b25aa5580502cd68389de9ae591b53b018f415f7193ff'
LOCAL,SHARED,NAMES,TABLE,REF=0x10001000,0x10010000,0x10020000,0x10030000,0x10040000
STACK,STOP=0x100e0000,0x100ff000
REGS={'eax':UC_X86_REG_EAX,'ebx':UC_X86_REG_EBX,'ecx':UC_X86_REG_ECX,'edx':UC_X86_REG_EDX,'esi':UC_X86_REG_ESI,'edi':UC_X86_REG_EDI,'esp':UC_X86_REG_ESP,'ebp':UC_X86_REG_EBP}
CODE,SECTIONS=load()

def u32(b,o):
    if o<0 or o+4>len(b):raise ValueError('OUT_OF_BOUNDS_U32')
    return struct.unpack_from('<I',b,o)[0]
def name(b):return b.split(b'\0',1)[0].decode('ascii')
def save(n,d):
    raw=(json.dumps(d,sort_keys=True,indent=2)+'\n').encode()
    with (ROOT/n).open('xb') as f:f.write(raw)
    return sha(raw)
def machine():
    u=Uc(UC_ARCH_X86,UC_MODE_32)
    u.mem_map(0x400000,0x180000)
    for _,vs,va,rs,rp in SECTIONS:
        if va<0x400000 or va+rs>0x580000:raise ValueError('IMAGE_MAP_BUDGET')
        if rs:u.mem_write(va,CODE[rp:rp+rs])
    u.mem_map(0x10000000,0x100000)
    u.reg_write(UC_X86_REG_ESP,STACK)
    return u
def w32(u,p,v):u.mem_write(p,struct.pack('<I',v&0xffffffff))
def r32(u,p):return struct.unpack('<I',u.mem_read(p,4))[0]
def descriptor_names(u,base,names):
    if len(names)>1024:raise ValueError('DESCRIPTOR_BUDGET')
    for i,n in enumerate(names):
        raw=n.encode('ascii')
        if len(raw)>8 or b'\0' in raw:raise ValueError('DESCRIPTOR_NAME_BUDGET')
        u.mem_write(base+i*52+40,raw+b'\0')

def resolver_model(names,primary,secondary,fallback=0):
    if not primary:return [0]*len(names)
    return [LOCAL+primary.index(n)*52 if n in primary else SHARED+secondary.index(n)*52 if n in secondary else fallback for n in names]

def original_resolver(names,primary,secondary,fallback=0):
    if not names or len(names)>512:raise ValueError('NAME_BUDGET')
    u=machine();descriptor_names(u,LOCAL,primary);descriptor_names(u,SHARED,secondary)
    for i,n in enumerate(names):
        raw=n.encode('ascii')
        if len(raw)>9:raise ValueError('GEOMETRY_NAME_TOO_LONG')
        u.mem_write(NAMES+i*10,raw+b'\0')
    for p,v in [(0x54b728,LOCAL),(0x54b72c,len(primary)),(0x54b730,SHARED),(0x54b734,len(secondary)),(0x54b73c,fallback),(REF,TABLE),(STACK,STOP)]:w32(u,p,v)
    u.mem_write(TABLE,b'\xa5'*(len(names)*4))
    for r,v in [('eax',len(names)),('edx',NAMES),('ebx',REF),('ecx',0)]:u.reg_write(REGS[r],v)
    state={'stopped':False,'instructions':0,'memset_stub_calls':0}
    def hook(uc,address,size,_):
        state['instructions']+=1
        if address==STOP:state['stopped']=True;uc.emu_stop();return
        if address==0x47d20a:
            # Only the observed zero-primary-table clearing call is stubbed.
            dest=uc.reg_read(UC_X86_REG_EAX);byte=uc.reg_read(UC_X86_REG_EDX);n=uc.reg_read(UC_X86_REG_EBX)
            if primary or dest!=TABLE or byte!=0 or n!=len(names)*4:raise ValueError('UNEXPECTED_EXTERNAL_CALL')
            uc.mem_write(dest,b'\0'*n);sp=uc.reg_read(UC_X86_REG_ESP)
            uc.reg_write(UC_X86_REG_EIP,r32(uc,sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
            state['memset_stub_calls']+=1;return
        if not (0x41a694<=address<0x41a7f5 or 0x42fa50<=address<0x42fa7d):raise ValueError('UNAUTHORIZED_EMULATION_ADDRESS:'+hex(address))
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x41a694,STOP+1,timeout=500000,count=200000)
    if not state['stopped']:raise ValueError('EMULATION_BUDGET_OR_NO_RETURN')
    return [r32(u,TABLE+4*i) for i in range(len(names))],state

CALLBACKS={0x415260:'flat_routine',0x47a770:'effect_routine',0x412970:'lut_routine',0x46e940:'special_1028',0x46daac:'texture_routine'}
def dispatch_model(code,has_descriptor=True):
    if code>=0:return ('texture_routine',LOCAL+code*52) if has_descriptor else ('flat_routine',255)
    if -1010<=code<=-990:return ('effect_routine',(code+1000)&0xffffffff)
    if -1027<=code<=-1024:return ('lut_routine',SHARED+(-1024-code)*256)
    if code==-1028:return ('special_1028',NAMES)
    if code< -1028:return ('lut_routine',SHARED+(-1029-code)*256)
    return ('flat_routine',-code)

def original_dispatch(code,has_descriptor=True):
    if not -32768<=code<=32767:raise ValueError('NOT_INT16')
    u=machine();w32(u,0x4ce518,TABLE);w32(u,0x540b20,SHARED)
    if code>=0:
        if code>1023:raise ValueError('SYNTHETIC_TABLE_BUDGET')
        desc=LOCAL+code*52
        w32(u,TABLE+code*4,desc if has_descriptor else 0);w32(u,desc+36,REF)
    for reg,value in [('ebx',code&0xffffffff),('esi',NAMES),('edx',NAMES+24),('ecx',NAMES+48),('edi',NAMES+128),('ebp',STACK+0x100)]:u.reg_write(REGS[reg],value)
    state={}
    def hook(uc,addr,size,_):
        if addr in CALLBACKS:
            state.update(callback=CALLBACKS[addr],callback_address=hex(addr),eax=uc.reg_read(UC_X86_REG_EAX))
            uc.emu_stop();return
        if not 0x40c8be<=addr<0x40c9ff:raise ValueError('UNAUTHORIZED_DISPATCH_ADDRESS:'+hex(addr))
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x40c8be,STOP,timeout=200000,count=500)
    if not state:raise ValueError('DISPATCH_DID_NOT_REACH_CALLBACK')
    return (state['callback'],state['eax']),state

def parse_corpus():
    b=MTO.read_bytes();m=MTI.read_bytes()
    if sha(b)!=MTO_PIN:raise ValueError('MTO_CHANGED')
    count=u32(b,20)
    if not 1<=count<=64:raise ValueError('HMO_COUNT_BUDGET')
    directory=[(name(b[24+12*i:32+12*i]),u32(b,32+12*i)) for i in range(count)]
    starts=[p for _,p in directory]
    if starts!=sorted(set(starts)) or starts[0]<24+12*count:raise ValueError('MTO_DIRECTORY_INVALID')
    mtcount=u32(m,20)
    if mtcount>1024 or 24+24*mtcount>len(m):raise ValueError('MTI_NAME_TABLE_INVALID')
    shared_names=[name(m[24+24*i:32+24*i]) for i in range(mtcount)]
    parts=[];totals=Counter();examples=[];allcodes=set()
    for idx,(hn,start) in enumerate(directory):
        end=starts[idx+1] if idx+1<count else len(b);h=b[start:end]
        mc=u32(h,36)
        if 40+mc*24>len(h):raise ValueError('LOCAL_MATERIAL_TABLE_INVALID')
        materials=[]
        for i in range(mc):
            q=40+i*24;mn=name(h[q:q+8]);flags=u32(h,q+8);rel=u32(h,q+20);at=20+rel
            if flags==0xffffffff:raise ValueError('NONPAYLOAD_LOCAL_MATERIAL_REQUIRES_SEPARATE_DECODER')
            if (flags>>16)&3:raise ValueError('EXTENDED_TEXTURE_HEADER_REQUIRES_SEPARATE_DECODER')
            if at<40+mc*24 or at+4>len(h):raise ValueError('INVALID_TEXTURE_OFFSET')
            w,ht=struct.unpack_from('<HH',h,at)
            if w==0 or ht==0 or at+4+w*ht>len(h):raise ValueError('TEXTURE_BOUNDS')
            materials.append({'name':mn,'ordinal':i,'width':w,'height':ht,'payload_raw_offset':start+at,
                'texel_sha256':sha(h[at+4:at+4+w*ht]),'serialized_flags':flags})
        g=u32(h,12)+4;nc=u32(h,g)
        if not 1<=nc<=512 or g+4+10*nc>len(h):raise ValueError('NAME_TABLE_BOUNDS')
        names=[name(h[g+4+10*j:g+14+10*j]) for j in range(nc)]
        po=(g+4+nc*10+3)&~3;pc=u32(h,po);to=po+4+pc*44;tc=u32(h,to);tb=to+4
        if tc>100000 or tb+tc*36>len(h):raise ValueError('TRIANGLE_RECORD_BOUNDS')
        localnames=[d['name'] for d in materials]
        # Conditional registry fixture: exact corpus names, not an assertion that MTI
        # is currently loaded in the live game's primary/secondary provider globals.
        fixture_out,state=original_resolver(names,localnames,shared_names)
        if fixture_out!=resolver_model(names,localnames,shared_names):raise ValueError('CORPUS_NAME_RESOLVER_MISMATCH')
        c=Counter();negative=Counter();unresolved=Counter();zero_names=Counter()
        for ti in range(tc):
            q=tb+36*ti;code=struct.unpack_from('<h',h,q+6)[0];allcodes.add(code);c['records']+=1
            if code<0:c['negative']+=1;negative[code]+=1;continue
            c['nonnegative']+=1;c['positive' if code else 'zero']+=1
            if code>=nc:c['name_index_out_of_range']+=1;continue
            mn=names[code]
            if code==0:
                zero_names[mn]+=1
                if len(set(struct.unpack_from('<3H',h,q)))==1:c['zero_repeated_single_vertex']+=1
            if mn in localnames:
                c['exact_local_payload_name_match']+=1
                if code>0:
                    c['positive_local_match']+=1
                    oldsel=struct.unpack_from('<H',h,q+34)[0]
                    if oldsel%16:raise ValueError('HISTORICAL_SELECTOR_CLASS_CHANGED')
                    old=localnames[(oldsel//16)%mc]
                    c['modulo_agrees' if old==mn else 'modulo_disagrees']+=1
                    if old!=mn and len(examples)<10:examples.append({'hmo':hn,'record':ti,'raw_record_offset':start+q,'f3':code,'by_f3_name':mn,'legacy_modulo_name':old,'raw_selector':oldsel})
            else:
                c['no_local_payload_match']+=1;unresolved[mn]+=1
                if mn in shared_names:c['name_present_in_MTI_candidate']+=1
        totals.update(c)
        parts.append({'hmo':hn,'counts':dict(c),'local_payloads':materials,'negative_histogram':dict(sorted(negative.items())),
             'nonlocal_names':dict(unresolved),'zero_names':dict(zero_names),'name_resolver_fixture_match':True,
             'fixture_instruction_count':state['instructions'],'provider_activation_verified':False})
    if sha(MTO.read_bytes())!=MTO_PIN or MTI.read_bytes()!=m:raise ValueError('CORPUS_CHANGED_DURING_PROBE')
    return {'source_sha256':MTO_PIN,'mti_sha256':sha(m),'totals':dict(totals),'parts':parts,
        'counterexamples':examples,'distinct_f3':sorted(allcodes),'scope':'RAW_RECORD_CENSUS_AND_CONDITIONAL_NAME_CROSSWALK_NOT_VISIBLE_WORLD_POPULATION'}

def main():
    tests=[]
    fixtures=[(['STONE','METAL'],['STONE','METAL'],[],0),(['STONE','stone'],['STONE'],['stone'],0),
      (['SAME'],['SAME','SAME'],['SAME'],0),(['SHARED','NONE'],['LOCAL'],['SHARED'],0),
      (['SHARED'],[],['SHARED'],0),(['MISSING'],['LOCAL'],[],REF),
      (['AB','ABC'],['ABC'],['AB'],0),(['12345678'],['12345678'],[],0)]
    for i,(ns,primary,secondary,fallback) in enumerate(fixtures):
        out,state=original_resolver(ns,primary,secondary,fallback)
        tests.append({'test':'original_resolver_fixture_'+str(i),'pass':out==resolver_model(ns,primary,secondary,fallback),'instructions':state['instructions'],'memset_stub_calls':state['memset_stub_calls']})
    corpus=parse_corpus()
    codes=sorted(set(corpus['distinct_f3'])|{-32768,-1029,-1028,-1027,-1026,-1025,-1024,-1023,-1011,-1010,-1000,-990,-989,-256,-255,-1,0,1,8,255})
    for code in codes:
        actual,details=original_dispatch(code)
        tests.append({'test':'original_dispatch_'+str(code),'f3':code,'pass':actual==dispatch_model(code),'observed':details})
    actual,_=original_dispatch(0,False)
    tests.append({'test':'null_descriptor_fallback','pass':actual==('flat_routine',255)})
    # Independent formulations of high-word signed extraction, including zero and
    # the entire int16 domain. Vary vertex2; its lower word must not affect f3.
    checked=0
    for raw in range(65536):
        for vertex in (0,65535):
            pair=struct.pack('<HH',vertex,raw)
            shifted=struct.unpack('<i',pair)[0]>>16
            direct=struct.unpack_from('<h',pair,2)[0]
            if shifted!=direct:raise ValueError('SIGNED_EXTRACTION_MISMATCH')
            checked+=1
    tests.append({'test':'full_int16_signed_extraction','pass':True,'comparisons':checked})
    tests.append({'test':'corpus_records_partition','pass':corpus['totals']['records']==7205 and corpus['totals']['negative']+corpus['totals']['nonnegative']==7205})
    tests.append({'test':'historical_modulo_counterexamples_reproduced','pass':corpus['totals']['modulo_disagrees']==1374 and corpus['totals']['positive_local_match']==1537})
    tests.append({'test':'HMO7_minus1024_is_151_not647','pass':next(p for p in corpus['parts'] if p['hmo']=='HMO_7')['negative_histogram'][-1024]==151})
    if sha(SOURCE.read_bytes())!=PIN:raise ValueError('EXE_CHANGED')
    report={'schema':'OpenMDK1.F3ConsumerVerification.v1','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL',
        'scope':'ISOLATED_ORIGINAL_INSTRUCTION_MECHANISM_AND_CORPUS_CROSSWALK',
        'original_game_runtime_launched':False,'native_game_code_executed_on_host':False,
        'emulator':{'name':'Unicorn','version':unicorn.__version__,'word_size':32,
            'boundaries':'Whitelisted resolver and dispatch blocks only; no host syscalls. Raster callbacks are observed, not executed.',
            'stub':'Only zero-primary registry memset external call is modeled, with exact target/length checks.'},
        'source_exe_sha256':PIN,'test_count':len(tests),'passed':sum(t['pass'] for t in tests),'tests':tests,
        'corpus':corpus,'conclusions':{
          'f3_signed16':'+0x06, read as arithmetic high word of dword at +0x04',
          'nonnegative_dispatch':'direct pointer-table index including zero; not selector modulo material count',
          'pointer_table_builder':'10-byte name entries resolve exact case-sensitive names against ordered 52-byte material descriptors; primary then secondary, fallback/null semantics retained',
          'negative_dispatch':'separate code-controlled branches; -1024..-1027 select LUT banks 0..3',
          'payload_pointer':'resolved descriptor +0x24 consumed by texture branch',
          'old_modulo_rule':'FALSIFIED_AS_GENERAL_MATERIAL_IDENTITY_RULE'},
        'remaining_gates':['Prove the precise active primary/shared registry providers for each LEVEL3 HMO.',
          'Resolve nonlocal payload cases and test live loader binding.',
          'Keep degenerate/inactive records separate from visible runtime instances.',
          'UV/sampler/flags and LUT blend/depth semantics remain separate.',
          'Production binding and original-runtime visual fidelity not tested.'],
        'source_or_game_worktree_writes':0,'production_promotion':False,
        'created_at_utc':datetime.now(timezone.utc).isoformat()}
    digest=save('f3-consumer-verification.json',report)
    print(json.dumps({'status':report['status'],'tests':len(tests),'passed':report['passed'],
        'unicorn_version':unicorn.__version__,'corpus_totals':corpus['totals'],
        'nonlocal_by_hmo':{p['hmo']:p['nonlocal_names'] for p in corpus['parts'] if p['nonlocal_names']},
        'zero_names':{p['hmo']:p['zero_names'] for p in corpus['parts'] if p['zero_names']},
        'dispatch_codes':len(codes),'report_sha256':digest,'game_runtime_launched':False},indent=2))
    if report['status']!='PASS':raise SystemExit(2)
if __name__=='__main__':main()
