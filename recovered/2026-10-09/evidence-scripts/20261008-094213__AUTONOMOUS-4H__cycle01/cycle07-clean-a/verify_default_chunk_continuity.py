"""Default-B perspective interval continuity on the exact constant-q subdomain.
This is a metamorphic coverage proof across aligned heads/full blocks/tails, not a
claim that varying-q perspective interpolation equals an affine ideal.
"""
from datetime import datetime,timezone
import json,struct,itertools
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.x86_const import *
from verify_perspective_span_inputs import make
from verify_f3_contract import w32,STACK,STOP
from static_probe import ROOT,PIN,sha
TEX,FRAME=0x20000000,0x10080000

def run(x,n,step,pattern):
 if not 0<=x<=31 or not 0<=n<=639 or step not in (-1,0,1):raise ValueError('CONTINUITY_DOMAIN')
 shift=8;width=256;height=128;u0=n+8 if step<0 else 8;v0=32;start=v0*width+u0
 texture=bytes((i*73+19)&255 if pattern==0 else (0 if i%13==0 else i&255) for i in range(width*height))
 expected_reads=[start+i*step for i in range(max(1,n))];pixels=bytes(texture[i] for i in expected_reads)
 if n:pixels+=pixels[-1:]
 u,_=make();u.mem_map(TEX,len(texture));u.mem_write(TEX,texture);before=b'\xa5'*(n+65);u.mem_write(FRAME-16,before)
 u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 for p,v in [(0x54ec2c,n),(0x54ec70,x),(0x54ec28,8),(0x54ec50,256),(0x54ec20,TEX),(0x54ec1c,FRAME)]:w32(u,p,v)
 for p,v in [(0x54ec30,1),(0x54ec34,u0),(0x54ec38,v0),(0x54ec10,0),(0x54ec14,step),(0x54ec18,0),(0x54ec80,0),(0x54ec84,32*step),(0x54ec88,0)]:u.mem_write(p,struct.pack('<f',v))
 reads=[];writes=[];state={'done':False,'instructions':0}
 def code(uc,a,size,_):
  state['instructions']+=1
  if a==STOP:state['done']=True;uc.emu_stop();return
  if not 0x471f82<=a or a+size>0x47278a:raise ValueError('CHUNK_CODE_ESCAPE')
 def read(uc,access,a,size,v,_):
  if TEX<=a<TEX+len(texture)+4096:
   if size!=1 or a>=TEX+len(texture):raise ValueError('CHUNK_SOURCE_BOUNDS')
   reads.append(a-TEX)
 def write(uc,access,a,size,v,_):
  if STACK-128<=a and a+size<=STACK:return
  if FRAME<=a and a+size<=FRAME+n+1 and size==1:writes.append((a-FRAME,v&255));return
  raise ValueError('CHUNK_WRITE_ESCAPE:'+hex(a))
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ,read);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x471f82,STOP+1,timeout=400000,count=30000)
 after=bytes(u.mem_read(FRAME-16,len(before)));expected=before[:16]+pixels+before[16+n+1:]
 if not state['done'] or reads!=expected_reads or writes!=list(enumerate(pixels)) or after!=expected:
  failure={'status':'FAIL','x':x,'delta':n,'step':step,'pattern':pattern,'expected_reads':expected_reads,'observed_reads':reads,'expected_pixels':list(pixels),'observed_writes':writes}
  p=ROOT/'default-chunk-counterexample.json'
  if not p.exists():p.write_text(json.dumps(failure,indent=2),encoding='utf-8')
  raise ValueError('CHUNK_CONTINUITY_COUNTEREXAMPLE')
 if bytes(u.mem_read(TEX,len(texture)))!=texture:raise ValueError('TEXTURE_MUTATED')
 return {'screen_x_mod32':x,'delta':n,'integer_u_step':step,'pattern':pattern,'reads':len(reads),'pixels':len(pixels),'pixels_sha256':sha(pixels),'instructions':state['instructions'],'pass':True}

def main():
 cases=[run(x,n,s,p) for x,n,s,p in itertools.product((0,1,7,15,16,30,31),(0,1,2,7,31,32,33,63,64,65,127,255,256,257,638,639),(-1,0,1),(0,1))]
 report={'schema':'OpenMDK1.DefaultChunkContinuity.v1','status':'PASS','tests':len(cases),'cases':cases,'source_exe_sha256':PIN,
  'function':'B/default/flags0 @0x471f82','domain':'q=1 constant, exact integral U steps -1/0/+1, zero V step; seven X residues and boundary deltas through639.',
  'independent_invariant':'The perspective function must reproduce the declared integral source-address sequence and exactly delta+1 byte writes including the final cached texel, regardless of partitioning.',
  'scope':'A strict constant-depth subdomain across multiple chunks; not a general varying-depth perspective model.',
  'game_runtime_executed':False,'fidelity_verified':False,'next':'Extend only with source-backed varying-q block arithmetic; never infer general perspective from this invariant.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'default-chunk-continuity-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
