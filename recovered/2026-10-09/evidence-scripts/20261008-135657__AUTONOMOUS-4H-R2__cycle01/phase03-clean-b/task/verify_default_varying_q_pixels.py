"""Original B/default/flags0 varying-q scanlines across aligned/nonaligned chunks.
Independent PC64 rational endpoint model plus explicit integer carry state.
Compares nonzero texel read order, byte writes and guards; no live game/GPU.
"""
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone
import itertools,json,struct,math
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_perspective_span_inputs import make,r,magic,BU,BV,signed
from verify_perspective_inputs import f32
from verify_f3_contract import machine,w32,STACK,STOP
from verify_default_chunk_lookahead import partition
from static_probe import ROOT,PIN,load,offset,sha
TEX,DEST=0x20000000,0x10080000;MASK=0xffffffff
TABLE=None

def initialized_machine():
 global TABLE
 if TABLE is None:
  first,digest=make();TABLE=bytes(first.mem_read(0x54dc30,2560));assert sha(TABLE)==digest
 u=machine();u.reg_write(UC_X86_REG_FPCW,0x37f);u.mem_write(0x54dc30,TABLE)
 return u

def endpoint(q,uq,vq):
 inv=r(1/q);return r(uq*inv),r(vq*inv)

def model(n,x,shift,values,texture):
 q,uq,vq,dq,duq,dvq=map(Fraction.from_float,values)
 head,full,tail=partition(x,n);intervals=([head] if head else [])+[32]*full+([tail] if tail else [])
 uu,vv=endpoint(q,uq,vq);mu,mv=magic(uu,BU),magic(vv,BV)
 addr=((signed(mv)>>12)<<shift)+(mu>>16);uf=mu<<16&MASK;vf=mv<<20&MASK
 reads=[];pixels=[];boundary_states=[]
 if n==0:
  if not 0<=addr<len(texture):raise ValueError('MODEL_ADDRESS_BOUNDS')
  return [addr],bytes([texture[addr]]),[]
 for length in intervals:
  qn,un,vn=[r(a+r(g*length)) for a,g in zip((q,uq,vq),(dq,duq,dvq))]
  right_u,right_v=endpoint(qn,un,vn)
  recip=Fraction.from_float(struct.unpack_from('<f',TABLE,4*length)[0])
  du=magic(r(r(right_u-uu)*recip),BU);dv=magic(r(r(right_v-vv)*recip),BV)
  us=du<<16&MASK;vs=dv<<20&MASK;step=(signed(du)>>16)+((signed(dv)>>12)<<shift)
  start=len(reads)
  for _ in range(length):
   vvsum=vf+vs;vc=int(vvsum>MASK);vf=vvsum&MASK
   uusum=uf+us;uc=int(uusum>MASK);uf=uusum&MASK
   if not 0<=addr<len(texture):raise ValueError('MODEL_ADDRESS_BOUNDS')
   texel=texture[addr];reads.append(addr);pixels.append(texel)
   us=(us&0xffffff00)|texel
   addr=(addr+step+(vc<<shift)+uc)&MASK
  boundary_states.append({'start':start,'end':len(reads),'du_raw':du,'dv_raw':dv,'address_after':addr,'u_fraction_after':uf,'v_fraction_after':vf})
  q,uq,vq=qn,un,vn;uu,vv=right_u,right_v
 if len(reads)!=n:raise ValueError('MODEL_PARTITION_COUNT')
 pixels.append(pixels[-1]);return reads,bytes(pixels),boundary_states

