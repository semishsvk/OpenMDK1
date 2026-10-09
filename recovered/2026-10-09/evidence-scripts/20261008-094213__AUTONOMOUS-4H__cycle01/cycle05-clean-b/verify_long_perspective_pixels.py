"""Original A0 perspective kernel to exact pixels for a bounded 33..637 delta spans.
Independent exact-rational endpoint setup + integer carry model; texture reads,
write order and cached-final-pixel behavior are compared, not merely image hashes.
"""
from datetime import datetime,timezone
from fractions import Fraction
import itertools,json,struct,math
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.x86_const import *
from verify_perspective_span_inputs import make,r,floatbytes,magic,BU,BV,signed
from verify_perspective_inputs import f32
from verify_f3_contract import w32,r32,STACK,STOP
from static_probe import ROOT,PIN,sha
TEX,FRAME=0x20000000,0x10080000;MASK=0xffffffff

def reference(n,shift,vals,texture):
 ql,qr,ul,vl,ur,vr=map(Fraction.from_float,vals)
 invl=r(1/ql);invr=r(1/qr);u0=r(ul*invl);v0=r(vl*invl);u1=r(ur*invr);v1=r(vr*invr)
 recip=Fraction.from_float(struct.unpack('<f',floatbytes(r(Fraction(1,n+2)),24))[0])
 ufixed,vfixed=magic(u0,BU),magic(v0,BV)
 du,dv=magic(r(r(u1-u0)*recip),BU),magic(r(r(v1-v0)*recip),BV)
 address=((signed(vfixed)>>12)<<shift)+(ufixed>>16)
 uf=(ufixed<<16)&MASK;vf=(vfixed<<20)&MASK;stepu=(du<<16)&MASK;stepv=(dv<<20)&MASK
 integerstep=(signed(du)>>16)+((signed(dv)>>12)<<shift)
 indices=[];pixels=[]
 for j in range(max(1,n)):
  vv=vf+stepv;vcarry=vv>MASK;vf=vv&MASK
  uu=uf+stepu;ucarry=uu>MASK;uf=uu&MASK
  if not 0<=address<len(texture):raise ValueError('MODEL_TEXEL_OUT_OF_DOMAIN')
  texel=texture[address];indices.append(address);pixels.append(texel)
  stepu=(stepu&0xffffff00)|texel
  address=(address+integerstep+((1<<shift) if vcarry else 0)+int(ucarry))&MASK
 if n>0:pixels.append(pixels[-1])
 return indices,bytes(pixels)

