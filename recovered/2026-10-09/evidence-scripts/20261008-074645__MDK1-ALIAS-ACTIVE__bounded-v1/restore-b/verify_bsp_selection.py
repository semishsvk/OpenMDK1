"""Iteration 2: source BSP traversal range ordering against original instructions.
No rasterization, game process, injected live state or filesystem access inside
emulation. Dynamic object links must be zero in every tested source plane.
"""
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,struct,sys
import unicorn
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STOP,STACK
from geometry_contract import corpus,initialized_flags,potential_selected
from static_probe import ROOT,sha
BSP,CAM=0x10030000,0x10008000
CAMERAS=[(0.,0.,0.),(800.,1800.,160.),(-500.,2600.,-600.),(129.25,2300.5,-700.75)]

def model(part,camera,mode):
    out=[]
    def visit(index):
        if index<0:return
        p=part['planes'][index];x,y,z,d=p['coeff'];cx,cy,cz=camera
        distance=struct.unpack('<f',struct.pack('<f',(y*cy+x*cx)+z*cz+d))[0]
        positive=distance>0
        a,b=p['children']
        selected=p['ranges'][0 if positive else 1]
        near,far=(a,b) if positive==bool(mode) else (b,a)
        # For mode 0 positive: B -> front range -> A; nonpositive: A -> back -> B.
        visit(near);out.append((index,selected[1],selected[0]));visit(far)
    visit(0)
    return out

def original(part,camera,mode):
    if len(part['planes'])>2048:raise ValueError('EMULATION_PLANE_BUDGET')
    if any(any(p['object_links']) for p in part['planes']):raise ValueError('DYNAMIC_LINKS_REQUIRE_SEPARATE_PROBE')
    u=machine();u.mem_write(BSP,part['plane_bytes']);u.mem_write(CAM,struct.pack('<3f',*camera))
    w32(u,0x4a2460,BSP);w32(u,0x4a2468,CAM);w32(u,0x499f8c,mode);w32(u,STACK,STOP)
    u.reg_write(UC_X86_REG_EAX,BSP);u.reg_write(UC_X86_REG_ESP,STACK)
    state={'returned':False,'instructions':0};out=[]
    def hook(uc,addr,size,_):
        state['instructions']+=1
        if addr==STOP:state['returned']=True;uc.emu_stop();return
        if addr==0x409860:
            index=(uc.reg_read(UC_X86_REG_ECX)-BSP)//44
            if uc.reg_read(UC_X86_REG_ECX)!=BSP+index*44 or not 0<=index<len(part['planes']):raise ValueError('BAD_NODE_IDENTITY')
            start=uc.reg_read(UC_X86_REG_EBX);start=start if start<2**31 else start-2**32
            count=uc.reg_read(UC_X86_REG_EDX)
            if count and (start<0 or start+count>len(part['triangles'])):raise ValueError('ORIGINAL_RANGE_BOUNDS')
            out.append((index,start,count))
            sp=uc.reg_read(UC_X86_REG_ESP);uc.reg_write(UC_X86_REG_EIP,r32(uc,sp));uc.reg_write(UC_X86_REG_ESP,sp+4)
            return
        if not 0x409a6c<=addr<0x409dc4:raise ValueError('UNEXPECTED_BSP_CODE:'+hex(addr))
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x409a6c,STOP+1,timeout=1500000,count=500000)
    if not state['returned']:raise ValueError('BSP_BUDGET_EXCEEDED')
    return out,state['instructions']

def selected_faces(part,ranges):
    return [j for _,start,count in ranges for j in range(start,start+count)
            if not initialized_flags(part['triangles'][j]['flag32']&255)&16]

