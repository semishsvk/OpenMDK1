"""Original depth-extrema and affine/perspective decision against a numeric model.
Only the routing blocks execute; no triangle rasterizer, native game or host API.
Source descriptor floats are preserved and given names limited to this consumer.
"""
from datetime import datetime,timezone
from collections import Counter
from fractions import Fraction
import itertools,json,math,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from static_probe import ROOT,PIN,sha
from verify_f3_contract import machine,w32,r32,STACK
DESC,V0,V1,V2=0x10010000,0x10020000,0x10020100,0x10020200

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def model(zs,threshold,weight,numerator,denominator,force):
    lo,hi=min(zs),max(zs)
    if hi>64*lo:return 'DEPTH_RATIO_GUARD'
    if force or lo<=threshold:return 'PERSPECTIVE'
    delta=f32(hi-lo)
    bound=f32(Fraction.from_float(numerator)*Fraction.from_float(lo)/Fraction.from_float(denominator))
    error=f32(delta*weight)
    return 'AFFINE' if bound>error else 'PERSPECTIVE'

def original(zs,threshold,weight,numerator,denominator,force):
    params=tuple(map(f32,zs))+tuple(map(f32,(threshold,weight,numerator,denominator)))
    if any(not math.isfinite(v) for v in params) or any(z<=0 for z in params[:3]) or denominator<=0 or numerator<=0:
        raise ValueError('ROUTING_FIXTURE_DOMAIN')
    zs=params[:3];threshold,weight,numerator,denominator=params[3:]
    uc=machine();uc.reg_write(UC_X86_REG_FPCW,0x37f)
    for ptr,z in zip((V0,V1,V2),zs):uc.mem_write(ptr+8,struct.pack('<f',z))
    uc.mem_write(DESC+28,struct.pack('<2f',threshold,weight))
    for addr,value in [(STACK-124,DESC),(STACK-116,V1),(STACK-112,V2),(0x541482,force)]:w32(uc,addr,value)
    uc.mem_write(0x540b58,struct.pack('<f',numerator));uc.mem_write(0x540b64,struct.pack('<f',denominator))
    uc.reg_write(UC_X86_REG_EBP,STACK);uc.reg_write(UC_X86_REG_EDX,V0)
    result={'branch':None,'instructions':0,'depth_extrema':None}
    ends={0x46dd1c:'PERSPECTIVE',0x46e182:'AFFINE',0x46dc79:'DEPTH_RATIO_GUARD'}
    def code(u,addr,size,_):
        result['instructions']+=1
        if addr==0x46dc58:
            result['depth_extrema']=[struct.unpack('<f',u.mem_read(STACK-128,4))[0],struct.unpack('<f',u.mem_read(STACK-120,4))[0]]
        if addr in ends:result['branch']=ends[addr];u.emu_stop();return
        if not any(a<=addr and addr+size<=b for a,b in [(0x46dc19,0x46dc79),(0x46e0ed,0x46e182)]):
            raise ValueError('ROUTING_CODE_ESCAPE:'+hex(addr))
    def write(u,access,addr,size,value,_):
        if not STACK-192<=addr or addr+size>STACK-116:raise ValueError('ROUTING_WRITE_ESCAPE:'+hex(addr))
    uc.hook_add(UC_HOOK_CODE,code);uc.hook_add(UC_HOOK_MEM_WRITE,write)
    uc.emu_start(0x46dc19,0x100ff000,timeout=200000,count=400)
    if result['branch'] is None or result['depth_extrema']!=[min(zs),max(zs)]:raise ValueError('ROUTER_INCOMPLETE_OR_EXTREMA_MISMATCH')
    expected=model(zs,threshold,weight,numerator,denominator,force)
    if result['branch']!=expected:raise ValueError('ORIGINAL_ROUTER_MODEL_DIFFERENCE')
    return result

