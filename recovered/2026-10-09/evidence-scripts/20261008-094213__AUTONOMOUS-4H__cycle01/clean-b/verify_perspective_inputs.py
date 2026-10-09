"""Guard -> reciprocal depth / perspective UV input mechanism, exact rational oracle.
Declared x87 precision/rounding and controlled positive-width branch. No rasterizer,
OS helpers, production game or live capture. Source data are never written.
"""
from fractions import Fraction
from datetime import datetime,timezone
import itertools,json,math,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK
from static_probe import ROOT,PIN,sha
V=(0x10020000,0x10020100,0x10020200);UV=(0x10030000,0x10030100,0x10030200);D=0x10010000

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def power(k):return Fraction(1<<k,1) if k>=0 else Fraction(1,1<<-k)
def quantize(q,bits,mode):
 if q==0:return q
 a=abs(q);e=a.numerator.bit_length()-a.denominator.bit_length()
 if a<power(e):e-=1
 unit=power(e-bits+1);n=q/unit
 integer=round(n) if mode==0 else math.floor(n) if mode==1 else math.ceil(n) if mode==2 else math.trunc(n)
 return integer*unit

def reference(zs,uvs,mode):
 floor_z=f32(max(zs)/64) if max(zs)>64*min(zs) else 0
 out=[]
 for z,(u,v) in zip(zs,uvs):
  effective=max(z,floor_z);q=quantize(quantize(1/Fraction.from_float(effective),64,mode),24,mode)
  uq=quantize(Fraction.from_float(u)*q,24,mode);vq=quantize(Fraction.from_float(v)*q,24,mode)
  out.append((q,uq,vq))
 return out

def run(zs,uvs,mode):
 zs=tuple(f32(x) for x in zs);uvs=tuple(tuple(f32(x) for x in uv) for uv in uvs)
 if any(not math.isfinite(z) or z<=0 for z in zs) or any(not math.isfinite(x) for uv in uvs for x in uv):raise ValueError('FIXTURE_DOMAIN')
 uc=machine();cw=0x37f|(mode<<10);uc.reg_write(UC_X86_REG_FPCW,cw)
 originals=[struct.pack('<6f',10+i,20+i,z,40+i,50+i,60+i) for i,z in enumerate(zs)]
 for p,b in zip(V,originals):uc.mem_write(p,b)
 for p,uv in zip(UV,uvs):uc.mem_write(p,struct.pack('<2f',*uv))
 uc.mem_write(D,struct.pack('<13I',7,128,128,0,127,127<<7,(~127)&0xffffffff,0,0,0x20000000,0,0,0))
 for p,v in [(STACK-124,D),(STACK-116,V[1]),(STACK-112,V[2]),(STACK+8,UV[0]),(STACK+12,UV[1]),(STACK+16,UV[2]),(0x541482,1),(0x54ebec,1),(0x54ebfc,1)]:w32(uc,p,v)
 uc.mem_write(0x540b58,struct.pack('<f',1.));uc.mem_write(0x540b64,struct.pack('<f',1.))
 uc.reg_write(UC_X86_REG_EBP,STACK);uc.reg_write(UC_X86_REG_EDX,V[0]);uc.reg_write(UC_X86_REG_EBX,UV[1])
 state={'done':False,'instructions':0};writes=[]
 def code(u,a,n,_):
  state['instructions']+=1
  if a==0x46de05:state['done']=True;u.emu_stop();return
  if not any(x<=a and a+n<=y for x,y in [(0x46dc19,0x46de05),(0x46e0ed,0x46e182)]):raise ValueError('CODE_ESCAPE:'+hex(a))
 def write(u,access,a,n,v,_):
  if STACK-192<=a and a+n<=STACK-108:return
  if 0x54dbb8<=a and a+n<=0x54dc00:return
  if 0x54ec20<=a and a+n<=0x54ec54:writes.append((a,n));return
  if a==0x54ebec and n==4:return
  raise ValueError('PERSPECTIVE_WRITE_ESCAPE:'+hex(a))
 uc.hook_add(UC_HOOK_CODE,code);uc.hook_add(UC_HOOK_MEM_WRITE,write)
 uc.emu_start(0x46dc19,0x100ff000,timeout=200000,count=800)
 if not state['done']:raise ValueError('PERSPECTIVE_INPUTS_NOT_COMPLETE')
 expected=reference(zs,uvs,mode)
 offsets=[(-0x84,-0x94,-0x8c),(-0x88,-0x9c,-0xa0),(-0x98,-0xa4,-0xa8)]
 observed=[]
 for triples,rels in zip(expected,offsets):
  for value,rel in zip(triples,rels):
   bits=bytes(uc.mem_read(STACK+rel,4));want=struct.pack('<f',float(value))
   if bits!=want:
    failure={'status':'FAIL','z':zs,'uv':uvs,'mode':mode,'stack_offset':rel,'original_hex':bits.hex(),'expected_hex':want.hex()}
    p=ROOT/'perspective-input-counterexample.json'
    if not p.exists():p.write_text(json.dumps(failure,indent=2),encoding='utf-8')
    raise ValueError('PERSPECTIVE_INPUT_NUMERIC_DIFFERENCE')
   observed.append(bits.hex())
 if any(bytes(uc.mem_read(p,24))!=raw for p,raw in zip(V,originals)):raise ValueError('SOURCE_VERTICES_CHANGED')
 if any(bytes(uc.mem_read(p,8))!=struct.pack('<2f',*uv) for p,uv in zip(UV,uvs)):raise ValueError('SOURCE_UV_CHANGED')
 if uc.reg_read(UC_X86_REG_FPCW)!=cw:raise ValueError('FPU_PROFILE_CHANGED')
 return {'depths':zs,'uv':uvs,'rounding':mode,'output_f32_hex':observed,'instructions':state['instructions'],'pass':True}

