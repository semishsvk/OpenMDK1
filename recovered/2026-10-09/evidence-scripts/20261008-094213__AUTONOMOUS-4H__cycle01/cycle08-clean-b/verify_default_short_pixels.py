"""Actual B/default/flags0 perspective kernel on aligned short spans, exact pixels.
Unlike B/alternate, the endpoint is advanced from q/uq/vq gradients at the selected
interval width. The original function/table identity is separately pinned.
"""
from datetime import datetime,timezone
from fractions import Fraction
import itertools,json,struct,math
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.x86_const import *
from verify_perspective_span_inputs import make,r,floatbytes,magic,BU,BV,signed
from verify_perspective_inputs import f32
from verify_f3_contract import w32,STACK,STOP
from static_probe import ROOT,PIN,load,offset,sha
TEX,FRAME=0x20000000,0x10080000;MASK=0xffffffff

def model(n,shift,inputs,texture):
 q,uq,vq,dq,duq,dvq=map(Fraction.from_float,inputs)
 inv=r(1/q);u0=r(uq*inv);v0=r(vq*inv)
 q1=r(q+r(dq*n));uq1=r(uq+r(duq*n));vq1=r(vq+r(dvq*n));inv1=r(1/q1)
 u1=r(uq1*inv1);v1=r(vq1*inv1)
 recip=Fraction.from_float(struct.unpack('<f',floatbytes(r(Fraction(1,n or 1)),24))[0])
 du=magic(r(r(u1-u0)*recip),BU);dv=magic(r(r(v1-v0)*recip),BV);u=magic(u0,BU);v=magic(v0,BV)
 addr=((signed(v)>>12)<<shift)+(u>>16);uf=u<<16&MASK;vf=v<<20&MASK;ufstep=du<<16&MASK;vfstep=dv<<20&MASK
 step=(signed(du)>>16)+((signed(dv)>>12)<<shift);indices=[];pixels=[]
 for _ in range(max(1,n)):
  vv=vf+vfstep;vc=vv>MASK;vf=vv&MASK;uu=uf+ufstep;uc=uu>MASK;uf=uu&MASK
  if not 0<=addr<len(texture):raise ValueError('MODEL_SOURCE_BOUNDS')
  texel=texture[addr];indices.append(addr);pixels.append(texel);ufstep=(ufstep&0xffffff00)|texel
  addr=(addr+step+((1<<shift) if vc else 0)+int(uc))&MASK
 if n:pixels.append(pixels[-1])
 return indices,bytes(pixels)

def run(n,shift,values,pattern):
 if not 0<=n<=31 or shift not in (5,7,8):raise ValueError('DEFAULT_SHORT_DOMAIN')
 values=tuple(map(f32,values));q,uq,vq,dq,duq,dvq=values
 if q<=0 or q+dq*n<=0:raise ValueError('POSITIVE_Q_DOMAIN')
 texture=bytes((i*73+19)&255 if pattern==0 else (0 if i%7==0 else i&255) for i in range((1<<shift)*128))
 er,ep=model(n,shift,values,texture)
 u,_=make();u.mem_map(TEX,(len(texture)+4095)&~4095);u.mem_write(TEX,texture)
 before=b'\xa5'*(n+1+64);u.mem_write(FRAME-16,before);u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 for p,v in [(0x54ec2c,n),(0x54ec70,0),(0x54ec28,shift),(0x54ec50,1<<shift),(0x54ec20,TEX),(0x54ec1c,FRAME)]:w32(u,p,v)
 for p,v in [(0x54ec30,q),(0x54ec34,uq),(0x54ec38,vq),(0x54ec10,dq),(0x54ec14,duq),(0x54ec18,dvq),(0x54ec80,f32(dq*32)),(0x54ec84,f32(duq*32)),(0x54ec88,f32(dvq*32))]:u.mem_write(p,struct.pack('<f',v))
 state={'done':False,'instructions':0};reads=[];writes=[]
 def code(uc,a,size,_):
  state['instructions']+=1
  if a==STOP:state['done']=True;uc.emu_stop();return
  if not 0x471f82<=a or a+size>0x47278a:raise ValueError('DEFAULT_CODE_ESCAPE')
 def read(uc,access,a,size,v,_):
  if TEX<=a<TEX+len(texture)+4096:
   if size!=1 or a>=TEX+len(texture):raise ValueError('SOURCE_READ_ESCAPE')
   reads.append(a-TEX)
 def write(uc,access,a,size,v,_):
  if STACK-128<=a and a+size<=STACK:return
  if FRAME<=a and a+size<=FRAME+n+1:
   if size!=1:raise ValueError('PIXEL_WRITE_SIZE')
   writes.append((a-FRAME,v&255));return
  raise ValueError('DEFAULT_WRITE_ESCAPE:'+hex(a))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x471f82,STOP+1,timeout=200000,count=3000)
 after=bytes(u.mem_read(FRAME-16,len(before)));expect=before[:16]+ep+before[16+n+1:]
 if not state['done'] or reads!=er or writes!=list(enumerate(ep)) or after!=expect:
  failure={'status':'FAIL','n':n,'shift':shift,'inputs':values,'expected_reads':er,'actual_reads':reads,'expected_pixels':list(ep),'actual_writes':writes}
  path=ROOT/'default-short-counterexample.json'
  if not path.exists():path.write_text(json.dumps(failure,indent=2),encoding='utf-8')
  raise ValueError('DEFAULT_PERSPECTIVE_PIXEL_MISMATCH')
 if bytes(u.mem_read(TEX,len(texture)))!=texture:raise ValueError('SOURCE_TEXTURE_MUTATED')
 return {'span_delta':n,'shift':shift,'q_uq_vq_and_gradients':values,'pattern':pattern,'read_count':len(reads),'pixel_count':len(ep),'pixel_sha256':sha(ep),'read_order_sha256':sha(struct.pack('<'+'I'*len(er),*er)),'instructions':state['instructions'],'pass':True}

def main():
 b,s=load();assert struct.unpack_from('<I',b,offset(s,0x49bce4,4))[0]==0x471f82
 inputs=[(1.,8.,30.,0.,1.,.5),(1.,8.,30.,.015625,.25,.25),(2.,80.,100.,-.015625,-.5,-.125),(.3,1.125,9.,.002,-.05,.01)]
 cases=[run(n,shift,v,p) for n,shift,v,p in itertools.product((0,1,2,3,7,15,30,31),(5,7,8),inputs,(0,1))]
 report={'schema':'OpenMDK1.DefaultShortPerspectivePixels.v1','status':'PASS','tests':len(cases),'cases':cases,'source_exe_sha256':PIN,
  'canonical_function':'VARIANT_B_DEFAULT_PERSPECTIVE_FLAGS0, table B slot0 @0x471f82','tested_x_alignment':0,
  'rule':'The default kernel advances q/uq/vq by gradients times the interval length before reciprocal conversion. It then linearly steps fixed coordinates within this interval; this differs from the alternate path denominator span_delta+2.',
  'validation':'Exact original source texel read sequence, byte writes, guards and source immutability vs explicit PC64 rational model.',
  'scope':'Aligned short interval delta0..31 only; no claim for nonaligned heads or chained32-pixel intervals.',
  'game_runtime_executed':False,'fidelity_verified':False,'next':'Bound the nonaligned/default chunk transitions or profile-A differences; do not claim default/alternate interchangeability.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'default-short-pixel-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
