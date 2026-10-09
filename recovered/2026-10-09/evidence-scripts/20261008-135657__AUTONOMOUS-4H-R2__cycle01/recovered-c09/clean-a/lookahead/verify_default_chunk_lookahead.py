"""Original default-perspective varying-q chunk lookahead state against exact arithmetic.
FP80 registers are observed without mutation. This proves interpolation state
continuity, not general pixel equality or live-profile/camera fidelity.
"""
from fractions import Fraction
from datetime import datetime,timezone
import json,struct,itertools
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.x86_const import *
from verify_perspective_span_inputs import make,r
from verify_perspective_inputs import f32
from verify_f3_contract import w32,STACK,STOP
from observe_default_chunk_fpu import number,REGS
from static_probe import ROOT,PIN,sha
TEX,DEST=0x20000000,0x10080000

def partition(x,n):
 aligned=x&31;head=min(n,32-aligned) if aligned else 0
 # Original uses a lone short tail when it cannot reach the first alignment boundary.
 if aligned and n<32-aligned:head=0
 full,tail=divmod(n-head,32)
 return head,full,tail

def run(n,x,values):
 if not 0<=n<=639 or not 0<=x<32:raise ValueError('DOMAIN')
 values=tuple(map(f32,values));q,uq,vq,dq,duq,dvq=values
 if min(q,q+dq*n)<=0:raise ValueError('NONPOSITIVE_Q')
 head,full,tail=partition(x,n);intervals=([head] if head else [])+[32]*full+([tail] if tail else [])
 at={0:tuple(map(Fraction.from_float,(q,uq,vq)))};position=0;state=at[0];grads=tuple(map(Fraction.from_float,(dq,duq,dvq)))
 for length in intervals:
  position+=length;state=tuple(r(a+r(g*length)) for a,g in zip(state,grads));at[position]=state
 u,_=make();u.mem_map(TEX,32768);u.mem_write(TEX,bytes(32768));u.mem_write(DEST-16,b'\xa5'*(n+65));u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 for p,v in [(0x54ec2c,n),(0x54ec70,x),(0x54ec28,7),(0x54ec50,128),(0x54ec20,TEX),(0x54ec1c,DEST)]:w32(u,p,v)
 for p,v in [(0x54ec30,q),(0x54ec34,uq),(0x54ec38,vq),(0x54ec10,dq),(0x54ec14,duq),(0x54ec18,dvq),(0x54ec80,f32(32*dq)),(0x54ec84,f32(32*duq)),(0x54ec88,f32(32*dvq))]:u.mem_write(p,struct.pack('<f',v))
 observations=[];done=[];writes=[]
 def code(uc,a,size,_):
  if a==STOP:done.append(True);uc.emu_stop();return
  if not 0x471f82<=a or a+size>0x47278a:raise ValueError('CODE_ESCAPE')
  if a in (0x47219a,0x47241d,0x4726a2):
   current=uc.reg_read(UC_X86_REG_EDI)-DEST;future=n if a==0x4726a2 else current+32
   if current not in at or future not in at:raise ValueError('OBSERVED_BOUNDARY_NOT_IN_PARTITION')
   cq,cuq,cvq=at[current];fq,fuq,fvq=at[future]
   expected=[r(1/fq),r(cvq*r(1/cq)),r(cuq*r(1/cq)),fvq,fuq,fq]
   top=(uc.reg_read(UC_X86_REG_FPSW)>>11)&7
   observed=[number(uc.reg_read(REGS[(top+i)&7])) for i in range(6)]
   if observed!=expected:
    fail={'status':'FAIL','delta':n,'x':x,'values':values,'pc':hex(a),'current':current,'future':future,'observed':[str(z) for z in observed],'expected':[str(z) for z in expected]}
    p=ROOT/'chunk-lookahead-counterexample.json'
    if not p.exists():p.write_text(json.dumps(fail,indent=2),encoding='utf-8')
    raise ValueError('CHUNK_LOOKAHEAD_NUMERIC_DIFFERENCE')
   observations.append({'pc':hex(a),'current_position':current,'lookahead_position':future,'logical_fp80_sha256':sha(json.dumps([str(v) for v in observed]).encode())})
 def read(uc,access,a,size,v,_):
  if TEX<=a<TEX+65536 and not a+size<=TEX+32768:raise ValueError('TEXEL_READ_BOUNDS')
 def write(uc,access,a,size,v,_):
  if STACK-128<=a and a+size<=STACK:return
  if DEST<=a and a+size<=DEST+n+1 and size==1:writes.append(a-DEST);return
  raise ValueError('CHUNK_WRITE_BOUNDS')
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x471f82,STOP+1,timeout=300000,count=30000)
 if not done or len(observations)!=full+1 or writes!=list(range(n+1)):raise ValueError('CHUNK_COVERAGE_OR_WRITE_ORDER')
 if bytes(u.mem_read(DEST-16,16))!=b'\xa5'*16 or bytes(u.mem_read(DEST+n+1,48))!=b'\xa5'*48:raise ValueError('GUARD_MUTATED')
 return {'delta':n,'screen_x_mod32':x,'inputs':values,'partition':[head,full,tail],'observations':observations,'pixel_write_count':len(writes),'pass':True}

def main():
 inputs=[(1.,8.,30.,1/256,1/16,1/32),(2.,30.,90.,-1/1024,1/32,-1/16),(1.1,9.3,40.1,.001,.031,.007)]
 cases=[run(n,x,v) for n,x,v in itertools.product((0,1,7,31,32,33,64,65,70,127,638,639),(0,1,5,31),inputs)]
 report={'schema':'OpenMDK1.DefaultChunkLookahead.v1','status':'PASS','tests':len(cases),'cases':cases,'source_exe_sha256':PIN,
  'rule':'At each original full-block/tail boundary, observed FP80 stack holds inverse future q, previous endpoint v/u, and future vq/uq/q. Future q/uq/vq advances by the source partition length with the original operation rounding.',
  'independent_oracle':'Exact Fraction arithmetic quantized to x87 PC64 at each source add/multiply/divide; no FPU state is modified by the observer.',
  'input_profile':'Binary32 endpoint and gradient fields; PC64 nearest-even; 12 deltas, 4 X residues, 3 varying-q states.',
  'scope':'Full original function executed with a guarded zero texture to isolate interpolation-state continuity; general nonzero texture/pixel equivalence is NOT inferred from this test.',
  'no_new_production_renderer':True,'game_runtime_executed':False,'fidelity_verified':False,
  'next':'Combine the verified chunk states with exact nonzero texel/read-state comparison, then require actual runtime profile/camera capture before scene fidelity.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'default-chunk-lookahead-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
