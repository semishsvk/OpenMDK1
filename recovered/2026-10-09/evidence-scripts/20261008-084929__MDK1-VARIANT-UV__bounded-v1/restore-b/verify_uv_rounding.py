"""Bounded original UV fixed-point and screen FISTP conversion tests.
The x87 control word is a declared input, not an assumed live-game state. No
runtime/OS calls or rendering occur. Exact rational arithmetic is the oracle.
"""
from datetime import datetime,timezone
from fractions import Fraction
import math,json,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from static_probe import ROOT,load,offset,PIN,sha
from verify_f3_contract import machine,w32,r32,STACK
VALUE=0x10010000
CWS={0:'nearest_even',1:'down',2:'up',3:'toward_zero'}
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def rounded(x,mode):
    if mode==0:return round(x)
    if mode==1:return math.floor(x)
    if mode==2:return math.ceil(x)
    return math.trunc(x)

def micro(value,mode,kind):
    x=f32(value)
    if not math.isfinite(x) or not -32768<=x<32768:raise ValueError('SUPPORTED_CONVERSION_DOMAIN')
    uc=machine();cw=0x037f|(mode<<10);uc.reg_write(UC_X86_REG_FPCW,cw)
    if uc.reg_read(UC_X86_REG_FPCW)!=cw:raise ValueError('FPU_PROFILE_NOT_APPLIED')
    if kind=='uv16_16':
        uc.mem_write(VALUE,struct.pack('<f',x));uc.reg_write(UC_X86_REG_ECX,VALUE);uc.reg_write(UC_X86_REG_EBP,STACK)
        start,end=0x46e597,0x46e5be
    elif kind=='screen_integer':
        uc.mem_write(0x4a1e30,struct.pack('<f',x));start,end=0x46dad6,0x46dae7
    else:raise ValueError('UNKNOWN_CONVERTER')
    state={'done':False,'instructions':0}
    def code(u,addr,size,_):
        state['instructions']+=1
        if addr==end:state['done']=True;u.emu_stop();return
        if not (start<=addr and addr+size<=end):raise ValueError('CONVERSION_CODE_ESCAPE')
    def write(u,access,addr,size,value,_):
        allowed=[(0x4a1e30,0x4a1e38)]
        if kind=='uv16_16':allowed += [(STACK-12,STACK-8),(STACK-44,STACK-40)]
        if not any(a<=addr and addr+size<=b for a,b in allowed):raise ValueError('CONVERSION_WRITE_ESCAPE')
    uc.hook_add(UC_HOOK_CODE,code);uc.hook_add(UC_HOOK_MEM_WRITE,write)
    uc.emu_start(start,end+1,timeout=150000,count=100)
    if not state['done']:raise ValueError('CONVERSION_NOT_FINISHED')
    raw=uc.reg_read(UC_X86_REG_EAX);result=raw if raw<2**31 else raw-2**32
    if kind=='uv16_16':
        # Storing positive (1.5*2^36 + value) as float64 rounds at 2^-16.
        # Towards-zero of the positive biased value acts like floor for signed UV.
        q=Fraction.from_float(x)*65536
        expected=rounded(q,1 if mode==3 else mode)
    else:expected=rounded(Fraction.from_float(x),mode)
    if result!=expected:
        report={'status':'FAIL','input_f32':x,'mode':CWS[mode],'kind':kind,'original':result,'expected':expected,'cw':cw}
        p=ROOT/'uv-rounding-counterexample.json'
        if not p.exists():p.write_text(json.dumps(report,indent=2),encoding='utf-8')
        raise ValueError('CONVERSION_MODEL_DIFFERENCE:'+str(report))
    if uc.reg_read(UC_X86_REG_FPCW)!=cw:raise ValueError('CONVERSION_CHANGED_FPU_MODE')
    return {'input_f32':x,'mode':CWS[mode],'kind':kind,'original':result,'expected':expected,'pass':True}

def main():
    exe,secs=load();bias=struct.unpack_from('<f',exe,offset(secs,0x499aac,4))[0]
    if bias!=1.5*2**36:raise ValueError('BIAS_CONSTANT_CHANGED')
    values=set([0.,-0.,0.5,-0.5,1.5,-1.5,32767.,-32768.,32767.5,-32767.5])
    for n in [-65537,-1025,-17,-3,-2,-1,0,1,2,3,17,1025,65537]:
        for fraction in [0.,.25,.5,.75]:values.add((n+fraction)/65536)
    for integer in [-2048,-128,-1,0,1,128,2048]:
        for fraction in [0.,.25,.5,.75]:values.add(integer+fraction)
    checks=[]
    for kind in ['uv16_16','screen_integer']:
        for mode in range(4):
            for value in sorted(values):checks.append(micro(value,mode,kind))
    for value in [float('nan'),float('inf'),-float('inf'),32768.,-32769.]:
        try:micro(value,0,'uv16_16')
        except ValueError as exc:
            if str(exc)!='SUPPORTED_CONVERSION_DOMAIN':raise
            checks.append({'kind':'reject_unsupported_domain','value':str(value),'pass':True})
        else:raise ValueError('UNSAFE_DOMAIN_ACCEPTED')
    report={'schema':'OpenMDK1.UVNumericConversion.v1','status':'PASS','tests':len(checks),'checks':checks,
       'source_exe_sha256':PIN,'uv_converter':'0x46e597..0x46e5be','screen_converter':'0x46dad6..0x46dae7',
       'bias_float32':bias,'uv_format':'signed 16.16 returned from low 32 bits of stored biased float64',
       'x87_profiles':{'precision':'64-bit significand input profile (PC=11)','rounding_modes':CWS,'control_words':[0x37f|(m<<10) for m in range(4)]},
       'important_distinction':'For the biased UV operation, round-toward-zero of the large positive intermediate is floor in UV space, including negative UV. Screen FISTP has ordinary signed toward-zero behavior.',
       'actual_live_game_fpu_profile':'NOT_OBSERVED','safe_fixture_input_domain':'finite binary32 values in [-32768,32768), with declared representable test values',
       'limits':['This compares original conversion instructions, not all UV source-to-world transformations.',
          'Different precision-control settings and near double-rounding sub-ULP cases are not covered.',
          'No blanket safe UV range is inferred for individual non-power-of-two texture payloads.'],
       'native_game_executed':False,'production_renderer_modified':False,'fidelity_verified':False,
       'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'uv-rounding-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
