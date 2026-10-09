"""Iteration 1: original initialization and pre-raster face filtering.
The raster entry is observed and returned from without rendering. All memory is
synthetic, except immutable source bytes copied into the emulator.
"""
from collections import Counter
from datetime import datetime,timezone
import json,struct
import unicorn
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,REGS,STOP,STACK
from static_probe import ROOT,load,offset,sha
from geometry_contract import corpus,initialized_flags,potential_selected
OBJ,TRI,VERT=0x10040000,0x10050000,0x10010000

def run_filter(raw,count,initialize=True,start=0,length=None):
    if length is None:length=count-start
    if count>10000 or len(raw)!=36*count or start<0 or length<0 or start+length>count:raise ValueError('MICROTEST_BUDGET_OR_RANGE')
    u=machine();u.mem_write(TRI,raw);w32(u,OBJ+0x28,TRI);w32(u,OBJ+0x10,count)
    w32(u,0x4a2464,TRI);w32(u,0x4a2458,VERT)
    for addr in [0x5414b4,0x5414d4,0x499f74,OBJ+0x110,OBJ+0x10c]:w32(u,addr,0)
    phase={'which':'init','instructions':0,'returned':False};calls=[]
    def hook(uc,addr,size,_):
        phase['instructions']+=1
        if addr==STOP:phase['returned']=True;uc.emu_stop();return
        if phase['which']=='init':
            if not 0x40b4dc<=addr<0x40b582:raise ValueError('UNEXPECTED_INIT_ADDRESS:'+hex(addr))
        else:
            if addr==0x40ca00:
                ptr=uc.reg_read(UC_X86_REG_ESI);index=(ptr-TRI)//36
                if ptr!=TRI+index*36 or not start<=index<start+length:raise ValueError('INVALID_SELECTED_FACE')
                sp=uc.reg_read(UC_X86_REG_ESP);code=r32(uc,sp+12)
                code=code if code<2**31 else code-2**32
                calls.append((index,code))
                uc.reg_write(UC_X86_REG_EIP,r32(uc,sp));uc.reg_write(UC_X86_REG_ESP,sp+16)
                return
            if not 0x409860<=addr<0x409a00:raise ValueError('UNEXPECTED_DRAW_ADDRESS:'+hex(addr))
    u.hook_add(UC_HOOK_CODE,hook)
    if initialize:
        w32(u,STACK,STOP);u.reg_write(UC_X86_REG_ESP,STACK)
        u.reg_write(UC_X86_REG_EAX,OBJ);u.reg_write(UC_X86_REG_EDX,1)
        u.emu_start(0x40b4dc,STOP+1,timeout=1000000,count=300000)
        if not phase['returned']:raise ValueError('INIT_DID_NOT_RETURN')
    initialized=bytes(u.mem_read(TRI,len(raw)))
    phase.update(which='filter',returned=False)
    for r,value in [('eax',1),('edx',length),('ebx',start),('esp',STACK)]:u.reg_write(REGS[r],value)
    w32(u,STACK,STOP)
    u.emu_start(0x409860,STOP+1,timeout=1000000,count=600000)
    if not phase['returned']:raise ValueError('FILTER_DID_NOT_RETURN')
    return initialized,calls,phase['instructions']

