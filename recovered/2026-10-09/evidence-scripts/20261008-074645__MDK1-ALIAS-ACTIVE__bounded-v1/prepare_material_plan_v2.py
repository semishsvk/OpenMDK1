"""Retain the failed v1 guard; model the original loader's valid empty provider."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
p=ROOT/'verify_material_plan.py';s=p.read_text(encoding='utf-8')
old="if not 1<=n<=1024 or len(blob)>4*1024*1024:raise ValueError('DESCRIPTOR_SOURCE_BUDGET')"
new="if not 0<=n<=1024 or len(blob)>4*1024*1024:raise ValueError('DESCRIPTOR_SOURCE_BUDGET')"
assert s.count(old)==1;s=s.replace(old,new)
old="if not state['returned'] or r32(u,COUNT_PTR)!=n or r32(u,ARRAY_PTR)!=DESCS:raise ValueError('LOADER_OUTPUT_INCOMPLETE')"
new="if not state['returned'] or r32(u,COUNT_PTR)!=n or r32(u,ARRAY_PTR)!=(DESCS if n else 0):raise ValueError('LOADER_OUTPUT_INCOMPLETE')"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'material-plan-verification.json'","'material-plan-verification-v2.json'")
s=s.replace("'schema':'OpenMDK1.MaterialPlanVerification.v1'","'schema':'OpenMDK1.MaterialPlanVerification.v2'")
with (ROOT/'verify_material_plan_v2.py').open('x',encoding='utf-8') as f:f.write(s)
with (ROOT/'material-plan-v1-failure.json').open('x',encoding='utf-8') as f:
    json.dump({'status':'FAIL','reason':'DESCRIPTOR_SOURCE_BUDGET','source_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'diagnosis':'HMO_7 has zero local material records, a valid empty provider. The test guard incorrectly required n>=1.',
        'observed':{'hmo':'HMO_7','material_count':0,'bounded_blob_bytes':52760},
        'correction':'Allow count 0 and require both original output pointers/count to be zero; retain the same maximum memory and instruction budgets.',
        'production_changes':False},f,indent=2)
print('v2 prepared; empty provider is checked against the original zero-count branch.')
