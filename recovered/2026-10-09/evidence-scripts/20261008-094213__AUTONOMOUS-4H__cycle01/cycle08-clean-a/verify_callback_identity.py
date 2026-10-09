"""Independent identity audit of the measured perspective function.
The numerical proofs remain tied to VA0x470f08, but an informal A0 label is wrong:
original table installation and selector execution identify variant B, alternate slot0.
No prior proof is rewritten and no live CPU/profile is inferred.
"""
from datetime import datetime,timezone
import json,struct,hashlib
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK,STOP
from static_probe import ROOT,load,offset,PIN,sha
B,SECTIONS=load();DESCRIPTOR=0x10010000
SOURCES={0:0x49bce4,1:0x49bcb4}

def run(profile,flags,alternate):
 u=machine();u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP);u.reg_write(UC_X86_REG_EAX,profile)
 phase={'mode':'install','done':False};writes=[]
 def code(uc,a,n,_):
  if a==(STOP if phase['mode']=='install' else 0x46dedb):phase['done']=True;uc.emu_stop();return
  lo,hi=(0x46da6c,0x46daa9) if phase['mode']=='install' else (0x46deb6,0x46dedb)
  if not lo<=a or a+n>hi:raise ValueError('IDENTITY_CODE_ESCAPE')
 def write(uc,access,a,n,v,_):
  if STACK-64<=a and a+n<=STACK:return
  if phase['mode']=='install' and 0x54dc00<=a and a+n<=0x54dc30:writes.append((a,n));return
  if phase['mode']=='select' and a==0x54ec88 and n==4:return
  raise ValueError('IDENTITY_WRITE_ESCAPE')
 ch=u.hook_add(UC_HOOK_CODE,code);wh=u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x46da6c,STOP+1,timeout=100000,count=100)
 p=SOURCES[bool(profile)];source=B[offset(SECTIONS,p,48):offset(SECTIONS,p,48)+48]
 if not phase['done'] or bytes(u.mem_read(0x54dc00,48))!=source:raise ValueError('ORIGINAL_TABLE_INSTALL_MISMATCH')
 u.hook_del(ch);u.hook_del(wh)
 # Seed the single unrelated FSTP using the original FLD1 at0x46dd81.
 assert B[offset(SECTIONS,0x46dd81,2):offset(SECTIONS,0x46dd81,2)+2]==b'\xd9\xe8'
 u.emu_start(0x46dd81,0x46dd83,count=1)
 w32(u,DESCRIPTOR+12,flags);w32(u,0x5414b8,alternate);u.reg_write(UC_X86_REG_EAX,DESCRIPTOR)
 phase.update(mode='select',done=False);u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x46deb6,STOP+1,timeout=100000,count=50)
 slot=(flags&3)+(4 if alternate else 0);expected=struct.unpack_from('<I',source,slot*4)[0]
 if not phase['done'] or u.reg_read(UC_X86_REG_EBX)!=expected:raise ValueError('CALLBACK_SELECTION_MISMATCH')
 return {'profile':'A' if profile else 'B','profile_input':profile,'flags':flags,'alternate':alternate,'slot':slot,'target':hex(expected),'pass':True}

def main():
 cases=[run(p,f,a) for p in (0,1,0xffffffff) for f in (0,1,2,3,0x10000,0x10003,0xffffffff) for a in (0,1,0x80000000)]
 tables={label:list(struct.unpack_from('<12I',B,offset(SECTIONS,SOURCES[p],48))) for p,label in [(0,'B'),(1,'A')]}
 identity=[(profile,i) for profile,values in tables.items() for i,x in enumerate(values) if x==0x470f08]
 if identity!=[('B',4)]:raise ValueError('MEASURED_FUNCTION_IDENTITY_CHANGED')
 affected=['perspective-span-input-verification.json','short-perspective-pixel-verification.json','long-perspective-pixel-verification.json']
 refs={n:sha((ROOT/n).read_bytes()) for n in affected}
 report={'schema':'OpenMDK1.PerspectiveCallbackIdentity.v1','status':'PASS_CORRECTION','tests':len(cases)+1,'cases':cases,
  'source_exe_sha256':PIN,'callback_tables':{p:[hex(x) for x in v] for p,v in tables.items()},
  'measured_function':{'va':'0x470f08','canonical_id':'VARIANT_B_ALTERNATE_PERSPECTIVE_FLAGS0','table_slot':4,'selector_condition':'profile B, alternate global nonzero, material flags&3==0'},
  'superseded_informal_label':'A0 perspective in three preceding reports: numerical mechanism assertions are still valid for the exact same original VA, but that label must not select a production profile.',
  'affected_reports_unchanged':refs,'no_numeric_test_rerun_required':'The correction changes scope/identity only. Prior numerical tests already pin the same immutable EXE and VA.',
  'withdrawn_speculative_blocker':'0x46e940 is not slot0 of either installed callback table. A presumed callback ABI mismatch based on that pointer must not be used as established evidence.',
  'live_runtime_profile':'NOT_OBSERVED','production_profile_selected':False,'game_runtime_executed':False,
  'next':'Test actual default-perspective slots independently; do not transplant alternate-path numerics into them.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'callback-identity-correction.json'
 with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in report.items() if k not in ('cases','callback_tables')},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