def run(n,x,shift,rawvalues):
 values=tuple(map(f32,rawvalues));q,uq,vq,dq,duq,dvq=values
 if not 0<=n<=639 or not 0<=x<32 or shift not in (5,7) or min(q,q+dq*n)<=0:raise ValueError('FIXTURE_DOMAIN')
 texture=bytes((i*73+(i>>7)*13+17)&255 for i in range((1<<shift)*256))
 u=initialized_machine();expected_reads,expected_pixels,expected_boundaries=model(n,x,shift,values,texture)
 u.mem_map(TEX,(len(texture)+4095)&~4095);u.mem_write(TEX,texture)
 before=b'\xa5'*(n+1+80);u.mem_write(DEST-16,before);u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 for p,v in [(0x54ec2c,n),(0x54ec70,x),(0x54ec28,shift),(0x54ec50,1<<shift),(0x54ec20,TEX),(0x54ec1c,DEST)]:w32(u,p,v)
 for p,v in zip((0x54ec30,0x54ec34,0x54ec38,0x54ec10,0x54ec14,0x54ec18),values):u.mem_write(p,struct.pack('<f',v))
 for p,g in zip((0x54ec80,0x54ec84,0x54ec88),(dq,duq,dvq)):u.mem_write(p,struct.pack('<f',f32(g*32)))
 reads=[];writes=[];state={'returned':False,'instructions':0}
 def code(uc,a,size,_):
  state['instructions']+=1
  if a==STOP:state['returned']=True;uc.emu_stop();return
  if not 0x471f82<=a or a+size>0x47278a:raise ValueError('ORIGINAL_CODE_ESCAPE')
 def read(uc,access,a,size,v,_):
  if TEX<=a<TEX+len(texture)+4096:
   if size!=1 or a>=TEX+len(texture):raise ValueError('TEXEL_BOUNDS')
   reads.append(a-TEX)
 def write(uc,access,a,size,v,_):
  if STACK-128<=a and a+size<=STACK:return
  if DEST<=a and a+size<=DEST+n+1 and size==1:writes.append((a-DEST,v&255));return
  raise ValueError('WRITE_ESCAPE:'+hex(a))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x471f82,STOP+1,timeout=400000,count=40000)
 after=bytes(u.mem_read(DEST-16,len(before)));expected=before[:16]+expected_pixels+before[16+n+1:]
 ok=state['returned'] and reads==expected_reads and writes==list(enumerate(expected_pixels)) and after==expected
 if not ok:
  failure={'status':'FAIL','n':n,'x':x,'shift':shift,'values':values,'expected_reads':expected_reads,'actual_reads':reads,'expected_pixels':list(expected_pixels),'actual_writes':writes,'model_boundaries':expected_boundaries}
  p=ROOT/'default-varying-q-counterexample.json'
  if not p.exists():p.write_text(json.dumps(failure,indent=2),encoding='utf-8')
  raise ValueError('VARYING_Q_PIXEL_OR_TRACE_MISMATCH')
 if bytes(u.mem_read(TEX,len(texture)))!=texture or u.reg_read(UC_X86_REG_FPCW)!=0x37f:raise ValueError('SOURCE_OR_FPU_PROFILE_CHANGED')
 return {'span_delta':n,'screen_x_mod32':x,'width_shift':shift,'inputs':values,'partition':partition(x,n),
  'read_count':len(reads),'pixel_count':len(writes),'pixel_sha256':sha(expected_pixels),'texel_read_sha256':sha(struct.pack('<'+'I'*len(reads),*reads)),
  'boundary_state_sha256':sha(json.dumps(expected_boundaries,sort_keys=True).encode()),'instructions':state['instructions'],'pass':True}

def main():
 b,s=load();assert struct.unpack_from('<I',b,offset(s,0x49bce4,4))[0]==0x471f82
 inputs=[(1.,8.,30.,1/256,1/16,1/32),(2.,40.,120.,-1/2048,1/32,-1/16),
  (1.1,9.3,40.1,.001,.031,.007),(1.2,120.,80.,.0002,-.011,.009)]
 cases=[run(n,x,shift,v) for n,x,shift,v in itertools.product((0,1,2,7,31,32,33,64,65,70,127,639),(0,1,5,31),(5,7),inputs)]
 report={'schema':'OpenMDK1.DefaultVaryingQPixels.v1','status':'PASS','tests':len(cases),'cases':cases,'source_exe_sha256':PIN,
  'function_identity':'VARIANT_B_DEFAULT_PERSPECTIVE_FLAGS0 @0x471f82, source table B slot0',
  'rule':'Perspective-correct endpoint values are recomputed per source head/full32/tail interval; interval slopes are magic-bias quantized; integer address and fractional carry state persist across intervals, including the original DL texel perturbation.',
  'validation':'Exact nonzero source texel-read sequence, every destination byte/write order, guards, source immutability and fixed FPU control word.',
  'oracle':'Independent rational PC64 endpoint arithmetic and integer carry-state model; no replayed original instruction interpreter in the expected path.',
  'cached_baseline_initializer':'Original 640-entry reciprocal initializer checked once per test invocation, then immutable bytes reused; not counted as new tests.',
  'scope':'Finite guarded positive-q synthetic scanlines, width shifts5/7, source default B flags0. No claim for profile A, transparency/wrapping variants or triangle coverage.',
  'new_game_jobs':0,'runtime_fidelity_verified':False,'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'default-varying-q-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
