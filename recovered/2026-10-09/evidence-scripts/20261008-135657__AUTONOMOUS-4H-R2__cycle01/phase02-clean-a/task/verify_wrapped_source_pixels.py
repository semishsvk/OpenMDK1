"""B/default/flags2 perspective on the actual four wrapped LEVEL3 payloads.
Independent rational interval/carry model, exact original reads/pixels/writes.
No source texture bytes are emitted as artifacts, no runtime renderer is installed.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
from datetime import datetime,timezone
import struct,json,itertools
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_default_varying_q_pixels import initialized_machine,partition
from verify_perspective_span_inputs import r,magic,BU,BV,signed
from verify_perspective_inputs import f32
from verify_f3_contract import w32,STACK,STOP
from static_probe import ROOT,PIN,load,offset,sha
TEX,DEST=0x20000000,0x10080000;MASK=0xffffffff
IR=ROOT.parent/'20261008-074645__MDK1-ALIAS-ACTIVE__bounded-v1'/'material-binding-sourceir.json'
IRPIN='b597a9f27d5e03b34117d02d893a6e8b456406c8d413a2dd73276e96db32e783'
SOURCE=Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO')
SOURCEPIN='6f33536701f57a404f8b25aa5580502cd68389de9ae591b53b018f415f7193ff'

def expected(n,x,shift,height,values,payload):
 q,uq,vq,dq,duq,dvq=map(Fraction.from_float,values)
 def uv(a,b,c):inv=r(1/a);return r(b*inv),r(c*inv)
 leftu,leftv=uv(q,uq,vq);mu,mv=magic(leftu,BU),magic(leftv,BV)
 addr=(((signed(mv)>>12)<<shift)+(mu>>16))&MASK
 uf=mu<<16&MASK;vf=mv<<20&MASK;combined=((1<<shift)-1)|((height-1)<<shift)
 reads=[];pixels=[];mask_changes=0
 head,full,tail=partition(x,n)
 for length in ([head] if head else [])+[32]*full+([tail] if tail else []):
  qn,un,vn=[r(a+r(g*length)) for a,g in zip((q,uq,vq),(dq,duq,dvq))]
  rightu,rightv=uv(qn,un,vn)
  recip=Fraction.from_float(f32(float(r(Fraction(1,length)))))
  du=magic(r(r(rightu-leftu)*recip),BU);dv=magic(r(r(rightv-leftv)*recip),BV)
  us=du<<16&MASK;vs=dv<<20&MASK;step=(signed(du)>>16)+((signed(dv)>>12)<<shift)
  for _ in range(length):
   a=vf+vs;vc=int(a>MASK);vf=a&MASK
   a=uf+us;uc=int(a>MASK);uf=a&MASK
   masked=addr&combined;mask_changes+=int(masked!=addr);addr=masked
   if addr>=len(payload):raise ValueError('MASK_ESCAPED_SOURCE_PAYLOAD')
   value=payload[addr];reads.append(addr);pixels.append(value)
   us=(us&0xffffff00)|value;addr=(addr+step+(vc<<shift)+uc)&MASK
  q,uq,vq=qn,un,vn;leftu,leftv=rightu,rightv
 if n:pixels.append(pixels[-1])
 else:
  addr&=combined;reads.append(addr);pixels.append(payload[addr])
 return reads,bytes(pixels),mask_changes

def run(n,x,material,values,payload):
 shift=(material['width']-1).bit_length();height=material['height'];values=tuple(map(f32,values))
 if not 0<=n<=639 or not 0<=x<32 or min(values[0],values[0]+values[3]*n)<=0:raise ValueError('DOMAIN')
 if material['width']&(material['width']-1) or height&(height-1):raise ValueError('POWER_TWO_SOURCE_PROFILE_REQUIRED')
 er,ep,changes=expected(n,x,shift,height,values,payload)
 u=initialized_machine();u.mem_map(TEX,(len(payload)+4095)&~4095);u.mem_write(TEX,payload)
 guard=b'\xa5'*16;before=guard+b'\x5a'*(n+1)+b'\xa5'*64;u.mem_write(DEST-16,before)
 u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 for p,v in [(0x54ec2c,n),(0x54ec70,x),(0x54ec28,shift),(0x54ec50,1<<shift),(0x54ec20,TEX),(0x54ec1c,DEST),
             (0x54ec24,(1<<shift)-1),(0x54ec48,(height-1)<<shift)]:w32(u,p,v)
 for p,v in zip((0x54ec30,0x54ec34,0x54ec38,0x54ec10,0x54ec14,0x54ec18),values):u.mem_write(p,struct.pack('<f',v))
 for p,g in zip((0x54ec80,0x54ec84,0x54ec88),values[3:]):u.mem_write(p,struct.pack('<f',f32(g*32)))
 reads=[];writes=[];done=[]
 def code(uc,a,size,_):
  if a==STOP:done.append(True);uc.emu_stop();return
  if not 0x4730f0<=a or a+size>0x473b0a:raise ValueError('WRAPPED_CODE_ESCAPE')
 def read(uc,access,a,size,value,_):
  if TEX<=a<TEX+len(payload)+4096:
   if size!=1 or a>=TEX+len(payload):raise ValueError('TEXEL_READ_BOUNDS')
   reads.append(a-TEX)
 def write(uc,access,a,size,value,_):
  if STACK-128<=a and a+size<=STACK:return
  if DEST<=a and a+size<=DEST+n+1 and size==1:writes.append((a-DEST,value&255));return
  raise ValueError('WRAPPED_WRITE_ESCAPE')
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x4730f0,STOP+1,timeout=400000,count=40000)
 actual=bytes(u.mem_read(DEST-16,len(before)));expect=guard+ep+b'\xa5'*64
 if not done or reads!=er or writes!=list(enumerate(ep)) or actual!=expect:
  failure={'status':'FAIL','n':n,'x':x,'material':material['name'],'values':values,'expected_reads':er,'reads':reads,'expected_pixels':list(ep),'writes':writes}
  p=ROOT/'wrapped-source-counterexample.json'
  if not p.exists():p.write_text(json.dumps(failure,indent=2),encoding='utf-8')
  raise ValueError('WRAPPED_SOURCE_PIXEL_DIFFERENCE')
 if bytes(u.mem_read(TEX,len(payload)))!=payload:raise ValueError('SOURCE_PAYLOAD_MUTATION')
 return {'material':material['name'],'provider':material['provider'],'ordinal':material['ordinal'],'span_delta':n,'screen_x_mod32':x,'inputs':values,
  'source_payload_sha256':material['first_plane_sha256'],'read_order_sha256':sha(struct.pack('<'+'I'*len(reads),*reads)),
  'pixel_sha256':sha(ep),'samples_remapped_by_linear_mask':changes,'pass':True}

def main():
 raw=IR.read_bytes();assert sha(raw)==IRPIN;ir=json.loads(raw);source=SOURCE.read_bytes();assert sha(source)==SOURCEPIN
 counts=Counter((x['material_provider'],x['material_ordinal']) for x in ir['records'] if x['kind']=='TEXTURE_REFERENCE')
 materials=[m for ms in ir['materials'].values() for m in ms if (m['provider'],m['ordinal']) in counts and m.get('runtime_flags')==2]
 assert len(materials)==4 and sum(counts[(m['provider'],m['ordinal'])] for m in materials)==120
 exe,sections=load();assert struct.unpack_from('<I',exe,offset(sections,0x49bce4+8,4))[0]==0x4730f0
 cases=[];profiles=[]
 for m in materials:
  start=m['raw_payload_offset'];size=m['width']*m['height'];payload=source[start:start+size]
  assert len(payload)==size and sha(payload)==m['first_plane_sha256']
  w,h=m['width'],m['height']
  inputs=[(1.,w-0.25,h-0.5,.002,1.75,.25),(1.,-2.5,-1.25,1/1024,-.5,.125),
   (2.,w*2+3.,h*2-1.,-1/2048,-.25,-.5),(1.1,9.3,40.1,.001,.031,.007)]
  for n,x,values in itertools.product((0,1,2,31,32,33,64,65,127,639),(0,1,5,31),inputs):cases.append(run(n,x,m,values,payload))
  profiles.append({'name':m['name'],'provider':m['provider'],'ordinal':m['ordinal'],'dimensions':[w,h],'references':counts[(m['provider'],m['ordinal'])],'payload_sha256':sha(payload)})
 mask_cases=sum(c['samples_remapped_by_linear_mask']>0 for c in cases)
 assert mask_cases>0 and sha(SOURCE.read_bytes())==SOURCEPIN and sha(IR.read_bytes())==IRPIN
 report={'schema':'OpenMDK1.WrappedSourcePerspectivePixels.v1','status':'PASS','tests':len(cases),'cases':cases,'source_exe_sha256':PIN,
  'source_mto_sha256':SOURCEPIN,'material_sourceir_sha256':IRPIN,'function_identity':'B/default/flags2 @0x4730f0, table B slot2',
  'actual_source_payload_profiles':profiles,'cases_with_mask_crossings':mask_cases,
  'rule':'Per-interval perspective endpoint calculation feeds persistent integer/fraction state, but every texel address is masked by the combined linear width/height bitmask before adding the source base.',
  'closed_scope':'All four wrapped material payload identities used by120 LEVEL3 references, under guarded synthetic perspective input domains; exact byte/read/write equivalence.',
  'original_scene_visibility_verified':False,'live_runtime_profile_verified':False,'source_bytes_exported':False,
  'game_runtime_executed':False,'fidelity_verified':False,'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'wrapped-source-pixel-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
