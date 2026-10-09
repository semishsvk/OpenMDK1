"""Actual variant-B default perspective entry: source 32-pixel alignment partition.
This is a different function from alternate B/slot4; identities are checked against
immutable source callback tables. No pixel code or full raster driver runs.
"""
from datetime import datetime,timezone
import json,struct,itertools
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK
from static_probe import ROOT,PIN,load,offset,sha
B,SECTIONS=load()
assert struct.unpack_from('<I',B,offset(SECTIONS,0x49bce4,4))[0]==0x471f82

def reference(x,n):
 align=x&31
 if align==0:
  full,tail=divmod(n,32);return [0,full,tail,32 if full else tail]
 head=32-align
 if n<head:return [0,0,n,n]
 full,tail=divmod(n-head,32);return [head,full,tail,head]

def run(x,n):
 if not 0<=n<=639 or not -65536<=x<=65535:raise ValueError('PARTITION_DOMAIN')
 u=machine();u.reg_write(UC_X86_REG_ESP,STACK);u.reg_write(UC_X86_REG_FPCW,0x37f)
 for p,v in [(0x54ec70,x),(0x54ec2c,n),(0x54ec1c,0x10080000)]:w32(u,p,v&0xffffffff)
 for p,v in [(0x54ec30,1.),(0x54ec34,2.),(0x54ec38,3.)]:u.mem_write(p,struct.pack('<f',v))
 state={'done':False,'instructions':0};writes=[]
 def code(uc,a,size,_):
  state['instructions']+=1
  if a==0x47201c:state['done']=True;uc.emu_stop();return
  if not 0x471f82<=a or a+size>0x47201c:raise ValueError('PARTITION_CODE_ESCAPE')
 def write(uc,access,a,size,v,_):
  if not STACK-84<=a or a+size>STACK:raise ValueError('PARTITION_WRITE_ESCAPE')
  writes.append((a-STACK,size))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x471f82,0x100ff000,timeout=100000,count=100)
 S=STACK-84;out=[r32(u,S+i) for i in (16,20,24,28)];expected=reference(x,n)
 if not state['done'] or out!=expected or out[0]+32*out[1]+out[2]!=n or u.reg_read(UC_X86_REG_ESP)!=S:raise ValueError('ORIGINAL_PARTITION_MISMATCH')
 return {'x':x,'span_delta':n,'head':out[0],'blocks32':out[1],'tail':out[2],'first_interpolation_width':out[3],'instructions':state['instructions'],'pass':True}

def main():
 xs=[-65536,-33,-1,*range(32),33,65535];ns=[0,1,2,7,15,30,31,32,33,63,64,65,127,638,639]
 cases=[run(x,n) for x,n in itertools.product(xs,ns)]
 report={'schema':'OpenMDK1.DefaultPerspectivePartition.v1','status':'PASS','tests':len(cases),'cases':cases,'source_exe_sha256':PIN,
  'canonical_function':'VARIANT_B_DEFAULT_PERSPECTIVE_FLAGS0 @0x471f82, source table B slot0',
  'rule':'Partitions source span_delta by screen-X modulo32 into initial alignment segment, full32 segments and tail. The first interpolation width is selected separately; total consumed lengths equal span_delta.',
  'identity_distinction':'Do not reuse alternate-profile endpoint-once slopes for this default path: the source explicitly schedules separate interpolation intervals.',
  'zero_width_scope':'The entry can partition a zero delta; upstream visibility/admission of degenerate triangles remains outside the gate.',
  'negative_screen_coordinates':'Only signed input arithmetic is tested; no claim unclipped negative destinations may be written.',
  'pixel_execution':False,'game_runtime_executed':False,'fidelity_verified':False,
  'next':'Original default-path interpolation at chunk boundaries and exact per-pixel outputs, without inheriting alternate-path results.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'default-span-partition-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