def run(n,shift,values,pattern):
 if not 33<=n<=637 or shift not in (5,7,8):raise ValueError('BOUNDED_SPAN_DOMAIN')
 vals=tuple(map(f32,values));width=1<<shift;height=128
 texture=bytes(((i*73+19)&255) if pattern==0 else (0 if i%7==0 else i&255) for i in range(width*height))
 expected_reads,expected_pixels=reference(n,shift,vals,texture)
 u,tablesha=make();u.mem_map(TEX,(len(texture)+4095)&~4095);u.mem_write(TEX,texture)
 u.mem_write(FRAME-16,b'\xa5'*(n+1+64));before=bytes(u.mem_read(FRAME-16,n+1+64))
 u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 for p,v in [(0x54ec2c,n),(0x54ec28,shift),(0x54ec50,width),(0x54ec20,TEX),(0x54ec1c,FRAME)]:w32(u,p,v)
 ql,qr,ul,vl,ur,vr=vals
 for p,v in [(0x54ec30,ql),(0x54ec3c,qr),(0x54ec34,ul),(0x54ec38,vl),(0x54ec40,ur),(0x54ec44,vr)]:u.mem_write(p,struct.pack('<f',v))
 reads=[];writes=[];state={'done':False,'instructions':0,'unrolled_blocks':0}
 def code(uc,a,size,_):
  state['instructions']+=1
  if a==0x471027:state['unrolled_blocks']+=1
  if a==STOP:state['done']=True;uc.emu_stop();return
  if not 0x470f08<=a or a+size>0x47124e:raise ValueError('KERNEL_CODE_ESCAPE:'+hex(a))
 def read(uc,access,a,size,value,_):
  if TEX<=a<TEX+len(texture)+4096:
   if size!=1 or a>=TEX+len(texture):raise ValueError('TEXEL_BOUNDS')
   reads.append(a-TEX)
 def write(uc,access,a,size,value,_):
  if STACK-128<=a and a+size<=STACK:return
  if a==0x54ec2c and size==4:return
  if FRAME<=a and a+size<=FRAME+n+1:
   if size!=1:raise ValueError('PIXEL_WRITE_SIZE')
   writes.append((a-FRAME,value&255));return
  raise ValueError('PIXEL_WRITE_ESCAPE:'+hex(a))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x470f08,STOP+1,timeout=300000,count=20000)
 after=bytes(u.mem_read(FRAME-16,len(before)));expected_frame=before[:16]+expected_pixels+before[16+n+1:]
 if not state['done'] or reads!=expected_reads or writes!=list(enumerate(expected_pixels)) or after!=expected_frame:
  failure={'status':'FAIL','n':n,'shift':shift,'inputs':vals,'expected_reads':expected_reads,'actual_reads':reads,'expected_pixels':list(expected_pixels),'actual_writes':writes}
  path=ROOT/'long-perspective-counterexample.json'
  if not path.exists():path.write_text(json.dumps(failure,indent=2),encoding='utf-8')
  raise ValueError('ORIGINAL_PERSPECTIVE_PIXEL_DIFFERENCE')
 if state['unrolled_blocks']!=(n-1)//32:raise ValueError('UNROLLED_BOUNDARY_COUNT')
 if bytes(u.mem_read(TEX,len(texture)))!=texture:raise ValueError('SOURCE_TEXTURE_CHANGED')
 return {'span_delta':n,'width_shift':shift,'inputs':vals,'texture_pattern':pattern,'pixel_count':n+1,'read_count':len(reads),
  'pixel_sha256':sha(expected_pixels),'read_order_sha256':sha(struct.pack('<'+'I'*len(reads),*reads)),'instructions':state['instructions'],'unrolled_blocks':state['unrolled_blocks'],'pass':True}

def main():
 inputs=[(1.,1.,7.75,20.5,19.25,22.125),(2.,4.,18.,60.,100.,128.),(.5,1.,4.125,11.,15.5,28.),(1.,1.,21.,45.,7.,39.)]
 tests=[run(n,shift,v,p) for n,shift,v,p in itertools.product((33,34,63,64,65,95,96,127,128,255,256,257,511,637),(5,7,8),inputs,(0,1))]
 report={'schema':'OpenMDK1.LongPerspectivePixelMechanism.v1','status':'PASS','tests':len(tests),'cases':tests,'source_exe_sha256':PIN,
  'kernel':'A0 perspective 0x470f08..0x47124d','declared_profile':'PC64 x87 round-to-nearest-even; span_delta 33..637; texture payload bounds checked.',
  'rule':'Endpoints divide uq/vq by q; slopes use reciprocal(span_delta+2); original magic-bias fixed conversion and integer carry stepping produce span_delta+1 writes. Final cached texel is repeated when delta>0.',
  'register_effect':'The source texel written to DL changes the low byte of EDX used by later U fractional additions; reference reproduces this actual instruction effect.',
  'compared':'All source texel addresses/order, all destination byte writes/order, pixel buffers and surrounding guards.',
  'coverage_limit':'Establishes A0 unrolled block and tail transitions only; does not establish alternate kernels, perspective triangle coverage or live variant selection.',
  'native_game_executed':False,'pixel_mechanism_only':True,'runtime_fidelity_verified':False,
  'next':'Close alternate perspective kernel flags and driver ABI before production integration; A0 span coverage is now bounded through reciprocal-table index639.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'long-perspective-pixel-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
