"""Lane A, bounded read-only continuation after verified newer checkpoint 004."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'20261008-084929__MDK1-VARIANT-UV__bounded-v1'
PIN='0e53976981c208631a5442769687b5ef0ffc410dd65ebb73ebd7d87986a0877c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
assert sha(BASE/'iteration-receipt.json')==PIN
r=json.loads((BASE/'iteration-receipt.json').read_text());assert r['status']=='PASS'
for n in ['static_probe.py','verify_f3_contract.py','verify_uv_rounding.py']:
 assert sha(BASE/n)==r['test_software_and_baseline_sha256'][n]
 with (ROOT/n).open('xb') as f:f.write((BASE/n).read_bytes())
for n,h in r['initial_report_sha256'].items():assert sha(BASE/n)==h
from static_probe import load,offset
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
b,secs=load();out=[];md=Cs(CS_ARCH_X86,CS_MODE_32)
for start,size in [(0x46dc79,0xa3),(0x46dd1c,0x350)]:
 at=offset(secs,start,size);raw=b[at:at+size]
 out.append({'va':hex(start),'file_offset':at,'sha256':hashlib.sha256(raw).hexdigest(),'instructions':[
 {'va':hex(i.address),'bytes':i.bytes.hex(),'op':i.mnemonic+' '+i.op_str} for i in md.disasm(raw,start)]})
put(ROOT/'depth-guard-code.json',{'source_exe_sha256':hashlib.sha256(b).hexdigest(),'regions':out})
put(ROOT/'job-contract.json',{'schema':'OpenRemaster.BoundedEvidenceJob.v1','task':'MDK_DEPTH_RATIO_GUARD','baseline_receipt_sha256':PIN,
 'baseline_checkpoint':r['checkpoint'],'hypothesis':'Depth-ratio guard computes a bounded adjustment/clipping operation, not the already tested branch predicate.',
 'falsification':'Compare exact original arithmetic/trace on boundary inputs; unresolved callbacks remain BLOCKED.',
 'mode':'INTERLEAVED_READ_ONLY','native_game_jobs':0,'worktree_writes':False,'output_scope':str(ROOT),
 'budget':{'seconds_per_probe':10,'max_emulated_instructions':100000,'new_heavy_jobs':0},
 'created_at_utc':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'baseline':'MDK1-VARIANT-UV-20261008-004','freshness':'HASH_VERIFIED','next':'depth-ratio guard','regions':[{'va':v['va'],'instructions':len(v['instructions'])} for v in out]}))
