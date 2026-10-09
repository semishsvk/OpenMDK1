"""Repeat the three new mechanisms from two independent clean source copies.
All copied inputs are fingerprinted; only new evidence paths are written. No
production runtime, game worktree, source corpus or live lease changes occur.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent
CP=Path(r'F:\Remaster Framework\orchestrator\control-plane')
PINS={
 'variant-selection-verification.json':'cd5b37467fc1c3ea73f7a88ca246d6caf1012af4d401942cae88264bd33d74c1',
 'uv-rounding-verification.json':'91179d8eb69f8b6476a6bbe037e327749ab070072b769eb6c51001934b22751e',
 'projection-routing-verification.json':'c2d057cf8a03b58e3a656cefed6c5dcb71184e770cc65a955dbb08ebbf239edd'}
TASKS=[('verify_variant_selection.py','variant-selection-verification.json',160),
       ('verify_uv_rounding.py','uv-rounding-verification.json',677),
       ('verify_projection_routing.py','projection-routing-verification.json',402)]
CODE=['static_probe.py','verify_f3_contract.py','verify_variant_selection.py','verify_uv_rounding.py','verify_projection_routing.py']
BASELINES=['baseline-material-sourceir.json','indexed-pixel-contract-sourceir.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def semantic(value):return {k:v for k,v in value.items() if k!='created_at_utc'}
def put(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,sort_keys=True)

def main():
    contract=load(ROOT/'job-contract.json');immutable=contract['source_and_control_hashes']
    if any(sha(Path(p))!=h for p,h in immutable.items()):raise RuntimeError('PINNED_INPUT_DRIFT')
    for name,h in PINS.items():
        if sha(ROOT/name)!=h or load(ROOT/name)['status']!='PASS':raise RuntimeError('UNSEALED_PASS_RESULT')
    fingerprints={name:sha(ROOT/name) for name in CODE+BASELINES}
    for name in CODE:ast.parse((ROOT/name).read_text(encoding='utf-8'),filename=name)
    repetitions=[]
    for label in ['restore-a','restore-b']:
        dst=ROOT/label;dst.mkdir(exist_ok=False)
        for name,h in fingerprints.items():
            with (dst/name).open('xb') as f:f.write((ROOT/name).read_bytes())
            if sha(dst/name)!=h:raise RuntimeError('RESTORE_FINGERPRINT_MISMATCH')
        cases=[]
        for script,report,n in TASKS:
            proc=subprocess.run([sys.executable,'-B',str(dst/script)],cwd=dst,capture_output=True,text=True,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),timeout=40)
            with (dst/(script+'.log')).open('x',encoding='utf-8') as f:f.write(proc.stdout+'\n'+proc.stderr)
            result=load(dst/report) if (dst/report).is_file() else {}
            same=semantic(result)==semantic(load(ROOT/report))
            good=proc.returncode==0 and result.get('status')=='PASS' and result.get('tests')==n and same
            cases.append({'script':script,'status':'PASS' if good else 'FAIL','exit_code':proc.returncode,
                'tests':result.get('tests'),'semantic_report_identical':same,
                'report_sha256':sha(dst/report) if (dst/report).is_file() else None})
            if not good:break
        stable=all(sha(dst/name)==h for name,h in fingerprints.items())
        repetitions.append({'restore':label,'status':'PASS' if stable and len(cases)==3 and all(c['status']=='PASS' for c in cases) else 'FAIL',
            'cases':cases,'source_and_baseline_fingerprints_unchanged':stable})
        if repetitions[-1]['status']!='PASS':break
    stable=all(sha(Path(p))==h for p,h in immutable.items()) and all(sha(ROOT/n)==h for n,h in fingerprints.items())
    passed=stable and len(repetitions)==2 and all(r['status']=='PASS' for r in repetitions)
    variant,uv,projection=[load(ROOT/name) for name in PINS]
    profile={'schema':'OpenMDK1.RendererProfileSourceIR.v1','scope':'EVIDENCE_ONLY_NOT_INSTALLED',
        'source_executable_sha256':variant['source_exe_sha256'],
        'prior_indexed_pixel_contract_sha256':fingerprints['indexed-pixel-contract-sourceir.json'],
        'startup_variant_predicate':variant['startup_rule'],'command_overrides':variant['command_options'],
        'parser_semantics':variant['parser_semantics'],
        'conversion':{'uv_format':uv['uv_format'],'bias':uv['bias_float32'],'declared_test_profiles':uv['x87_profiles'],
           'rounding_distinction':uv['important_distinction']},
        'projection_rules':projection['rule_order'],'material_projection_parameters':projection['source_profiles'],
        'actual_runtime_profile':'UNKNOWN_NOT_CAPTURED',
        'required_at_original_capture':['executable_sha256','stored_cpu_word','ordered_command_tokens',
          'callback_table_bytes_and_sha256','x87_control_word','projection_scale_globals','force_perspective_state',
          'camera_and_dynamic_object_state','original_frame_and_replay_provenance'],
        'validation_inputs_sha256':PINS,'fidelity_verified':False}
    put(ROOT/'renderer-profile-sourceir.json',profile)
    receipt={'schema':'OpenMDK1.VariantUVIterationReceipt.v1','checkpoint':'MDK1-VARIANT-UV-20261008-004',
       'status':'PASS' if passed else 'FAIL','iterations_completed':3,'checks_per_complete_pass':1239,
       'complete_passes':3 if passed else 1,'clean_repetitions':repetitions,
       'semantic_equivalence_excludes_only':'created_at_utc',
       'iterations':[
          {'task':'Renderer variant selection','tests':160,'status':variant['status'],
           'result':'Original startup predicate and real case-insensitive encoded command parser match. Last -pprotx/-nopprotx override wins.'},
          {'task':'UV and screen numeric conversion','tests':677,'status':uv['status'],
           'result':'16.16 bias conversion and FISTP match exact-rational reference for four declared x87 rounding profiles; negative UV toward-zero is not equivalent to integer truncation after bias.'},
          {'task':'Affine/perspective routing','tests':402,'status':projection['status'],
           'result':'Depth extrema, ratio-64 gate, forced perspective and strict descriptor-dependent thresholds match original instructions.'}],
       'source_material_parameter_groups':projection['distinct_source_threshold_pairs'],
       'descriptor_semantics_correction':projection['descriptor_field_clarification'],
       'renderer_profile_sourceir_sha256':sha(ROOT/'renderer-profile-sourceir.json'),
       'prior_checkpoint':contract['prior_checkpoint'],'prior_receipt_sha256':contract['prior_receipt_sha256'],
       'source_and_control_hashes':immutable,'test_software_and_baseline_sha256':fingerprints,
       'initial_report_sha256':PINS,'inputs_unchanged':stable,
       'actual_original_runtime_profile_observed':False,
       'evidence_class':'SOURCE_DATAFLOW_AND_ALLOWLISTED_X86_MICROEMULATION',
       'game_runtime_executed':False,'native_game_jobs':0,'gpu_jobs':0,'new_game_builds':0,
       'live_game_frames':0,'production_renderer_modified':False,'fidelity_verified':False,
       'authoritative_corpora_written':False,'game_worktrees_written':False,'live_leases_modified':False,
       'production_control_plane_modified':False,'azrael_polled':False,'azrael':'RETAIL_PAUSED_DEMO_CLOSED',
       'limits':['Startup tests use supplied classifier result, not host CPUID or a launched original game.',
         'The original runtime FPU, command-line and callback-table snapshot remain unknown.',
         'Numeric tests declare PC=64-bit significand and four rounding modes; untested precision and double-rounding corners are not generalized.',
         'Projection routing ends before rasterization and perspective interpolation; ratio-guard body is not verified.',
         'A source branch predicate does not prove end-to-end original/reconstruction pixel fidelity.'],
       'next_task':'Validate perspective span/UV setup and depth-ratio guard against original instructions, then bind the proved profile to a capture-ready renderer without guessing live variant/FPU state.',
       'created_at_utc':datetime.now(timezone.utc).isoformat(),'portfolio':[]}
    portfolio=load(CP/'portfolio-lanes-20261008-v3.json')
    for entry in portfolio['entries']:
        state='NO_NEW_EXECUTION'
        if entry['id']=='OpenMDK1':state='VARIANT_UV_ROUTING_MECHANISMS_PASS' if passed else 'VALIDATION_FAILED'
        elif entry['id']=='OpenAzrael-Demo':state='CLOSED'
        elif entry['id']=='OpenAzrael-Retail':state='PAUSED_NOT_POLLED'
        receipt['portfolio'].append({'project':entry['id'],'lane':entry['lane'],'state':state})
    put(ROOT/'iteration-receipt.json',receipt)
    put(ROOT/'CONTINUATION.json',{'checkpoint':receipt['checkpoint'],'status':receipt['status'],
       'focus':'OpenMDK1','next':receipt['next_task'],'other_focus':['OpenStonekeep','OpenUltima8'],
       'azrael':'RETAIL_PAUSED_DEMO_CLOSED_NO_POLLING','receipt_sha256':sha(ROOT/'iteration-receipt.json'),
       'runtime_fidelity_verified':False})
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name not in ['sealed-manifest.json','mdk1-variant-uv-evidence.zip'])
    put(ROOT/'sealed-manifest.json',{'schema':'OpenRemaster.SealedEvidence.v1','files':[
       {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    with zipfile.ZipFile(ROOT/'mdk1-variant-uv-evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in files+[ROOT/'sealed-manifest.json']:z.write(p,p.relative_to(ROOT).as_posix())
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['source_and_control_hashes','test_software_and_baseline_sha256','portfolio']},indent=2))
    print('RECEIPT_SHA256',sha(ROOT/'iteration-receipt.json'))
    print('PACKAGE_SHA256',sha(ROOT/'mdk1-variant-uv-evidence.zip'))
    return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