def main():
 cases=[]
 depths=[(1.,2.,128.),(0.5,32.,64.),(3.,7.,11.),(1.1,2.3,3.7),(100.,100.,100.),(1.,64.,64.)]
 uvs=[((0.,0.),(1.,1.),(128.,256.)),((-0.1,1/3),(3.5,-7.25),(1023.75,-512.125)),((123.456,-345.67),(-1.5,0.),(0.0001,33.333))]
 for z in depths:
  for perm in sorted(set(itertools.permutations(z))):
   for uv in uvs:
    for mode in range(4):cases.append(run(perm,uv,mode))
 result={'schema':'OpenMDK1.PerspectiveInputMechanism.v1','status':'PASS','tests':len(cases),'cases':cases,
  'source_exe_sha256':PIN,'rule':'Apply depth guard when required, then q_i=f32(1/z_i); uq_i=f32(u_i*q_i); vq_i=f32(v_i*q_i), retaining the original explicit stores and operation order.',
  'oracle':'Exact Fraction arithmetic with an explicit 64-bit significand reciprocal rounding followed by binary32 storage; four declared x87 rounding modes.',
  'numeric_profile':'x87 PC=64-bit significand, RC nearest-even/down/up/toward-zero. Finite positive depths, no subnormal/overflow fixtures.',
  'scope':'Perspective reciprocal/UV inputs only on the source positive-width branch, before span-gradient generation.',
  'output_order':'q0,uq0,vq0,q1,uq1,vq1,q2,uq2,vq2','new_native_game_jobs':0,'fidelity_verified':False,
  'remaining':'Signed triangle-width counterpart, gradient setup, perspective span approximation and live runtime/FPU profile.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 with (ROOT/'perspective-input-verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,sort_keys=True,indent=2)
 print(json.dumps({'status':'PASS','tests':len(cases),'delta':'guard-to-q/uq/vq inputs verified against exact rational rounding','sha256':sha((ROOT/'perspective-input-verification.json').read_bytes())}))
if __name__=='__main__':main()
