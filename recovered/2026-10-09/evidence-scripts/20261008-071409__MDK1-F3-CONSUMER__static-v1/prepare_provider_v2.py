"""Retain failed assumption probe; bound HMO access by actual archive entries.
The original loader removes the first dword, but its numeric size convention is
not identical to a standalone MTI file. Do not generalize that unrelated field.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
old=ROOT/'validate_provider_precedence.py'
s=old.read_text(encoding='utf-8')
needle="        check(hn+'_prefix',u32(h,0)==len(h)-4)"
assert s.count(needle)==1
s=s.replace(needle,"        check(hn+'_bounded_size_word',0<u32(h,0)<=len(h))")
s=s.replace("'emulated_instructions':stats['instructions']", "'emulated_instructions':stats['instructions'],'container_entry_bytes':len(h),'leading_size_word':u32(h,0),'size_word_semantics':'NOT_GENERALIZED_FROM_STANDALONE_MTI'")
s=s.replace("'provider-precedence-verification.json'","'provider-precedence-verification-v2.json'")
s=s.replace("'schema':'OpenMDK1.F3ProviderPrecedence.v1'","'schema':'OpenMDK1.F3ProviderPrecedence.v2'")
with (ROOT/'validate_provider_precedence_v2.py').open('x',encoding='utf-8') as f:f.write(s)
with (ROOT/'provider-v1-failure.json').open('x',encoding='utf-8') as f:
    json.dump({'status':'FAIL','failed_test':'HMO_1_prefix','original_script_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
      'falsified_assumption':'Every MTO embedded HMO length dword equals archive entry byte span minus four, as for standalone MTI.',
      'observed_HMO_1':{'span':923580,'leading_dword':923579,'standalone_assumption_expected':923576},
      'correction':'Retain exact loader pointer +4; do not claim identical size-number convention. Bounds use source directory extents; size word must fit within span.',
      'not_a_runtime_fix':True},f,indent=2)
print('Prepared separate v2 probe; failed source-length assumption retained.')
