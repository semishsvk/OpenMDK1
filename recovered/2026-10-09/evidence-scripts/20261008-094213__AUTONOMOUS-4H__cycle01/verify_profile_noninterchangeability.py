"""Original default-vs-alternate perspective counterexamples and profile-pinned gate.
New relational tests, not a rerun of the complete already sealed pixel suites.
"""
from datetime import datetime,timezone
import json,struct,itertools
from verify_callback_identity import run as select_original
from verify_default_short_pixels import run as default_original
from verify_short_perspective_pixels import run as alternate_original
from static_probe import ROOT,PIN,sha

def authorize(request,artifact):
 actual=select_original(0,request['flags'],request['alternate'])['target']
 if artifact['source_exe_sha256']!=PIN or artifact['profile']!='B' or artifact['function']!=actual or artifact['flags']!=request['flags']:
  raise ValueError('SOURCE_PROFILE_OR_FUNCTION_MISMATCH')
 if artifact['scope']!='ALIGNED_SHORT_SPAN_FLAGS0' or request['flags']!=0:raise ValueError('OUTSIDE_VERIFIED_SCOPE')
 return True

def main():
 examples=[];checks=[]
 for n,q,step in itertools.product((2,3,7,15,31),(1.,2.),(0.,1.,2.)):
  d=default_original(n,7,(q,8*q,30*q,0.,step*q,0.),0)
  a=alternate_original(n,7,(q,q,8*q,30*q,(8+n*step)*q,30*q),0)
  equal=d['pixel_sha256']==a['pixel_sha256']
  if step==0 and not equal:raise ValueError('SAME_CONSTANT_SAMPLE_DOMAIN_MISMATCH')
  examples.append({'n':n,'q':q,'ideal_endpoint_u':[8,8+n*step],'default_pixel_sha256':d['pixel_sha256'],'alternate_pixel_sha256':a['pixel_sha256'],
   'same_pixels':equal,'default_read_order_sha256':d['read_order_sha256'],'alternate_read_order_sha256':a['read_order_sha256']})
  checks.append({'test':f'original_pair_{n}_{q}_{step}','pass':True})
 witness=next(x for x in examples if x['n']==2 and x['q']==1. and x['ideal_endpoint_u']==[8,12.])
 dp=bytes([91,237,237]);ap=bytes([91,164,164])
 if witness['default_pixel_sha256']!=sha(dp) or witness['alternate_pixel_sha256']!=sha(ap):raise ValueError('MINIMAL_GOLDEN_COUNTEREXAMPLE')
 checks.append({'test':'minimal_distinct_pixels_at_same_ideal_endpoints','pass':True})
 for mode in (0,1):
  request={'flags':0,'alternate':mode};actual=select_original(0,0,mode)['target']
  artifact={'source_exe_sha256':PIN,'profile':'B','function':actual,'flags':0,'scope':'ALIGNED_SHORT_SPAN_FLAGS0'}
  if not authorize(request,artifact):raise ValueError('CORRECT_PROFILE_REJECTED')
  checks.append({'test':f'correct_profile_{mode}','pass':True})
  for field,value in [('function',select_original(0,0,1-mode)['target']),('profile','A'),('source_exe_sha256','0'*64),('flags',1),('scope','FULL_SCENE')]:
   bad=dict(artifact);bad[field]=value
   try:authorize(request,bad)
   except ValueError:checks.append({'test':f'reject_{mode}_{field}','pass':True})
   else:raise ValueError('WRONG_PROFILE_ACCEPTED')
 if not any(not e['same_pixels'] for e in examples) or not any(e['same_pixels'] for e in examples):raise ValueError('RELATIONAL_TEST_NOT_DISCRIMINATING')
 result={'schema':'OpenMDK1.ProfilePinnedPixelEvidence.v1','status':'PASS','tests':len(checks),'checks':checks,'original_pairs':examples,'source_exe_sha256':PIN,
  'function_identity':{'B_default_flags0':'0x471f82','B_alternate_flags0':'0x470f08'},
  'minimal_counterexample':{'q':1,'span_delta':2,'ideal_u_endpoints':[8,12],'v':30,'default_pixels':list(dp),'alternate_pixels':list(ap)},
  'inference':'Both original kernels can be internally validated yet disagree at identical ideal endpoints because their interval formulas differ. Some constant cases agree, so output equality alone cannot authorize a profile substitution.',
  'gate':'Pin EXE hash, profile, selected source function, flags and tested input scope before reusing a pixel contract.',
  'production_router_modified':False,'runtime_profile_observed':False,'game_runtime_executed':False,'fidelity_verified':False,
  'next':'Require actual original runtime/profile selection for scene integration; default and alternate contracts remain distinct.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'profile-noninterchangeability-verification.json'
 with p.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True)
 print(json.dumps({k:v for k,v in result.items() if k not in ('checks','original_pairs')},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
