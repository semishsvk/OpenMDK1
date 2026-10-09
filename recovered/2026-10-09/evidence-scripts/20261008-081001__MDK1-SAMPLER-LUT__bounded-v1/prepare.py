"""Rehydrate only pinned MDK evidence tools in this new output run.
No production runtime, worktree patch, source modification or live lease mutation.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'20261008-074645__MDK1-ALIAS-ACTIVE__bounded-v1'
CP=Path(r'F:\Remaster Framework\orchestrator\control-plane')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
receipt=json.loads((OLD/'iteration-receipt.json').read_text())
assert sha(OLD/'iteration-receipt.json')=='c522b7a413b8e09f73e81600896618886a7d726293495bad971c0f4e5397976c'
for n in ['static_probe.py','verify_f3_contract.py','geometry_contract.py','verify_material_plan_v2.py']:
    assert sha(OLD/n)==receipt['test_sources_sha256'][n]
    with (ROOT/n).open('xb') as f:f.write((OLD/n).read_bytes())
assert sha(OLD/'material-binding-sourceir.json')==receipt['sourceir_sha256']
with (ROOT/'baseline-material-sourceir.json').open('xb') as f:f.write((OLD/'material-binding-sourceir.json').read_bytes())
for p,h in receipt['immutable_input_hashes_verified'].items():
    assert sha(Path(p))==h,'Input changed: '+p
put(ROOT/'job-contract.json',{'schema':'OpenRemaster.BoundedEvidenceJob.v1','task':'MDK1-SAMPLER-LUT',
    'owner_scope':'THIS_NEW_EVIDENCE_DIRECTORY_ONLY','read_only_corpora':True,'native_game_processes':0,
    'source_and_control_hashes':receipt['immutable_input_hashes_verified'],
    'baseline_receipt_sha256':sha(OLD/'iteration-receipt.json'),'baseline_sourceir_sha256':receipt['sourceir_sha256'],
    'blocker':'Sampling/wrapping and LUT pixel semantics are not established for the corrected material bindings.',
    'hypothesis':'The original indexed renderer exposes deterministic address, masking, and destination-LUT transforms that can be isolated and falsified.',
    'expected_unlock':'Precise tested pixel-operation contracts instead of nearest/clamp/alpha guesses.',
    'max_process_seconds':40,'emulation_rule':'Instruction and memory allowlists, finite counts/timeouts, no host syscalls or live runtime.',
    'global_admission':'NO_NATIVE_GAME_OR_GPU_DISPATCH_REQUESTED',
    'azrael':'RETAIL_PAUSED_DEMO_CLOSED_NO_POLLING','created_at_utc':datetime.now(timezone.utc).isoformat()})
print('PREPARED',ROOT)
