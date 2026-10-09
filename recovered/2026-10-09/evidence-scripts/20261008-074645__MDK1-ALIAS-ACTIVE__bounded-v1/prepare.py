"""Read-only rehydration for one bounded MDK alias/face-selection investigation.
All outputs stay in this private evidence run; no production job, renderer or corpus writes.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'20261008-071409__MDK1-F3-CONSUMER__static-v1'
CP=Path(r'F:\Remaster Framework\orchestrator\control-plane')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,sort_keys=True)
r=json.loads((OLD/'iteration-receipt.json').read_text())
assert sha(OLD/'iteration-receipt.json')=='04b036ca82191c513a26aea7bcb310df28c67668c9e2eebdb2bc801bd05a0714'
for name in ['static_probe.py','verify_f3_contract.py']:
    assert sha(OLD/name)==r['script_sha256'][name]
    with (ROOT/name).open('xb') as f:f.write((OLD/name).read_bytes())
paths=[Path(r'F:\Remaster Framework\source\MDK\MDK95.EXE'),
       Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO'),
       Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3S.MTI')]
assert all(sha(p)==r['source_sha256'][p.name] for p in paths)
protected=[CP/n for n in ['portfolio-lanes-20261008-v3.json','orch_k003.py','leases.py','capabilities.json','worker-commissioning.json']]
put(ROOT/'job-contract.json',{'schema':'OpenRemaster.BoundedEvidenceJob.v1','task':'MDK1-ALIAS-ACTIVE',
  'project':'OpenMDK1','scope':'READ_ONLY_CORPUS_AND_ISOLATED_MICROTESTS','owner_scope':'THIS_NEW_OUTPUT_DIRECTORY_ONLY',
  'global_heavy_admission':'NOT_REQUESTED','max_native_game_processes':0,'max_test_wall_seconds':40,
  'blocker':'22 nonpayload material references and unresolved raw-record activation',
  'hypothesis':'Original loader or renderer normalizes nonpayload material descriptors before render dispatch.',
  'expected_unlock':'Exact classification of NONE/PEN references and source-backed active-face filtering.',
  'prior_checkpoint':r['checkpoint'],'source_hashes':{str(p):sha(p) for p in paths},
  'protected_hashes':{str(p):sha(p) for p in protected},'written_game_worktrees':False,
  'azrael':'NOT_POLLED_RETAIL_PAUSED_DEMO_CLOSED','created_at_utc':datetime.now(timezone.utc).isoformat()})
print('PREPARED',ROOT)
