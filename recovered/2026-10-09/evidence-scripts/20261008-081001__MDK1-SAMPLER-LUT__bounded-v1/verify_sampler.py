"""Validate eight original affine sampler kernels against an independent integer
state model. Includes actual byte-read order, keyed writes and endpoint behavior.
No claim about live variant choice, perspective setup or final game fidelity.
"""
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,struct
import unicorn
from sampler_probe import execute,KERNELS,U32
from static_probe import ROOT,sha

def model(kernel,texture,width,height,n,u0=0,v0=0,du=65536,dv=0):
    _,_,wrap,key,keeps_delta=KERNELS[kernel]
    offset=((u0>>16)&(width-1))+(((v0>>16)&(height-1))*width)
    uf=(u0<<16)&U32;vf=(v0<<16)&U32
    dx=(du<<16)&U32;dy=(dv<<16)&U32;delta=dx
    base=(du>>16)+(dv>>16)*width
    samples=[];reads=[]
    for _ in range(max(1,n-1)):
        vsum=vf+dy;vcarry=int(vsum>U32);vf=vsum&U32
        if wrap:offset&=width*height-1
        usum=uf+delta;ucarry=int(usum>U32);uf=usum&U32
        if not 0<=offset<len(texture):raise ValueError('MODEL_FIXTURE_ESCAPED_SOURCE')
        sample=texture[offset];reads.append(offset);samples.append(sample)
        if not keeps_delta:delta=(delta&~255)|sample
        offset=(offset+base+vcarry*width+ucarry)&U32
    if n>1:samples.append(samples[-1])
    writes=[8+i for i,s in enumerate(samples) if not key or s!=0]
    pixels=[s if not key or s!=0 else 0xa7 for s in samples]
    return {'reads':reads,'pixels':pixels,'write_offsets':writes}

def main():
    checks=[];variants=Counter();compared_pixels=0;compared_reads=0
    lengths=[1,2,3,4,31,32,33,257]
    increments=[(0,0),(65536,0),(-32768,16384),(81920,-32768),(16384,49152),(-98304,-32768)]
    for kernel in KERNELS:
        for n in lengths:
            for du,dv in increments:
                wrap=KERNELS[kernel][2]
                width,height=(8,8) if wrap else (32,1024)
                texture=bytes(0 if i%13==0 else (i*73+19)&255 for i in range(width*height))
                u0=(7<<16)+49152
                v0=((7 if wrap else 512)<<16)+16384
                expected=model(kernel,texture,width,height,n,u0,v0,du,dv)
                for reverse in (False,True):
                    got=execute(kernel,texture,width,height,n,u0,v0,du,dv,reverse)
                    case={'kernel':kernel,'n':n,'du':du,'dv':dv,'reverse':reverse}
                    equal=all(got[k]==expected[k] for k in ('pixels','reads','write_offsets'))
                    if not equal:
                        with (ROOT/'sampler-model-failure.json').open('x',encoding='utf-8') as f:
                            json.dump({'status':'FAIL','case':case,'expected':expected,'observed':got},f,indent=2)
                        raise ValueError('SAMPLER_MODEL_DIFFERENCE:'+str(case))
                    checks.append(dict(case,pass_test=True,read_sequence_sha256=sha(struct.pack('<'+'I'*len(got['reads']),*got['reads'])),pixel_sha256=sha(bytes(got['pixels']))))
                    variants[kernel]+=1;compared_pixels+=len(got['pixels']);compared_reads+=len(got['reads'])
    texture=bytes([255,50]+[13]*62)
    a=execute('A2',texture,8,8,600,65535,0,0,0)
    b=execute('B2',texture,8,8,600,65535,0,0,0)
    for k,got in [('A2',a),('B2',b)]:
        expected=model(k,texture,8,8,600,65535,0,0,0)
        if any(got[f]!=expected[f] for f in ('pixels','reads','write_offsets')):raise ValueError('VARIANT_MODEL_DISAGREEMENT')
    first=next((i for i,(x,y) in enumerate(zip(a['pixels'],b['pixels'])) if x!=y),None)
    if first is None:raise ValueError('EXPECTED_VARIANT_COUNTEREXAMPLE_ABSENT')
    checks.append({'case':'variantA_vs_B_low_byte_carry_counterexample','pass_test':True,'first_different_pixel':first})
    report={'schema':'OpenMDK1.AffineSamplerKernelVerification.v1','status':'PASS','tests':len(checks),'checks':checks,
        'kernel_counts':dict(variants),'pixel_comparisons':compared_pixels,'texture_read_comparisons':compared_reads,
        'rules':{'flags_bit0':'zero texel skips destination write in keyed kernels; opaque kernels write zero',
            'flags_bit1':'mask linear address by combined descriptor width/height masks in wrapped kernels; other kernels have no per-sample mask',
            'endpoint':'tested inclusive scanline widths read max(1,width-1) texels and repeat the cached final texel at the final pixel',
            'fixed_point':'separate unsigned 32-bit fractional accumulators with integer address steps and carry',
            'variantA':'retains original U fractional step in scratch memory',
            'variantB':'texel in DL changes low byte of EDX used for subsequent U fractional additions'},
        'variant_counterexample':{'n':600,'u0_16_16':65535,'du_16_16':0,'dv_16_16':0,
            'first_different_pixel':first,'A_pixel':a['pixels'][first],'B_pixel':b['pixels'][first],
            'A_pixel_hash':sha(bytes(a['pixels'])),'B_pixel_hash':sha(bytes(b['pixels'])),
            'interpretation':'Variant-specific numeric behavior on a valid synthetic sampler state; no assertion which table the live game selects.'},
        'no_host_game_execution':True,'unicorn_version':unicorn.__version__,
        'scope':'ORIGINAL_AFFINE_INSTRUCTIONS_TO_PIXEL_BYTES_IN_SYNTHETIC_SINGLE_SCANLINES',
        'limits':['No triangle edge generation or perspective scanline interpolation tested by this suite.',
          'Live CPU/renderer variant selection is unverified.',
          'Power-of-two synthetic texture planes; actual material flag compatibility is a separate source audit.',
          'Byte-identical to the tested original kernels does not constitute final scene fidelity.'],
        'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'affine-sampler-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
    print('REPORT_SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