def main():
    p=ROOT/'baseline-material-sourceir.json';raw=p.read_bytes()
    if sha(raw)!='b597a9f27d5e03b34117d02d893a6e8b456406c8d413a2dd73276e96db32e783':raise ValueError('BASELINE_SOURCEIR_CHANGED')
    ir=json.loads(raw);refcounts=Counter((r['material_provider'],r['material_ordinal']) for r in ir['records'] if r['kind']=='TEXTURE_REFERENCE')
    groups={};profiles=[]
    for values in ir['materials'].values():
        for m in values:
            key=(m['provider'],m['ordinal'])
            if key not in refcounts:continue
            threshold,weight=struct.unpack('<2f',bytes.fromhex(m['uv_parameter_raw_hex']))
            pair=(threshold,weight);groups.setdefault(pair,{'materials':0,'references':0})
            groups[pair]['materials']+=1;groups[pair]['references']+=refcounts[key]
            profiles.append({'provider':key[0],'ordinal':key[1],'material':m['name'],'references':refcounts[key],
                'affine_minimum_depth_exclusive':threshold,'affine_depth_difference_weight':weight,
                'raw_parameter_bytes':m['uv_parameter_raw_hex']})
    checks=[];counts=Counter()
    depth_sets=[(1.,1.,1.),(10.,11.,10.5),(10.,20.,15.),(10.,640.,300.),
                (10.,641.,300.),(20000.,20000.,20000.),(20001.,20001.,20001.),(20001.,22000.,21000.)]
    for (threshold,weight),group in sorted(groups.items()):
        for zs in depth_sets:
            # Distinct permutations only: identical depths are not duplicate tests.
            for perm in sorted(set(itertools.permutations(zs))):
                for num,den in [(1.,1.),(.5,1.),(1.,4.)]:
                    for force in (0,1):
                        got=original(perm,threshold,weight,num,den,force);counts[got['branch']]+=1
                        checks.append({'test':'source_profile_routing','threshold':threshold,'weight':weight,'depths':perm,
                          'scale':(num,den),'force':force,'branch':got['branch'],'pass':True,'instructions':got['instructions']})
    # Exact equalities must not accidentally become <= affine decisions.
    boundary=[((8.,12.,10.),0.,2.,1.,1.,0,'PERSPECTIVE'),
              ((8.,12.,10.),0.,2.,1.25,1.,0,'AFFINE'),
              ((8.,12.,10.),8.,2.,2.,1.,0,'PERSPECTIVE'),
              ((8.,12.,10.),7.,2.,2.,1.,0,'AFFINE'),
              ((8.,512.,100.),0.,0.,1.,1.,0,'AFFINE'),
              ((8.,513.,100.),0.,0.,1.,1.,0,'DEPTH_RATIO_GUARD')]
    for zs,t,w,n,d,force,expected in boundary:
        got=original(zs,t,w,n,d,force)
        if got['branch']!=expected:raise ValueError('STRICT_THRESHOLD_BOUNDARY_FAILED')
        checks.append({'test':'strict_boundary','depths':zs,'threshold':t,'weight':w,'scale':(n,d),'expected':expected,'pass':True})
    report={'schema':'OpenMDK1.ProjectionRoutingContract.v1','status':'PASS','tests':len(checks),'checks':checks,
        'source_exe_sha256':PIN,'source_material_ir_sha256':sha(raw),'source_profiles':profiles,
        'distinct_source_threshold_pairs':[{'minimum_depth_exclusive':t,'depth_difference_weight':w,**g} for (t,w),g in sorted(groups.items())],
        'branch_case_counts':dict(counts),'rule_order':[
          'Use original camera-space depth extrema from all three vertices.',
          'max_depth > 64*min_depth enters the separate depth-ratio guard; that guard body is not run by this test.',
          'A nonzero force-perspective state selects perspective.',
          'min_depth <= descriptor.float_at_0x1c selects perspective.',
          'Otherwise compare float32((global_0x540b58/global_0x540b64)*min_depth) with float32(float32(max_depth-min_depth)*descriptor.float_at_0x20).',
          'Only a strictly greater left side selects affine. Equality selects perspective.'],
        'descriptor_field_clarification':'The earlier raw field name uv_parameter_raw_hex is preserved for compatibility; this consumer proves the two floats are affine eligibility threshold/weight, not direct texture-coordinate scale.',
        'numeric_profile':'Explicit FPCW 0x037f; positive finite fixture depths and denominator.',
        'actual_runtime_depth_projection_state':'NOT_OBSERVED','game_runtime_executed':False,
        'production_renderer_modified':False,'fidelity_verified':False,
        'limits':['Branch selection only: perspective interpolation, coverage and clipping are not validated here.',
          'Camera scale globals, per-frame forcing and real FPU profile need capture-bound provenance.',
          'No production or corpus fields were relabelled or modified.'],
        'created_at_utc':datetime.now(timezone.utc).isoformat()}
    out=ROOT/'projection-routing-verification.json'
    with out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k not in ['checks','source_profiles']},indent=2));print('SHA256',sha(out.read_bytes()))
if __name__=='__main__':main()
