"""New guard-body proof, not replay of the existing branch-selection tests.
Original code is emulated only over whitelisted addresses and synthetic memory;
all source vertex bytes, copied attributes, pointer changes and writes compared.
"""
from pathlib import Path
from datetime import datetime,timezone
import itertools,json,struct,math
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK
from static_probe import ROOT,load,offset,PIN,sha
V=(0x10020000,0x10020100,0x10020200);D=0x10010000;BUFFERS=(0x54dbb8,0x54dbd0,0x54dbe8)
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def test(zs):
 zs=tuple(f32(x) for x in zs)
 if any(not math.isfinite(z) or z<=0 for z in zs):raise ValueError('POSITIVE_FINITE_DOMAIN')
 u=machine();u.reg_write(UC_X86_REG_FPCW,0x37f)
 originals=[struct.pack('<6f',10.+i,20.+i,z,40.+i,50.+i,60.+i) for i,z in enumerate(zs)]
 for p,b in zip(V,originals):u.mem_write(p,b)
 u.mem_write(0x54dbb8,b'\xa5'*72)
 for p,v in [(STACK-124,D),(STACK-116,V[1]),(STACK-112,V[2]),(0x541482,1)]:w32(u,p,v)
 u.mem_write(D+28,struct.pack('<2f',0.,0.))
 u.mem_write(0x540b58,struct.pack('<f',1.));u.mem_write(0x540b64,struct.pack('<f',1.))
 u.reg_write(UC_X86_REG_EBP,STACK);u.reg_write(UC_X86_REG_EDX,V[0]);info={'end':False,'guard':False};writes=[]
 def code(uc,a,n,_):
  if a==0x46dc79:info['guard']=True
  if a==0x46dd1c:info['end']=True;uc.emu_stop();return
  if not any(x<=a and a+n<=y for x,y in [(0x46dc19,0x46dd1c),(0x46e0ed,0x46e182)]):raise ValueError('CODE_ESCAPE:'+hex(a))
 def write(uc,access,a,n,v,_):
  if STACK-192<=a and a+n<=STACK-108:return
  if 0x54dbb8<=a and a+n<=0x54dc00:writes.append((a,n));return
  raise ValueError('WRITE_ESCAPE:'+hex(a))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x46dc19,0x100ff000,timeout=150000,count=1000)
 if not info['end']:raise ValueError('DID_NOT_REACH_PERSPECTIVE')
 guarded=max(zs)>64*min(zs);threshold=f32(max(zs)/64)
 ptrs=[u.reg_read(UC_X86_REG_EDX),r32(u,STACK-116),r32(u,STACK-112)]
 expected_writes=[];changed=[]
 for i,(z,p,orig) in enumerate(zip(zs,ptrs,originals)):
  clamp=guarded and z<threshold;expect=bytearray(orig)
  if clamp:struct.pack_into('<f',expect,8,threshold)
  if p!=(BUFFERS[i] if clamp else V[i]) or bytes(u.mem_read(p,24))!=bytes(expect):raise ValueError('POINTER_OR_VERTEX_MISMATCH')
  if bytes(u.mem_read(V[i],24))!=orig:raise ValueError('SOURCE_VERTEX_CHANGED')
  if clamp:expected_writes.extend([(BUFFERS[i]+j,4) for j in range(0,24,4)]+[(BUFFERS[i]+8,4)]);changed.append(i)
  elif bytes(u.mem_read(BUFFERS[i],24))!=b'\xa5'*24:raise ValueError('UNUSED_BUFFER_CHANGED')
 if writes!=expected_writes or info['guard']!=guarded:raise ValueError('TRACE_MISMATCH')
 return {'z':zs,'entered_guard':guarded,'threshold':threshold if guarded else None,'clamped_vertices':changed,'writes':writes,'pass':True}
def main():
 b,s=load();at=offset(s,0x498fe4,8);constant=struct.unpack_from('<d',b,at)[0]
 if constant!=1/64:raise ValueError('SOURCE_CONSTANT_NOT_1_OVER_64')
 checks=[]
 for values in [(1.,1.,128.),(1.,2.,128.),(1.,64.,64.),(1.,64.,65.),(.25,10.,64.),(2.,3.,1024.),(100.,100.,100.),(1.,2.000000238418579,128.)]:
  for perm in sorted(set(itertools.permutations(values))):checks.append(test(perm))
 result={'schema':'OpenMDK1.DepthRatioGuardMechanism.v1','status':'PASS','tests':len(checks),'cases':checks,
  'rule':'If max_depth>64*min_depth, copy each vertex with depth below max_depth/64 to its private 24-byte scratch slot; replace only depth at +8; other attributes and source vertices are unchanged.',
  'constant':constant,'source_exe_sha256':PIN,'numeric_profile':'Explicit x87 FPCW 0x037f; finite positive binary32 vertex depths.',
  'claim_limit':'This is a guard before perspective interpolation, not polygon clipping, runtime camera evidence or a proof of stable pixels.',
  'native_game_executed':False,'runtime_fidelity_verified':False,'created_at_utc':datetime.now(timezone.utc).isoformat()}
 with (ROOT/'depth-guard-verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True)
 print(json.dumps({'status':'PASS','tests':len(checks),'delta':'guard copies and clamps depth only; exact write and pointer traces verified','sha256':sha((ROOT/'depth-guard-verification.json').read_bytes())}))
if __name__=='__main__':main()
