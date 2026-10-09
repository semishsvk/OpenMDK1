"""Repeat three independently validated pixel mechanisms in two clean copies.
No native game process or renderer is started. Only this run's evidence is written.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent
CP=Path(r'F:\Remaster Framework\orchestrator\control-plane')
PINS={
 'lut-mechanism-verification.json':'e956fd50cfef1a705c1e897126e79beabf6530ef1986a2a5da4717d80225c417',
 'affine-sampler-verification-v2.json':'aa9d08a22905a18bd9e9f0cc0c7f3c89d50a41f1feafd61497489ee9923a05c3',
 'sampling-material-contract.json':'6b206d394076c1ff0dae8f0e85b1aceec8ad87f45b368297fbcdc94a9ea15081'}
TASKS=[('verify_lut.py','lut-mechanism-verification.json',860),
       ('verify_sampler_v2.py','affine-sampler-verification-v2.json',769),
       ('verify_sampling_contract.py','sampling-material-contract.json',720)]
SOURCES=['static_probe.py','verify_f3_contract.py','geometry_contract.py','verify_material_plan_v2.py',
         'sampler_probe.py','verify_lut.py','verify_sampler_v2.py','verify_sampling_contract.py']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def semantic(x):return {k:v for k,v in x.items() if k!='created_at_utc'}
def put(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,sort_keys=True)
def main():
    contract=load(ROOT/'job-contract.json');immutable=contract['source_and_control_hashes']
    if any(sha(Path(p))!=h for p,h in immutable.items()):raise RuntimeError('INITIAL_INPUT_DRIFT')
    for p,h in PINS.items():
        if sha(ROOT/p)!=h or load(ROOT/p)['status']!='PASS':raise RuntimeError('UNSEALED_INITIAL_RESULTS')
    baseline=ROOT/'baseline-material-sourceir.json'
    if sha(baseline)!=contract['baseline_sourceir_sha256']:raise RuntimeError('BASELINE_IR_CHANGED')
    hashes={name:sha(ROOT/name) for name in SOURCES}
    for name in SOURCES:ast.parse((ROOT/name).read_text(encoding='utf-8'),filename=name)
    restored=[]
    for label in ('restore-a','restore-b'):
        path=ROOT/label;path.mkdir(exist_ok=False)
        for name in SOURCES+['baseline-material-sourceir.json']:
            with (path/name).open('xb') as f:f.write((ROOT/name).read_bytes())
            if sha(path/name)!=sha(ROOT/name):raise RuntimeError('CLEAN_RESTORE_HASH_DIFFERENCE')
        cases=[]
        for script,report,ntests in TASKS:
            p=subprocess.run([sys.executable,'-B',str(path/script)],cwd=path,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=40)
            with (path/(script+'.log')).open('x',encoding='utf-8') as f:f.write(p.stdout+'\n'+p.stderr)
            got=load(path/report) if (path/report).exists() else {}
            identical=semantic(got)==semantic(load(ROOT/report))
            passed=p.returncode==0 and got.get('status')=='PASS' and got.get('tests')==ntests and identical
            cases.append({'script':script,'exit_code':p.returncode,'tests':got.get('tests'),
               'status':'PASS' if passed else 'FAIL','semantic_report_identical':identical,
               'report_sha256':sha(path/report) if (path/report).is_file() else None})
            if not passed:break
        stable=all(sha(path/n)==h for n,h in hashes.items()) and sha(path/baseline.name)==sha(baseline)
        restored.append({'restore':label,'status':'PASS' if stable and len(cases)==3 and all(c['status']=='PASS' for c in cases) else 'FAIL',
            'cases':cases,'software_and_baseline_unchanged':stable})
        if restored[-1]['status']!='PASS':break
    stable=all(sha(Path(p))==h for p,h in immutable.items()) and all(sha(ROOT/n)==h for n,h in hashes.items())
    passed=stable and len(restored)==2 and all(r['status']=='PASS' for r in restored)
    lut,sampler,binding=[load(ROOT/n) for n in PINS]
    evidence_ir={'schema':'OpenMDK1.IndexedPixelContractSourceIR.v1','scope':'VALIDATED_MECHANISMS_NOT_PRODUCTION_RENDERER',
       'baseline_material_sourceir_sha256':sha(baseline),'source_exe_sha256':lut['source_exe_sha256'],
       'lut':lut['rules'],'affine_sampler':sampler['rules'],
       'initial_address':binding['address_rule'],'material_profiles':binding['profiles'],
       'callback_tables':binding['callback_tables'],
       'variant_selection':'REQUIRED_EXPLICIT_INPUT; NO_DEFAULT_VARIANT_IS_VERIFIED',
       'validation_receipt_hashes':PINS,
       'production_requirements':['Source-backed live renderer-table variant selection.',
          'UV conversion, perspective interpolation and FPU rounding evidence.',
          'Actual LUT palette tree/tint/weight state tied to a capture point.',
          'Payload address-domain checks for non-power-of-two heights.',
          'Canonical native admission and original-runtime visual comparison.'],
       'fidelity_verified':False,'source_payloads_or_executables_embedded':False}
    put(ROOT/'indexed-pixel-contract-sourceir.json',evidence_ir)
    report={'schema':'OpenMDK1.SamplerLUTIterationReceipt.v1','checkpoint':'MDK1-SAMPLER-LUT-20261008-003',
       'status':'PASS' if passed else 'FAIL','iterations_completed':3,
       'checks_per_complete_pass':2349,'complete_passes':3 if passed else 1,
       'restores':restored,'semantic_equivalence_excludes_only':'created_at_utc',
       'iterations':[
          {'task':'LUT destination remap, generator and palette tree lookup','tests':860,'status':lut['status'],
           'result':'Exact index-space destination remap; RGB table generator divides by 256; original threshold/XOR lookup tested on synthetic trees.'},
          {'task':'Eight affine sampler kernels','tests':769,'status':sampler['status'],
           'result':'Exact pixel bytes, source reads, write order, keying, masks and endpoint behavior matched; A/B counterexample retained.'},
          {'task':'Source descriptor address setup and callback routing','tests':720,'status':binding['status'],
           'result':'67 used descriptors, 1656 source texture references; 1536 flag0 and 120 flag2 references; 50 non-power-of-two height descriptors retained.'}],
       'counts':{'active_materials':67,'texture_references':1656,'references_flags0':1536,'references_flags2':120,
           'nonpower_height_descriptors':50,'wrapped_descriptors':4,
           'affine_pixel_comparisons_per_sampler_run':sampler['pixel_comparisons'],
           'affine_texel_read_comparisons_per_sampler_run':sampler['texture_read_comparisons']},
       'variant_counterexample':sampler['variant_counterexample'],
       'pixel_contract_sourceir_sha256':sha(ROOT/'indexed-pixel-contract-sourceir.json'),
       'baseline_sourceir_unchanged':sha(baseline)==contract['baseline_sourceir_sha256'],
       'evidence_class':'ORIGINAL_X86_MICROEMULATION_AND_SOURCE_MATERIAL_DATAFLOW',
       'new_native_game_jobs':0,'new_game_builds':0,'gpu_jobs':0,'live_game_frames_captured':0,
       'production_renderer_modified':False,'fidelity_verified':False,
       'authoritative_corpora_written':False,'game_worktrees_written':False,
       'production_control_plane_written':False,'live_leases_changed':False,
       'azrael_polled':False,'azrael_state':'RETAIL_PAUSED_DEMO_CLOSED',
       'source_and_control_hashes':immutable,'inputs_unchanged':stable,'software_sha256':hashes,
       'initial_results_sha256':PINS,'prior_checkpoint_receipt_sha256':contract['baseline_receipt_sha256'],
       'failed_experiment_retained':'sampler-model-failure.json + sampler-v1-supersession.json; wrong destination order assumption for reversed endpoints corrected in v2.',
       'limits':['All original instruction tests use synthetic memory and finite execution guards, not a full game.',
          'Triangle coverage, perspective interpolation and dynamic state are not closed by affine-span tests.',
          'The two real callback variants differ numerically in a boundary case; live variant selection remains unverified.',
          'Actual palette-tree/tint state is not supplied by the synthetic LUT fixtures.',
          'A combined address bitmask is not proof of an arbitrary safe UV range or conventional independent U/V repeat.'],
       'next_task':'Resolve source-backed renderer variant selection and the perspective/UV conversion path before integrating the indexed pixel contract.',
       'created_at_utc':datetime.now(timezone.utc).isoformat(),'portfolio':[]}
    portfolio=load(CP/'portfolio-lanes-20261008-v3.json')
    for e in portfolio['entries']:
        state='NO_NEW_EXECUTION'
        if e['id']=='OpenMDK1':state='THREE_PIXEL_MECHANISM_ITERATIONS_PASS' if passed else 'VALIDATION_FAILED'
        elif e['id']=='OpenAzrael-Retail':state='PAUSED_NOT_POLLED'
        elif e['id']=='OpenAzrael-Demo':state='CLOSED'
        report['portfolio'].append({'project':e['id'],'lane':e['lane'],'state':state})
    put(ROOT/'iteration-receipt.json',report)
    put(ROOT/'CONTINUATION.json',{'checkpoint':report['checkpoint'],'status':report['status'],
        'focus':'OpenMDK1','next':report['next_task'],'other_focus':['OpenStonekeep','OpenUltima8'],
        'azrael':'RETAIL_PAUSED_DEMO_CLOSED_NO_POLLING','receipt_sha256':sha(ROOT/'iteration-receipt.json'),
        'runtime_fidelity_verified':False})
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name not in {'sealed-manifest.json','mdk1-sampler-lut.zip'})
    put(ROOT/'sealed-manifest.json',{'schema':'OpenRemaster.SealedEvidence.v1','files':[
        {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    # Code, contracts and evidence only: no source EXE or raw retail texture payloads.
    with zipfile.ZipFile(ROOT/'mdk1-sampler-lut.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in files+[ROOT/'sealed-manifest.json']:z.write(p,p.relative_to(ROOT).as_posix())
    print(json.dumps({k:v for k,v in report.items() if k not in {'source_and_control_hashes','software_sha256','portfolio'}},indent=2))
    print('RECEIPT_SHA256',sha(ROOT/'iteration-receipt.json'))
    print('PACKAGE_SHA256',sha(ROOT/'mdk1-sampler-lut.zip'))
    return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