def main():
    parts,primary=corpus();checks=[];rows=[];totals=Counter()
    def check(label,ok,**values):
        checks.append({'test':label,'pass':bool(ok),**values})
        if not ok:raise ValueError('CHECK_FAILED:'+label)
    alias_names={r['name'] for r in primary if r['kind']==0xffffffff}
    for part in parts:
        hn=part['name'];raw=part['triangle_bytes'];tri=part['triangles'];n=len(tri)
        initialized,calls,steps=run_filter(raw,n)
        expected=bytearray(raw)
        for t in tri:expected[t['index']*36+32]=initialized_flags(raw[t['index']*36+32])
        check(hn+'_original_initializer_byte_exact',initialized==bytes(expected))
        predicted=[(t['index'],t['f3']) for t in tri if not initialized_flags(t['flag32']&255)&16]
        check(hn+'_prefilter_order_and_material',calls==predicted)
        aliases=[t for t in tri if t['f3']>=0 and t['name'] in alias_names]
        selected={i for i,c in calls}
        check(hn+'_no_alias_reaches_raster',all(t['index'] not in selected for t in aliases))
        check(hn+'_alias_source_record_signature',all(t['raw_hex']=='00'*32+'03000000' for t in aliases))
        nodes,ranges=potential_selected(part)
        check(hn+'_reachable_node_graph_bounded',len(nodes)<=len(part['planes']))
        c=Counter(raw_records=n,prefilter_selected=len(calls),prefilter_blocked=n-len(calls),aliases=len(aliases),
            alias_zero_area=sum(t['zero_area'] for t in aliases),reachable_nodes=len(nodes),
            range_union=len(ranges),range_union_prefiltered=len(ranges&selected),
            prefilter_selected_zero_codes=sum(code==0 for _,code in calls),
            prefilter_selected_zero_area=sum(tri[i]['zero_area'] for i in selected))
        totals.update(c)
        rows.append({'hmo':hn,'counts':dict(c),'alias_record_indices':[t['index'] for t in aliases],
            'alias_names':dict(Counter(t['name'] for t in aliases)),
            'nonzero_area_aliases':[],'instruction_count':steps,
            'selected_indices_sha256':sha(struct.pack('<'+'I'*len(calls),*[i for i,_ in calls])),
            'unreachable_plane_indices':sorted(set(range(len(part['planes'])))-nodes),
            'not_in_either_source_plane_range':sorted(set(range(n))-ranges)})
    # Negative controls: flags, not the string NONE or material index zero, drive the filter.
    dummy=bytes(32)+bytes([3,0,0,0])
    _,before,_=run_filter(dummy,1,initialize=False)
    _,after,_=run_filter(dummy,1,initialize=True)
    check('alias_without_initialization_reaches_boundary',before==[(0,0)])
    check('alias_after_initialization_is_rejected',after==[])
    for flag in range(256):
        raw=bytes(32)+bytes([flag,0,0,0]);normalized,got,_=run_filter(raw,1)
        check('flag_truth_table_'+str(flag),bool(got)==(not bool(initialized_flags(flag)&16)) and normalized[32]==initialized_flags(flag))
    check('all_22_alias_references_are_inactive',totals['aliases']==22 and totals['alias_zero_area']==22)
    report={'schema':'OpenMDK1.InactiveAliasContract.v1','status':'PASS','evidence_scope':'ORIGINAL_INSTRUCTION_MICROTEST_AND_CORPUS_SIGNATURE',
        'tests':len(checks),'passed':sum(c['pass'] for c in checks),'checks':checks,'counts':dict(totals),'parts':rows,
        'closed_blocker':'All 22 previously unresolved nonpayload references are source placeholder records, and the observed initialization/filter path excludes them before material lookup.',
        'normalization_hypothesis':'NOT_NEEDED_FOR_THESE_22_RECORDS; no invented alias-to-pixel conversion installed.',
        'exact_rules':{'initializer':'if record[0x20] & 0x02: record[0x20] |= 0x30',
            'draw_prefilter':'skip record when record[0x20] & 0x10 != 0',
            'material_zero':'May reach drawing when flags permit; do not discard every f3==0.'},
        'method':'Raster callback 0x40ca00 intercepted at entry with no raster body execution; model compares initialization and call-selection only.',
        'unicorn_version':unicorn.__version__,'production_binding_changed':False,'game_runtime_executed':False,
        'limits':['This does not prove final pixel visibility or occlusion.','BSP per-camera ordering is the next separate test.',
                 'Live dynamic flag mutations and global state are not covered by the zero-mask initialization fixture.'],
        'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'inactive-alias-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({'status':'PASS','tests':len(checks),'counts':dict(totals),'parts':[{'hmo':r['hmo'],'counts':r['counts']} for r in rows],'sha256':sha(p.read_bytes())},indent=2))
if __name__=='__main__':main()
