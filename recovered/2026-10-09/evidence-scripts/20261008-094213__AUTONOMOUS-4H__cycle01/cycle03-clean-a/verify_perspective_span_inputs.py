"""Original A0 perspective-span reciprocal and fixed-point setup, before texel reads.
Verifies the original 640-entry reciprocal table, x87 magic-bias conversion,
initial pointer and fractional/integer step registers against exact rational arithmetic.
"""
from fractions import Fraction
from datetime import datetime,timezone
import itertools,json,struct,math
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK
from verify_perspective_inputs import quantize,f32
from static_probe import ROOT,PIN,load,offset,sha
B,SECS=load();BU,BV=struct.unpack_from('<2f',B,offset(SECS,0x49bd20,8));TEX=0x20000000;FRAME=0x10080000
MASK=0xffffffff

def r(x):return quantize(x,64,0)
def floatbytes(x,n):return struct.pack('<f' if n==24 else '<d',float(quantize(x,n,0)))
def magic(value,bias):return struct.unpack('<I',floatbytes(r(value+Fraction.from_float(bias)),53)[:4])[0]
def signed(x):return x if x<0x80000000 else x-0x100000000

def make():
 u=machine();u.reg_write(UC_X86_REG_FPCW,0x37f);u.reg_write(UC_X86_REG_ESP,STACK);u.mem_write(0x54dc30,b'\xa5'*(640*4));state={'done':False};writes=[]
 def code(uc,a,n,_):
  if a==0x46da08:state['done']=True;uc.emu_stop();return
  if not 0x46d9d0<=a or a+n>0x46da08:raise ValueError('RECIPROCAL_INIT_CODE_ESCAPE')
 def write(uc,access,a,n,v,_):
  if STACK-32<=a and a+n<=STACK:return
  if n==4 and 0x54dc30<=a<0x54e630:writes.append(a);return
  raise ValueError('RECIPROCAL_INIT_WRITE_ESCAPE')
 hc=u.hook_add(UC_HOOK_CODE,code);hw=u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x46d9d0,0x100ff000,timeout=200000,count=10000);u.hook_del(hc);u.hook_del(hw)
 expected=b''.join(floatbytes(r(Fraction(1,i if i else 1)),24) for i in range(640))
 if not state['done'] or bytes(u.mem_read(0x54dc30,2560))!=expected or writes!=list(range(0x54dc30,0x54e630,4)):raise ValueError('RECIPROCAL_TABLE_OR_WRITE_ORDER')
 return u,sha(expected)

