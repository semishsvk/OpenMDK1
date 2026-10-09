"""Resolve registry source precedence from original loader calls and LEVEL3.
Preserves the earlier conditional resolver test; this is the concrete provider
cross-check. It is still isolated instruction emulation, not live-game fidelity.
"""
import json,struct
from collections import Counter
from datetime import datetime,timezone
from static_probe import load,offset,ROOT,PIN,SOURCE,sha
from verify_f3_contract import MTO,MTI,MTO_PIN,original_resolver,resolver_model,LOCAL,SHARED,u32,name

def main():
    exe,sections=load();b=MTO.read_bytes();m=MTI.read_bytes()
    if sha(b)!=MTO_PIN:raise ValueError('MTO_PIN_MISMATCH')
    checks={}
    def check(k,v):
        checks[k]=bool(v)
        if not v:raise ValueError(k)
    # Matched instruction boundaries and direct-call operand bytes from observed source.
    anchors={
      0x433df2:'688c754900',0x433e16:'e8b566feff',
      0x41a502:'bb28b75400',0x41a507:'ba2cb75400',0x41a513:'e8c8fcffff',
      0x43255b:'e8e485feff',0x432560:'83c010',0x432563:'e8b882feff',
      0x41a826:'bb30b75400',0x41a82b:'ba34b75400',0x41a832:'e8a9f9ffff',
      0x41aa3b:'ba04000000',0x41aa4b:'e89f370600',0x41aaff:'89f3',0x41ab07:'e8e3360600',
      0x41ab47:'a144b75400',0x431368:'8b4020',0x43136d:'a324b75400',
      0x41a6da:'8b0d28b75400',0x41a70a:'8b0d30b75400',0x41a764:'83c30a',0x41a767:'8908',
      0x40c8be:'85db',0x40c8c0:'7c7d',0x40c8c7:'c1e302',0x40c8cc:'8b18',0x40c8d8:'837b2400',
      0x40c99a:'b800fcffff',0x40c99f:'29d8',0x40c9a7:'c1e008',0x40c9b0:'e8bb5f0000'
    }
    for va,h in anchors.items():
        data=bytes.fromhex(h);at=offset(sections,va,len(data))
        check('anchor_'+hex(va),exe[at:at+len(data)]==data)
    p=offset(sections,0x49758c,24);path_template=exe[p:p+24].split(b'\0',1)[0].decode('ascii')
    check('level_primary_path',path_template=='%s\\LEVEL%d\\LEVEL%dS.MTI')
    check('MTI_length_prefix',u32(m,0)==len(m)-4)
    n=u32(m,20)
    if n>1024 or 24+n*24>len(m):raise ValueError('MTI_BOUNDS')
    primary=[]
    for i in range(n):
        q=24+24*i
        primary.append({'name':name(m[q:q+8]),'ordinal':i,'serialized_flags':u32(m,q+8),
             'record_raw_offset':q,'relative_payload_or_alias':u32(m,q+20)})
    pn=[r['name'] for r in primary]
    totals=Counter();perhmo=[]
    count=u32(b,20)
    for i in range(count):
        q=24+i*12;hn=name(b[q:q+8]);start=u32(b,q+8);end=u32(b,q+20) if i+1<count else len(b);h=b[start:end]
        check(hn+'_prefix',u32(h,0)==len(h)-4)
        localcount=u32(h,36)
        secondary=[name(h[40+j*24:48+j*24]) for j in range(localcount)]
        g=u32(h,12)+4;nc=u32(h,g);names=[name(h[g+4+j*10:g+14+j*10]) for j in range(nc)]
        outputs,stats=original_resolver(names,pn,secondary)
        check(hn+'_original_resolver_matches_provider_order',outputs==resolver_model(names,pn,secondary))
        pcount_at=(g+4+nc*10+3)&~3;tcount_at=pcount_at+4+u32(h,pcount_at)*44;tn=u32(h,tcount_at);base=tcount_at+4
        c=Counter();aliases=Counter();sharedmaterials=Counter()
        for ti in range(tn):
            f3=struct.unpack_from('<h',h,base+36*ti+6)[0]
            if f3<0:c['negative_codes']+=1;continue
            if f3>=nc:raise ValueError('NONNEGATIVE_CODE_OUTSIDE_NAME_TABLE')
            chosen=outputs[f3];mn=names[f3]
            c['nonnegative_codes']+=1
            if chosen==0:c['unresolved_null']+=1
            elif LOCAL<=chosen<LOCAL+52*len(primary):
                r=primary[(chosen-LOCAL)//52];c['primary_LEVEL3S_MTI']+=1;sharedmaterials[mn]+=1
                if r['serialized_flags']==0xffffffff:c['primary_alias_or_nonpayload']+=1;aliases[mn]+=1
                else:c['primary_texture_descriptor']+=1
            elif SHARED<=chosen<SHARED+52*len(secondary):c['secondary_current_HMO_MAT']+=1
            else:raise ValueError('PROVIDER_OUTPUT_OUT_OF_BOUNDS')
        totals.update(c)
        perhmo.append({'hmo':hn,'counts':dict(c),'primary_material_names':dict(sharedmaterials),
            'alias_or_nonpayload_names':dict(aliases),'shadowed_MTO_names':[n for n in secondary if n in pn],
            'emulated_instructions':stats['instructions']})
    check('all_nonnegative_names_resolved',totals['nonnegative_codes']==1691 and totals['unresolved_null']==0)
    check('full_partition',totals['nonnegative_codes']+totals['negative_codes']==7205)
    check('unchanged_inputs',sha(SOURCE.read_bytes())==PIN and sha(MTO.read_bytes())==MTO_PIN and MTI.read_bytes()==m)
    report={'schema':'OpenMDK1.F3ProviderPrecedence.v1','status':'PASS','checks':checks,
      'source_exe_sha256':PIN,'source_mto_sha256':MTO_PIN,'source_mti_sha256':sha(m),
      'primary_provider':{'file_template':path_template,'table_global':'0x54b728','count_global':'0x54b72c'},
      'secondary_provider':{'source':'Current HMO block: length-prefix removed, plus 0x10 points to embedded MAT object.',
          'table_global':'0x54b730','count_global':'0x54b734'},
      'resolver_order':'Primary level MTI first, current HMO embedded MAT second; exact case-sensitive first match.',
      'earlier_fixture_scope':'f3-consumer-verification.json used synthetic primary=HMO,secondary=MTI only to test the generic name resolver. That fixture is NOT the concrete runtime provider order. This record establishes the provider order.',
      'counts':dict(totals),'per_hmo':perhmo,'checks_pass':len(checks),
      'remaining_semantics':['Primary alias/nonpayload descriptors need the exact final normalization consumer; name resolution alone is not pixel payload readiness.',
         'Visibility, record activation and degenerate geometry are separate from total record counts.',
         'Sampler/UV, LUT contents/blend/depth and original-runtime visual comparison remain unverified.'],
      'game_runtime_launched':False,'production_binding_installed':False,
      'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'provider-precedence-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({'status':'PASS','checks':len(checks),'counts':report['counts'],
        'per_hmo_primary':{r['hmo']:r['primary_material_names'] for r in perhmo if r['primary_material_names']},
        'shadowed_mto':{r['hmo']:r['shadowed_MTO_names'] for r in perhmo if r['shadowed_MTO_names']},
        'report_sha256':sha(p.read_bytes())},indent=2))
if __name__=='__main__':main()
