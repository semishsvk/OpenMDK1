"""Join both signed-width branches with original q/uq/vq and gradient setup.
No render callback is invoked; this closes the untested counterpart of the
positive-width fixture while preserving exact x87 operation/store order.
"""
from fractions import Fraction
from datetime import datetime,timezone
import itertools,json,math,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK
from verify_perspective_inputs import quantize,f32
from static_probe import ROOT,PIN,sha
D=0x10010000;V=(0x10020000,0x10020100,0x10020200);UV=(0x10030000,0x10030100,0x10030200)

def rq(x):return quantize(x,64,0)
def rf(x):return quantize(x,24,0)
def run(width,short,total,zs,uvs):
 if not -10000<=width<=10000 or not 0<short<total<1000:raise ValueError('INTEGER_FIXTURE_DOMAIN')
 zs=tuple(f32(z) for z in zs);uvs=tuple(tuple(f32(x) for x in uv) for uv in uvs)
 if min(zs)<=0 or max(zs)>64*min(zs):raise ValueError('POST_GUARD_FIXTURE_DOMAIN')
 u=machine();u.reg_write(UC_X86_REG_FPCW,0x37f);u.reg_write(UC_X86_REG_EBP,STACK);u.reg_write(UC_X86_REG_EDX,V[0]);u.reg_write(UC_X86_REG_EBX,UV[1])
 u.mem_write(D,struct.pack('<13I',7,128,128,0,127,127<<7,(~127)&0xffffffff,0,0,0x20000000,0,0,0))
 originals=[]
 for i,(p,z,uv) in enumerate(zip(V,zs,uvs)):
  b=struct.pack('<6f',10.+i,20.+i,z,40.+i,50.+i,60.+i);u.mem_write(p,b);originals.append(b);u.mem_write(UV[i],struct.pack('<2f',*uv))
 for p,v in [(STACK-124,D),(STACK-116,V[1]),(STACK-112,V[2]),(STACK+8,UV[0]),(STACK+12,UV[1]),(STACK+16,UV[2]),(0x54ebec,width),(0x54ebfc,total),(0x54ec00,short),(0x5414b8,0)]:w32(u,p,v&0xffffffff)
 ends={'done':False,'negative_branch':False,'instructions':0};gradient_writes=[]
 targets=[0x54ec10,0x54ec80,0x54ec14,0x54ec84,0x54ec18,0x54ec88]
 def code(uc,a,n,_):
  ends['instructions']+=1
  if a==0x46e1a2:ends['negative_branch']=True
  if a==0x46dec8:ends['done']=True;uc.emu_stop();return
  if not any(x<=a and a+n<=y for x,y in [(0x46dd1c,0x46dec8),(0x46e1a2,0x46e1b1)]):raise ValueError('CODE_ESCAPE:'+hex(a))
 def write(uc,access,a,n,v,_):
  if n!=4:raise ValueError('NON_DWORD_WRITE')
  if a in targets:gradient_writes.append(a);return
  if a in (0x54ec20,0x54ec24,0x54ec28,0x54ec48,0x54ec4c,0x54ec50,0x54ebec):return
  if STACK-0xa8<=a and a+4<=STACK-0x80:return
  raise ValueError('WRITE_ESCAPE:'+hex(a))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x46dd1c,0x100ff000,timeout=150000,count=600)
 denominator=width+2*total if width>0 else width-2*total
 observed_den=struct.unpack('<i',u.mem_read(0x54ebec,4))[0]
 if not ends['done'] or ends['negative_branch']!=(width<=0) or observed_den!=denominator or gradient_writes!=targets:raise ValueError('SIGNED_PATH_OR_STORE_ORDER')
 q=[rf(rq(1/Fraction.from_float(z))) for z in zs]
 uq=[rf(Fraction.from_float(uv[0])*x) for uv,x in zip(uvs,q)];vq=[rf(Fraction.from_float(uv[1])*x) for uv,x in zip(uvs,q)]
 components=[q,uq,vq];stored=[]
 for a,addresses in zip(components,[(targets[0],targets[1]),(targets[2],targets[3]),(targets[4],targets[5])]):
  first=rq(rq(a[2]-a[0])*short);second=rq(rq(a[0]-a[1])*total);g=rq(rq(second+first)*rq(Fraction(1,denominator)))
  expected=[rf(g),rf(rq(g*32))]
  for value,p in zip(expected,addresses):
   got=bytes(u.mem_read(p,4));want=struct.pack('<f',float(value))
   if got!=want:raise ValueError('SIGNED_GRADIENT_NUMERIC_MISMATCH')
   stored.append(got.hex())
 if any(bytes(u.mem_read(p,24))!=b for p,b in zip(V,originals)):raise ValueError('INPUT_VERTEX_MUTATION')
 return {'width_before':width,'width_after':denominator,'short':short,'total':total,'depths':zs,'uvs':uvs,'gradient_f32_hex':stored,'negative_branch':ends['negative_branch'],'instructions':ends['instructions'],'pass':True}

def main():
 depths=[(1.,2.,4.),(3.,7.,11.),(11.25,10.75,12.5)]
 uvsets=[((1.,2.),(3.,4.),(5.,6.)),((1.1,-2.2),(3.3,4.4),(-5.5,6.6)),((0.,0.),(128.,0.),(0.,64.))]
 tests=[run(w,s,t,z,uv) for w,(s,t),z,uv in itertools.product((-257,-7,-1,0,1,7,257),((1,2),(3,7),(7,16)),depths,uvsets)]
 report={'schema':'OpenMDK1.SignedPerspectiveWidth.v1','status':'PASS','tests':len(tests),'cases':tests,
  'source_exe_sha256':PIN,'rule':'Signed width >0 uses width+2*total; width<=0 uses width-2*total. Both enter the same q/uq/vq and horizontal gradient operations.',
  'boundary_observation':'Zero width follows the nonpositive branch in this local code; this does not claim the upstream triangle classifier admits zero-area geometry.',
  'oracle':'Exact rational arithmetic with declared PC64 nearest-even x87 steps and binary32 stores, independently checked against original branch execution.',
  'scope':'Post-depth-guard setup through all six gradient stores, prior to callback selection/raster work.',
  'full_runtime_executed':False,'fidelity_verified':False,
  'next':'Perspective scanline interpolation and callback execution with finite pixel/address traces.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 with (ROOT/'signed-width-verification.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({'status':'PASS','tests':len(tests),'rule':report['rule'],'sha256':sha((ROOT/'signed-width-verification.json').read_bytes())}))
if __name__=='__main__':main()
