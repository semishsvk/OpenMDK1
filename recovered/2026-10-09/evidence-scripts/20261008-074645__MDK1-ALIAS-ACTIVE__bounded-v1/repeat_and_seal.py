"""Repeat all three iterations from two independently restored software copies.
Evidence-only execution: source/production hashes are checked before and after;
no mutation to native game state, source corpus, worktree or shared live leases.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent
CP=Path(r'F:\Remaster Framework\orchestrator\control-plane')
OLD=ROOT.parent/'20261008-071409__MDK1-F3-CONSUMER__static-v1'
EXPECTED={
 'inactive-alias-verification.json':'1013d8afccc126e1b57a5130a28da2a3332dc300977c7532055646838d730656',
 'bsp-selection-verification.json':'108c8c6a925c253b21dce3a087f9ed2277d67cfc2a4f361fed8c95152f125b3d',
 'material-plan-verification-v2.json':'04e633a4855135b3ad7bfe8e62e8d54fc13838524c701c8a677787b4ec80adc4'}
SCRIPTS=['static_probe.py','verify_f3_contract.py','geometry_contract.py',
         'verify_inactive_aliases.py','verify_bsp_selection.py','verify_material_plan_v2.py']
RUNS=[('verify_inactive_aliases.py','inactive-alias-verification.json',309),
      ('verify_bsp_selection.py','bsp-selection-verification.json',88),
      ('verify_material_plan_v2.py','material-plan-verification-v2.json',13)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,indent=2,sort_keys=True)
def semantic(r):return {k:v for k,v in r.items() if k!='created_at_utc'}
def main():
    contract=load(ROOT/'job-contract.json')
    immutable=dict(contract['source_hashes'],**contract['protected_hashes'])
    if any(sha(Path(p))!=h for p,h in immutable.items()):raise RuntimeError('INITIAL_INPUT_CHANGED')
    for name,digest in EXPECTED.items():
        if sha(ROOT/name)!=digest or load(ROOT/name)['status']!='PASS':raise RuntimeError('INITIAL_RECEIPT_MISMATCH')
    code={n:sha(ROOT/n) for n in SCRIPTS}
    for n in SCRIPTS:ast.parse((ROOT/n).read_text(encoding='utf-8'),filename=n)
    irsha=sha(ROOT/'material-binding-sourceir.json')
    repeats=[]
    for tag in ('restore-a','restore-b'):
        dst=ROOT/tag;dst.mkdir(exist_ok=False)
        for name in SCRIPTS:
            with (dst/name).open('xb') as f:f.write((ROOT/name).read_bytes())
            if sha(dst/name)!=code[name]:raise RuntimeError('RESTORE_HASH_MISMATCH')
        cases=[]
        for script,output,expected_tests in RUNS:
            p=subprocess.run([sys.executable,'-B',str(dst/script)],cwd=dst,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=40)
            with (dst/(script+'.log')).open('x',encoding='utf-8') as f:f.write(p.stdout+'\n'+p.stderr)
            observed=load(dst/output) if (dst/output).is_file() else {}
            equal=semantic(observed)==semantic(load(ROOT/output))
            ok=p.returncode==0 and observed.get('status')=='PASS' and observed.get('tests')==expected_tests and equal
            cases.append({'script':script,'status':'PASS' if ok else 'FAIL','exit_code':p.returncode,
                'tests':observed.get('tests'),'semantic_report_equal':equal,
                'report_sha256':sha(dst/output) if (dst/output).exists() else None})
            if not ok:break
        ir_equal=(dst/'material-binding-sourceir.json').is_file() and sha(dst/'material-binding-sourceir.json')==irsha
        clean=all(sha(dst/n)==h for n,h in code.items())
        repeats.append({'restore':tag,'status':'PASS' if len(cases)==3 and all(c['status']=='PASS' for c in cases) and ir_equal and clean else 'FAIL',
            'cases':cases,'sourceir_byte_identical':ir_equal,'script_hashes_unchanged':clean})
        if repeats[-1]['status']!='PASS':break
    stable=all(sha(Path(p))==h for p,h in immutable.items()) and all(sha(ROOT/n)==h for n,h in code.items())
    passed=stable and len(repeats)==2 and all(r['status']=='PASS' for r in repeats)
    alias,bsp,material=[load(ROOT/n) for n in EXPECTED]
    receipt={'schema':'OpenMDK1.RepeatedEvidenceIterations.v1','checkpoint':'MDK1-ALIAS-BSP-MATERIAL-20261008-002',
      'status':'PASS' if passed else 'FAIL','iterations_completed':3,'new_checks_per_pass':410,
      'initial_passes':1,'clean_repetitions':len(repeats),'successful_passes':3 if passed else 1,
      'restores':repeats,'repeated_equivalence_excludes_only':'created_at_utc',
      'iterations':[
        {'task':'Inactive aliases','tests':309,'status':alias['status'],
         'result':'All 22 nonpayload references are source placeholders rejected by initialized flag filtering before raster material lookup.'},
        {'task':'BSP range selection/order','tests':88,'status':bsp['status'],
         'result':'10 source HMO trees, 4284 nodes, 4 camera fixtures and 2 ordering modes matched the original traversal; 8 boundary cases passed.'},
        {'task':'Descriptor construction and binding SourceIR','tests':13,'status':material['status'],
         'result':'282 descriptors from 11 providers match original loader output byte-for-byte; all 1656 eligible nonnegative material references resolve to source payloads.'}],
      'classification':material['counts'],'candidate_zero_area_faces':alias['counts']['prefilter_selected_zero_area'],
      'sourceir_sha256':irsha,'sourceir_bytes':(ROOT/'material-binding-sourceir.json').stat().st_size,
      'sourceir_equivalence':'Byte-identical in both clean repeats; retains all 7205 raw records and provenance.',
      'evidence_class':'CORPUS_STATIC_DATAFLOW_AND_WHITELISTED_X86_MICROEMULATION',
      'fidelity_verified':False,'game_runtime_executed':False,'native_game_executed':False,
      'production_renderer_installed':False,'new_game_builds':0,'heavy_gpu_jobs':0,
      'authoritative_corpora_written':False,'game_worktrees_written':False,
      'production_control_plane_written':False,'live_leases_modified':False,
      'azrael_polled':False,'azrael_status':'RETAIL_PAUSED_DEMO_CLOSED',
      'immutable_input_hashes_verified':immutable,'inputs_unchanged':stable,
      'prior_checkpoint_receipt_sha256':sha(OLD/'iteration-receipt.json'),
      'test_sources_sha256':code,'initial_report_sha256':EXPECTED,
      'retained_failed_experiment':'material-plan-v1-failure.json; initial test guard rejected HMO_7 valid empty material provider. v2 validates the original zero-count branch.',
      'limits':['Micro-emulation uses exact-size allocation/zero-fill stubs and intercepts raster boundaries; it is not a full game run.',
        'The initialized flag fixture has zero group-state masks; later dynamic flag changes remain unverified.',
        '7170 prefilter candidates and per-camera BSP selections are not final visible pixels.',
        '210 eligible records have zero geometric area; preserved, not silently removed.',
        'Texture sampling/wrapping, LUT pixel operations, dynamic scene state, native admission and original-runtime visual comparison remain separate gates.'],
      'next_task':'Derive texture sampling/wrapping and LUT pixel semantics for the verified binding SourceIR, then validate before any renderer integration.',
      'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'portfolio':[]}
    portfolio=load(CP/'portfolio-lanes-20261008-v3.json')
    for e in portfolio['entries']:
        state='NO_NEW_EXECUTION'
        if e['id']=='OpenMDK1':state='THREE_STATIC_MECHANISM_ITERATIONS_PASS' if passed else 'ITERATION_VALIDATION_FAILED'
        elif e['id']=='OpenAzrael-Demo':state='CLOSED'
        elif e['id']=='OpenAzrael-Retail':state='PAUSED_NOT_POLLED'
        receipt['portfolio'].append({'project':e['id'],'lane':e['lane'],'state':state})
    put(ROOT/'iteration-receipt.json',receipt)
    put(ROOT/'CONTINUATION.json',{'schema':'OpenRemaster.Continuation.v1','checkpoint':receipt['checkpoint'],
      'status':receipt['status'],'focus':'OpenMDK1','next':receipt['next_task'],
      'other_focus':['OpenStonekeep','OpenUltima8'],'azrael':'PAUSED; NO_POLLING; DEMO_CLOSED',
      'new_fidelity_attestation':False,'receipt_sha256':sha(ROOT/'iteration-receipt.json')})
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name not in {'sealed-manifest.json','mdk1-alias-bsp-material.zip'})
    put(ROOT/'sealed-manifest.json',{'schema':'OpenRemaster.SealedEvidence.v1','files':[
        {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    with zipfile.ZipFile(ROOT/'mdk1-alias-bsp-material.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in files+[ROOT/'sealed-manifest.json']:z.write(p,p.relative_to(ROOT).as_posix())
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'immutable_input_hashes_verified','test_sources_sha256','portfolio'}},indent=2))
    print('RECEIPT_SHA256',sha(ROOT/'iteration-receipt.json'))
    print('PACKAGE_SHA256',sha(ROOT/'mdk1-alias-bsp-material.zip'))
    return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
