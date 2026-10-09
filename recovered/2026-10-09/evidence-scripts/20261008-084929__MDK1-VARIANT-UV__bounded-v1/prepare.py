"""Rehydrate the pinned prior microtest tools in a new evidence-only workspace.
No game, GPU, service, production patch or shared-lease mutation is performed.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'20261008-081001__MDK1-SAMPLER-LUT__bounded-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,indent=2,sort_keys=True)
pin='5e7151ce43b37636f5f797c27c7f18ab34aba20aa497770614175c76a7e793b8'
assert sha(OLD/'iteration-receipt.json')==pin,'PRIOR_CHECKPOINT_CHANGED'
r=json.loads((OLD/'iteration-receipt.json').read_bytes())
for n in ['static_probe.py','verify_f3_contract.py','geometry_contract.py','sampler_probe.py','verify_sampler_v2.py','verify_sampling_contract.py','verify_material_plan_v2.py']:
    assert sha(OLD/n)==r['software_sha256'][n]
    with (ROOT/n).open('xb') as f:f.write((OLD/n).read_bytes())
for n,h in [('indexed-pixel-contract-sourceir.json',r['pixel_contract_sourceir_sha256']),('baseline-material-sourceir.json','b597a9f27d5e03b34117d02d893a6e8b456406c8d413a2dd73276e96db32e783')]:
    assert sha(OLD/n)==h
    with (ROOT/n).open('xb') as f:f.write((OLD/n).read_bytes())
for p,h in r['source_and_control_hashes'].items():assert sha(Path(p))==h,'IMMUTABLE_INPUT_CHANGED:'+p
put(ROOT/'job-contract.json',{'schema':'OpenRemaster.BoundedEvidenceJob.v1','task':'MDK1-VARIANT-UV',
 'owner_scope':'THIS_NEW_EVIDENCE_DIRECTORY_ONLY','source_and_control_hashes':r['source_and_control_hashes'],
 'prior_checkpoint':r['checkpoint'],'prior_receipt_sha256':pin,
 'blocker':'Which source-backed predicate selects the differing sampler variants, and how are UV values converted to fixed point and perspective callbacks?',
 'expected_unlock':'Explicit variant-selection predicate and tested rounding/conversion/routing contracts, not a guessed renderer default.',
 'native_game_processes':0,'max_single_process_seconds':40,'emulation':'Finite instruction, address and memory-write allowlists; no original OS calls.',
 'source_write_policy':'DENY','production_promotion':False,'azrael':'PAUSED_DEMO_CLOSED_NO_POLLING',
 'created_at_utc':datetime.now(timezone.utc).isoformat()})
print('PREPARED',ROOT)