def run(span_delta,shift,ql,qr,ul,vl,ur,vr):
 if not 0<=span_delta<=637 or shift not in (3,7,8):raise ValueError('SPAN_DOMAIN')
 vals=tuple(map(f32,(ql,qr,ul,vl,ur,vr)));ql,qr,ul,vl,ur,vr=vals
 if min(ql,qr)<=0 or any(not math.isfinite(v) for v in vals):raise ValueError('PERSPECTIVE_NUMERIC_DOMAIN')
 u,tablesha=make();u.reg_write(UC_X86_REG_ESP,STACK);u.reg_write(UC_X86_REG_EBP,0)
 for p,v in [(0x54ec2c,span_delta),(0x54ec28,shift),(0x54ec50,1<<shift),(0x54ec20,TEX),(0x54ec1c,FRAME)]:w32(u,p,v)
 for p,v in [(0x54ec30,ql),(0x54ec3c,qr),(0x54ec34,ul),(0x54ec38,vl),(0x54ec40,ur),(0x54ec44,vr)]:u.mem_write(p,struct.pack('<f',v))
 u.mem_write(FRAME,b'\xa5'*32);state={'done':False,'instructions':0}
 def code(uc,a,n,_):
  state['instructions']+=1
  if a==0x470ff7:state['done']=True;uc.emu_stop();return
  if not 0x470f08<=a or a+n>0x470ff7:raise ValueError('SPAN_SETUP_CODE_ESCAPE')
 def write(uc,access,a,n,v,_):
  if STACK-128<=a and a+n<=STACK:return
  if a==0x54ec2c and n==4:return
  raise ValueError('SPAN_SETUP_WRITE_ESCAPE:'+hex(a))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x470f08,0x100ff000,timeout=200000,count=300)
 if not state['done']:raise ValueError('SPAN_SETUP_INCOMPLETE')
 invl=r(1/Fraction.from_float(ql));invr=r(1/Fraction.from_float(qr))
 u0=r(Fraction.from_float(ul)*invl);v0=r(Fraction.from_float(vl)*invl);u1=r(Fraction.from_float(ur)*invr);v1=r(Fraction.from_float(vr)*invr)
 recip=Fraction.from_float(struct.unpack('<f',floatbytes(r(Fraction(1,span_delta+2)),24))[0])
 du=r(r(u1-u0)*recip);dv=r(r(v1-v0)*recip)
 a,b,c,d=magic(u0,BU),magic(v0,BV),magic(du,BU),magic(dv,BV)
 expected={'initial_pointer':(TEX+((signed(b)>>12)<<shift)+(a>>16))&MASK,'u_fraction':(a<<16)&MASK,'v_fraction':(b<<20)&MASK,
  'du_fraction':(c<<16)&MASK,'dv_fraction':(d<<20)&MASK,'integer_step':((signed(c)>>16)+((signed(d)>>12)<<shift))&MASK}
 S=STACK-7*4-0x38
 actual={'initial_pointer':u.reg_read(UC_X86_REG_ESI),'u_fraction':u.reg_read(UC_X86_REG_EBX),'v_fraction':u.reg_read(UC_X86_REG_EBP),
  'du_fraction':u.reg_read(UC_X86_REG_EDX),'dv_fraction':u.reg_read(UC_X86_REG_EAX),'integer_step':r32(u,S+48)}
 if actual!=expected or r32(u,S+44)!=(expected['integer_step']+(1<<shift))&MASK:raise ValueError('SPAN_FIXED_POINT_STATE_MISMATCH:'+json.dumps({'actual':actual,'expected':expected}))
 if r32(u,0x54ec2c)!=span_delta+2 or u.reg_read(UC_X86_REG_ESP)!=S or bytes(u.mem_read(FRAME,32))!=b'\xa5'*32:raise ValueError('SPAN_SETUP_FRAME_OR_STACK_DRIFT')
 return {'span_delta':span_delta,'width_shift':shift,'q_uv_inputs':vals,'state':actual,'integer_step_vcarry':r32(u,S+44),'reciprocal_table_sha256':tablesha,'instructions':state['instructions'],'pass':True}

def main():
 cases=[]
 endpoints=[(1.,1.,7.75,3.5,19.25,8.125),(2.,4.,5.,16.,96.,32.),(.3,2.1,1.125,3.33,6.75,8.125),(7.,11.,700.,140.,900.,200.)]
 for n,shift,values in itertools.product((0,1,2,7,30,31,32,127,637),(3,7,8),endpoints):cases.append(run(n,shift,*values))
 _,tablehash=make()
 result={'schema':'OpenMDK1.PerspectiveSpanInputMechanism.v1','status':'PASS','tests':len(cases)+1,'cases':cases,'source_exe_sha256':PIN,
  'reciprocal_table':{'entries':640,'index0':1,'rule':'index i>0 stores binary32(1/i) from original x87 sequence','sha256':tablehash},
  'bias_constants':{'u':BU,'v':BV},'kernel_scope':'A0 0x470f08 to 0x470ff7, before the first source texel read.',
  'rule':'Divide uq/vq by q at both endpoints; multiply their difference by the source reciprocal table indexed by span_delta+2; magic-bias conversion produces U16.16/V20.12; preserve integer address/carry steps.',
  'independent_oracle':'Exact Fraction arithmetic with PC64-nearest-even operation rounding, binary32 reciprocal storage and binary64 magic-bias stores.',
  'pixel_reads_or_writes_executed':False,'source_texture_address_dereferenced':False,'native_game_executed':False,'fidelity_verified':False,
  'remaining':['Actual per-pixel stepping/chunk approximation and the other perspective kernels.',
    'Variant B driver/callback ABI requires separate source-backed execution evidence; copying its function table is not sufficient.'],
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'perspective-span-input-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