def main():
    parts,primary=corpus();tests=[];summaries=[]
    aliasnames={x['name'] for x in primary if x['kind']==0xffffffff}
    for part in parts:
        nodes,_=potential_selected(part)
        for camera_id,camera in enumerate(CAMERAS):
            orders=[]
            for mode in (0,1):
                predicted=model(part,camera,mode);observed,steps=original(part,camera,mode)
                if predicted!=observed:raise ValueError('BSP_ORDER_MISMATCH:'+part['name']+':'+str((camera_id,mode)))
                if {i for i,_,_ in observed}!=nodes:raise ValueError('BSP_NODE_COVERAGE')
                faces=selected_faces(part,observed)
                if any(part['triangles'][j]['f3']>=0 and part['triangles'][j]['name'] in aliasnames for j in faces):raise ValueError('ALIAS_ENTERED_SELECTED_STREAM')
                orders.append(faces)
                tests.append({'case':part['name']+'-camera'+str(camera_id)+'-mode'+str(mode),'pass':True,
                    'range_count':len(observed),'face_count_before_clip':len(faces),'original_instructions':steps,
                    'range_stream_sha256':sha(json.dumps(observed,separators=(',',':')).encode()),
                    'face_stream_sha256':sha(struct.pack('<'+'I'*len(faces),*faces)),
                    'face_multiplicity_extra':len(faces)-len(set(faces))})
            if Counter(orders[0])!=Counter(orders[1]):raise ValueError('SORT_MODE_CHANGED_SELECTION_MULTISET')
        summaries.append({'hmo':part['name'],'plane_count':len(part['planes']),'source_reachable_nodes':len(nodes),
            'tested_camera_states':len(CAMERAS),'sort_modes':2,'range_streams_match':True})
    # Exact-plane boundary checks are synthetic; same strict comparison rule must hold.
    fake={'name':'axis-fixture','planes':[{'coeff':(1.,0.,0.,0.),'children':(-1,-1),'ranges':[(1,0),(1,1)],'object_links':(0,0)}],
        'plane_bytes':struct.pack('<4f2hHhHh4I',1.,0.,0.,0.,-1,-1,1,0,1,1,0,0,0,0),
        'triangles':[{'flag32':0,'f3':0,'name':'TEST'},{'flag32':0,'f3':1,'name':'TEST2'}]}
    for x in (-1.,-0.,0.,1.):
        for mode in (0,1):
            observed,_=original(fake,(x,0.,0.),mode);predicted=model(fake,(x,0.,0.),mode)
            if observed!=predicted or observed[0][1]!=(0 if x>0 else 1):raise ValueError('PLANE_EQUALITY_BRANCH')
            tests.append({'case':'exact-plane-'+repr(x)+'-mode'+str(mode),'pass':True})
    report={'schema':'OpenMDK1.BSPRangeSelection.v1','status':'PASS','tests':len(tests),'passed':len(tests),
       'cases':tests,'parts':summaries,'camera_states':CAMERAS,
       'rules':{'rangeA':'plane+0x14: u16 count then i16 start','rangeB':'plane+0x18: u16 count then i16 start',
          'children':'i16 node indices at +0x10 and +0x12, negative = no child',
          'side':'float32-stored plane dot camera + d > 0 chooses A, zero/negative chooses B',
          'order_mode0':'positive: childB,A-range,childA; otherwise childA,B-range,childB',
          'order_mode1':'positive: childA,A-range,childB; otherwise childB,B-range,childA'},
       'scope':'SOURCE_BSP_RANGE_SELECTION_WITH_ORIGINAL_INSTRUCTION_COMPARISON',
       'raster_body_executed':False,'full_game_runtime_executed':False,'live_runtime_state_verified':False,
       'stub':'Only range-submit function 0x409860 is observed and returned from; no effect/actor callbacks occur because all checked source object links are zero.',
       'unicorn_version':unicorn.__version__,
       'limits':['These camera coordinates are controlled fixture inputs, not captured live cameras.',
          'Selected face stream is before clipping, rasterization and pixel occlusion.',
          'Dynamic per-frame node links and flag changes require separate runtime evidence.'],
       'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'bsp-selection-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({'status':'PASS','tests':len(tests),'parts':len(parts),'source_nodes':sum(len(p['planes']) for p in parts),'sha256':sha(p.read_bytes())},indent=2))
if __name__=='__main__':main()
