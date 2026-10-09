"""Independent profile-A default perspective model on all67 used LEVEL3 payloads.
The immutable U fractional step differs from profileB's DL-perturbed step. Pin
source callback identity and compare exact nonzero texel/read/write behavior.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
from datetime import datetime,timezone
import json,struct,itertools
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_default_varying_q_pixels import initialized_machine,partition
from verify_perspective_span_inputs import r,magic,BU,BV,signed
from verify_perspective_inputs import f32
from verify_f3_contract import w32,STACK,STOP
from static_probe import ROOT,PIN,load,offset,sha
IR=Path(r'F:\Remaster Framework\output\projects\OpenMDK1\evidence\20261008-074645__MDK1-ALIAS-ACTIVE__bounded-v1\material-binding-sourceir.json')
IRPIN='b597a9f27d5e03b34117d02d893a6e8b456406c8d413a2dd73276e96db32e783'
SOURCE=Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3')
KERNELS={('A',0):(0x477e04,0x4786a4),('A',2):(0x4790a2,0x479b54),('B',0):(0x471f82,0x47278a),('B',2):(0x4730f0,0x473b0a)}
TEX,DEST=0x20000000,0x10080000;MASK=0xffffffff


def model(profile,flags,w,h,n,x,values,data):
 shift=w.bit_length()-1;q,uq,vq,dq,duq,dvq=map(Fraction.from_float,values)
 def ep(a,b,c):inv=r(1/a);return r(b*inv),r(c*inv)
 u,v=ep(q,uq,vq);mu,mv=magic(u,BU),magic(v,BV)
 address=(((signed(mv)>>12)<<shift)+(mu>>16))&MASK;uf=mu<<16&MASK;vf=mv<<20&MASK
 if flags==2:address&=w*h-1
 reads=[];pix=[];head,full,tail=partition(x,n)
 for length in ([head] if head else [])+[32]*full+([tail] if tail else []):
  qn,un,vn=[r(a+r(g*length)) for a,g in zip((q,uq,vq),(dq,duq,dvq))]
  eu,ev=ep(qn,un,vn);recip=Fraction.from_float(f32(float(r(Fraction(1,length)))))
  du,dv=magic(r(r(eu-u)*recip),BU),magic(r(r(ev-v)*recip),BV)
  us=du<<16&MASK;vs=dv<<20&MASK;istep=(signed(du)>>16)+((signed(dv)>>12)<<shift)
  for _ in range(length):
   temp=vf+vs;vc=temp>>32;vf=temp&MASK
   temp=uf+us;uc=temp>>32;uf=temp&MASK
   if flags==2:address&=w*h-1
   if address>=len(data):raise ValueError('DECLARED_INPUT_ESCAPES_PAYLOAD')
   pixel=data[address];pix.append(pixel);reads.append(address)
   if profile=='B':us=(us&0xffffff00)|pixel
   address=(address+istep+(vc<<shift)+uc)&MASK
  q,uq,vq=qn,un,vn;u,v=eu,ev
 if n:pix.append(pix[-1])
 else:
  if address>=len(data):raise ValueError('ZERO_DELTA_SOURCE_BOUNDS')
  reads.append(address);pix.append(data[address])
 return reads,bytes(pix)


def run(profile,flags,w,h,n,x,values,data):
 values=tuple(map(f32,values))
 if profile not in ('A','B') or flags not in (0,2) or not 0<=n<=639 or not 0<=x<32 or w&(w-1) or len(data)!=w*h:raise ValueError('PROFILE_DOMAIN')
 if flags==2 and h&(h-1):raise ValueError('MASKED_HEIGHT_DOMAIN')
 if min(values[0],values[0]+values[3]*n)<=0:raise ValueError('DEPTH_DOMAIN')
 expected_reads,expected_pixels=model(profile,flags,w,h,n,x,values,data)
 u=initialized_machine();u.mem_map(TEX,(len(data)+4095)&~4095);u.mem_write(TEX,data)
 before=b'\xa5'*16+b'\x5a'*(n+1)+b'\xa5'*64;u.mem_write(DEST-16,before);u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 shift=w.bit_length()-1
 for p,v in [(0x54ec2c,n),(0x54ec70,x),(0x54ec28,shift),(0x54ec50,w),(0x54ec20,TEX),(0x54ec1c,DEST),(0x54ec24,w-1),(0x54ec48,(h-1)<<shift)]:w32(u,p,v)
 for p,v in zip((0x54ec30,0x54ec34,0x54ec38,0x54ec10,0x54ec14,0x54ec18),values):u.mem_write(p,struct.pack('<f',v))
 for p,g in zip((0x54ec80,0x54ec84,0x54ec88),values[3:]):u.mem_write(p,struct.pack('<f',f32(g*32)))
 lo,hi=KERNELS[(profile,flags)];reads=[];writes=[];done=[]
 def code(uc,a,size,_):
  if a==STOP:done.append(True);uc.emu_stop();return
  if not lo<=a or a+size>hi:raise ValueError('SOURCE_PROFILE_CODE_ESCAPE')
 def read(uc,access,a,size,v,_):
  if TEX<=a<TEX+len(data)+4096:
   if size!=1 or a>=TEX+len(data):raise ValueError('TEXTURE_READ_BOUNDS')
   reads.append(a-TEX)
 def write(uc,access,a,size,v,_):
  if STACK-128<=a and a+size<=STACK:return
  if DEST<=a and a+size<=DEST+n+1 and size==1:writes.append((a-DEST,v&255));return
  raise ValueError('PROFILE_WRITE_BOUNDS')
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(lo,STOP+1,timeout=300000,count=40000)
 expected=before[:16]+expected_pixels+before[16+n+1:]
 if not done or reads!=expected_reads or writes!=list(enumerate(expected_pixels)) or bytes(u.mem_read(DEST-16,len(before)))!=expected:
  bad={'profile':profile,'flags':flags,'n':n,'x':x,'values':values,'expected_reads':expected_reads,'reads':reads,'writes':writes,'expected_pixels':list(expected_pixels)}
  f=ROOT/'profile-a-pixel-counterexample.json'
  if not f.exists():f.write_text(json.dumps(bad,indent=2),encoding='utf-8')
  raise ValueError('PROFILE_A_SOURCE_PIXEL_MODEL_DIFF')
 if bytes(u.mem_read(TEX,len(data)))!=data or u.reg_read(UC_X86_REG_FPCW)!=0x37f:raise ValueError('INPUT_OR_FPU_MUTATION')
 return {'profile':profile,'flags':flags,'n':n,'x_mod32':x,'values':values,'pixels_sha256':sha(expected_pixels),
  'read_trace_sha256':sha(struct.pack('<'+'I'*len(reads),*reads)),'pass':True},expected_pixels


def main():
 raw=IR.read_bytes();assert sha(raw)==IRPIN;ir=json.loads(raw)
 refs=Counter((x['material_provider'],x['material_ordinal']) for x in ir['records'] if x['kind']=='TEXTURE_REFERENCE')
 mats=[m for ms in ir['materials'].values() for m in ms if (m['provider'],m['ordinal']) in refs]
 assert len(mats)==67
 source={n:(SOURCE/n).read_bytes() for n in ('LEVEL3O.MTO','LEVEL3S.MTI')}
 for n,h in ir['source_sha256'].items():assert sha(source[n])==h
 exe,sections=load()
 assert struct.unpack_from('<I',exe,offset(sections,0x49bcb4,4))[0]==0x477e04 and struct.unpack_from('<I',exe,offset(sections,0x49bcb4+8,4))[0]==0x4790a2
 cases=[]
 for m in mats:
  w,h=m['width'],m['height'];data=source[m['source_file']][m['raw_payload_offset']:m['raw_payload_offset']+w*h];assert sha(data)==m['first_plane_sha256']
  for n,x,values in itertools.product((0,1,31,33,65),(0,5),[(1.,w/4,h/2,1/4096,1/32,0.),(2.,w/2,h,-1/4096,-1/16,0.)]):
   obs,_=run('A',m['runtime_flags'],w,h,n,x,values,data);obs.update(material_name=m['name'],provider=m['provider'],ordinal=m['ordinal'],payload_sha256=m['first_plane_sha256']);cases.append(obs)
 texture=bytes([255,7])+bytes([29])*62;v=(1.,65535/65536,0.,0.,0.,0.)
 aa,pa=run('A',2,8,8,639,5,v,texture);bb,pb=run('B',2,8,8,639,5,v,texture)
 first=next((i for i,(a,b) in enumerate(zip(pa,pb)) if a!=b),None);assert first is not None
 cases.append({'case':'profile-specific-fractional-carry-negative-control','pass':True,'first_different_pixel':first})
 report={'schema':'OpenMDK1.ProfileASourcePerspectivePixels.v1','status':'PASS','tests':len(cases),'cases':cases,'source_exe_sha256':PIN,
  'tested_source_materials':67,'source_texture_references_represented':sum(refs.values()),'source_ir_sha256':IRPIN,'source_data_sha256':ir['source_sha256'],
  'source_function_identities':{str(k):hex(v[0]) for k,v in KERNELS.items()},
  'rule':'A/default retains the U fractional step in scratch storage; the sampled DL value does not replace that step. Both default A0 and A2 use the source perspective chunk schedule, with masking only for A2.',
  'counterexample':{'first_different_pixel':first,'A_pixel':pa[first],'B_pixel':pb[first],'A_trace':aa,'B_trace':bb},
  'claim':'Exact read/write/pixel equivalence on bounded synthetic camera-interpolant inputs using every source material payload identity. Not a captured LEVEL3 frame.',
  'live_profile_selected':False,'source_bytes_exported':False,'game_runtime_executed':False,'fidelity_verified':False,
  'next':'Keep profile contracts distinct and validate original triangle coverage and camera/depth state before image-level promotion.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'profile-a-source-pixel-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
