"""Repeat the bounded static/instruction tests from clean software copies and seal.
No game runtime, corpus mutation, worktree patch, lease edit or renderer capture.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent
CP=Path(r'F:\Remaster Framework\orchestrator\control-plane')
EXPECTED={'f3-consumer-verification.json':'2f54092f6c4cef2584625d9a1ca3f9ec1255ef1515d8f7e07612bf2855686f93',
    'provider-precedence-verification-v2.json':'bf9d60023d11d57b10c4944b3615a9aa38fef66d7a2850fa062779d56884f921'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,sort_keys=True)
def semantic(r):return {k:v for k,v in r.items() if k!='created_at_utc'}
def main():
    for n,d in EXPECTED.items():
        if sha(ROOT/n)!=d or load(ROOT/n)['status']!='PASS':raise RuntimeError('INPUT_RECEIPT_MISMATCH')
    first=load(ROOT/'f3-consumer-verification.json');provider=load(ROOT/'provider-precedence-verification-v2.json')
    hashes={p.name:sha(p) for p in ROOT.glob('*.py')}
    fresh=ROOT/'clean-repeat';fresh.mkdir(exist_ok=False)
    scripts=['static_probe.py','verify_f3_contract.py','validate_provider_precedence_v2.py']
    for n in scripts:
        with (fresh/n).open('xb') as f:f.write((ROOT/n).read_bytes())
        if sha(fresh/n)!=hashes[n]:raise RuntimeError('RESTORE_HASH_MISMATCH')
    runs=[]
    for n,outname in [('verify_f3_contract.py','f3-consumer-verification.json'),
                      ('validate_provider_precedence_v2.py','provider-precedence-verification-v2.json')]:
        p=subprocess.run([sys.executable,'-B',str(fresh/n)],cwd=fresh,capture_output=True,text=True,timeout=40,
                         env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        with (fresh/(n+'.log')).open('x',encoding='utf-8') as f:f.write(p.stdout+'\n'+p.stderr)
        result=load(fresh/outname) if (fresh/outname).is_file() else {}
        equal=semantic(result)==semantic(load(ROOT/outname))
        runs.append({'script':n,'exit_code':p.returncode,'semantic_report_identical':equal,
            'status':'PASS' if p.returncode==0 and result.get('status')=='PASS' and equal else 'FAIL',
            'report_sha256':sha(fresh/outname) if (fresh/outname).is_file() else None})
    stable=all(sha(ROOT/n)==h for n,h in hashes.items()) and all(sha(fresh/n)==hashes[n] for n in scripts)
    passed=stable and all(r['status']=='PASS' for r in runs)
    portfolio=load(CP/'portfolio-lanes-20261008-v3.json')
    checkcount=first['test_count']+provider['checks_pass']
    result={'schema':'OpenMDK1.F3ConsumerIterationReceipt.v1',
      'checkpoint':'MDK1-F3-CONSUMER-20261008-STATIC-001',
      'status':'PASS' if passed else 'FAIL',
      'evidence_class':'CORPUS_STATIC_DATAFLOW_PLUS_ISOLATED_ORIGINAL_INSTRUCTION_EMULATION',
      'full_original_game_runtime_executed':False,'native_game_execution':False,
      'production_binding_changed':False,'fidelity_verified':False,
      'mechanism_tests':first['test_count'],'mechanism_passed':first['passed'],
      'provider_checks':provider['checks_pass'],'combined_checks_per_pass':checkcount,
      'completed_passes':2 if passed else 1,'clean_repeat':runs,
      'semantic_repeat_excludes_only':'created_at_utc',
      'candidate_sources_unchanged':stable,'script_sha256':hashes,
      'source_sha256':{'MDK95.EXE':first['source_exe_sha256'],'LEVEL3O.MTO':first['corpus']['source_sha256'],
                      'LEVEL3S.MTI':provider['source_mti_sha256']},
      'corpus_counts':{'raw_records':7205,'nonnegative_material_indices':1691,'negative_render_codes':5514,
         'zero_indices':124,'primary_LEVEL3S_MTI':140,'primary_texture_descriptors':118,
         'primary_alias_or_nonpayload_descriptors':22,'secondary_current_HMO_MAT':1551,
         'unresolved_names_in_tested_tables':0,'HMO4_XTOMB_F_primary_over_secondary_records':88,
         'HMO7_minus1024_records':151,'old_modulo_disagreements':1374,'old_modulo_comparable_positive_records':1537},
      'resolved_in_scope':['signed f3 extraction at record +6','direct nonnegative pointer-table indexing including zero',
        'case-sensitive first-match registry resolver','primary LEVEL3S.MTI before current HMO embedded MAT',
        'negative code dispatch; -1024..-1027 select LUT banks 0..3',
        'old selector-modulo rule is not original material identity mechanism'],
      'remaining':['Resolve final normalization/activation of 22 alias or nonpayload cases.',
        'Establish which raw records become visible/runtime-active faces; do not equate 7205 records with rendered geometry.',
        'UV/sampling, LUT pixel operation and depth semantics are not closed.',
        'Runtime integration and original-game visual fidelity comparison still required.'],
      'retained_failed_probe':'provider-v1-failure.json: standalone MTI length convention cannot be imposed on embedded HMO size word.',
      'new_game_builds':0,'gpu_jobs':0,'azrael_polled':False,'azrael_lease_changed':False,
      'game_worktrees_written':False,'authoritative_corpora_written':False,
      'next_task':'Trace alias/nonpayload normalization and active face selection before installing corrected material binding.',
      'portfolio':[], 'created_at_utc':datetime.now(timezone.utc).isoformat()}
    for e in portfolio['entries']:
        status='NO_NEW_EXECUTION'
        if e['id']=='OpenMDK1':status='STATIC_CONSUMER_CONTRACT_PASS' if passed else 'STATIC_CONSUMER_CONTRACT_FAIL'
        elif e['id']=='OpenAzrael-Demo':status='CLOSED_BY_OWNER'
        elif e['id']=='OpenAzrael-Retail':status='PAUSED_NOT_POLLED'
        result['portfolio'].append({'project':e['id'],'lane':e['lane'],'status':status})
    put(ROOT/'iteration-receipt.json',result)
    put(ROOT/'CONTINUATION.json',{'checkpoint':result['checkpoint'],'current_focus':'OpenMDK1',
        'evidence_scope':result['evidence_class'],'status':result['status'],
        'next':result['next_task'],'other_focus_lanes':['OpenStonekeep','OpenUltima8'],
        'azrael':'RETAIL_PAUSED_DEMO_CLOSED','no_new_runtime_fidelity_claim':True,
        'iteration_receipt_sha256':sha(ROOT/'iteration-receipt.json')})
    # Every trace records bytes and hashes. No original executable/assets included.
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name not in {'sealed-manifest.json','mdk1-f3-static-evidence.zip'})
    put(ROOT/'sealed-manifest.json',{'schema':'OpenRemaster.SealedEvidenceManifest.v1','files':[
        {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]})
    with zipfile.ZipFile(ROOT/'mdk1-f3-static-evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in files+[ROOT/'sealed-manifest.json']:z.write(p,p.relative_to(ROOT).as_posix())
    print(json.dumps({k:v for k,v in result.items() if k not in {'script_sha256','portfolio'}},indent=2))
    print('ITERATION_RECEIPT_SHA256',sha(ROOT/'iteration-receipt.json'))
    print('MANIFEST_SHA256',sha(ROOT/'sealed-manifest.json'))
    print('PACKAGE_SHA256',sha(ROOT/'mdk1-f3-static-evidence.zip'))
    return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
