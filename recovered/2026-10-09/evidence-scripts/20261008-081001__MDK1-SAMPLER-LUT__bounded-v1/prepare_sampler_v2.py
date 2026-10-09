"""Preserve v1 counterexample; correct the independently modeled destination order.
The original routine selects reversed writes when its X endpoints are reversed;
source-coordinate increments are unchanged. No source or production patch.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
p=ROOT/'verify_sampler.py';s=p.read_text(encoding='utf-8')
s=s.replace('def model(kernel,texture,width,height,n,u0=0,v0=0,du=65536,dv=0):',
            'def model(kernel,texture,width,height,n,u0=0,v0=0,du=65536,dv=0,reverse=False):')
s=s.replace('writes=[8+i for i,s in enumerate(samples) if not key or s!=0]',
            'writes=[8+(n-1-i if reverse else i) for i,s in enumerate(samples) if not key or s!=0]')
s=s.replace("    return {'reads':reads,'pixels':pixels,'write_offsets':writes}",
            "    if reverse:pixels.reverse()\n    return {'reads':reads,'pixels':pixels,'write_offsets':writes}")
s=s.replace('                expected=model(kernel,texture,width,height,n,u0,v0,du,dv)\n','')
s=s.replace('                for reverse in (False,True):\n',
            '                for reverse in (False,True):\n                    expected=model(kernel,texture,width,height,n,u0,v0,du,dv,reverse)\n')
s=s.replace("'sampler-model-failure.json'","'sampler-model-failure-v2.json'")
s=s.replace("'affine-sampler-verification.json'","'affine-sampler-verification-v2.json'")
s=s.replace("'schema':'OpenMDK1.AffineSamplerKernelVerification.v1'","'schema':'OpenMDK1.AffineSamplerKernelVerification.v2'")
with (ROOT/'verify_sampler_v2.py').open('x',encoding='utf-8') as f:f.write(s)
with (ROOT/'sampler-v1-supersession.json').open('x',encoding='utf-8') as f:
    json.dump({'prior_status':'FAIL','prior_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'prior_failure_sha256':hashlib.sha256((ROOT/'sampler-model-failure.json').read_bytes()).hexdigest(),
        'counterexample':'B0, two pixels, reversed endpoints: byte content matches but write sequence is [9,8], not [8,9].',
        'evidence':'Anchored original reverse branch at 0x46f0f0 and 0x470007; independent 4-pixel observation.',
        'correction':'Reverse destination placement/write order, not the source sample increment.',
        'validation_not_weakened':'Still require exact source-read sequence, byte values, and destination-write sequence.'},f,indent=2)
print('Prepared v2; original failure retained.')
