from mdk_machine import *
from collision_port import Collision
import json,random
m=Machine();base=0x3001000;cmd=0x3007000;startptr=0x3007100;endptr=0x3007120
m.write(base+0x38,'I',1);m.write(base+0x3c,'I',cmd);m.write(0x574ae0,'I',base)
raw=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI').read_bytes();record=bytearray(raw[0x2c8:0x2c8+36]);struct.pack_into('<I',record,4,10);m.uc.mem_write(cmd,bytes(record))
margin=m.read(0x4945c8,'f')[0]
def outside_or_cross(end,start,lo,hi):
 return lo<=end<=hi or ((end<lo)!=(start<lo)) or ((end<hi)!=(start<hi))
def port(start,end):
 return outside_or_cross(end[2],start[2],104+margin,126) and outside_or_cross(end[0],start[0],-19,17) and end[1]>654 and start[1]<=654
rng=random.Random(653);inputs=[([0,653,115],[0,655,115]),([0,655,115],[0,653,115])]
for x in [-20,-19,-18,16,17,18]:
 for z in [103,104,104+margin,105,125,126,127]:inputs.append(([x,654,z],[x,655,z]))
for _ in range(700):inputs.append(([rng.uniform(-30,30),rng.uniform(650,658),rng.uniform(98,132)],[rng.uniform(-30,30),rng.uniform(650,658),rng.uniform(98,132)]))
cases=[]
for start,end in inputs:
 start=list(struct.unpack('<3f',struct.pack('<3f',*start)));end=list(struct.unpack('<3f',struct.pack('<3f',*end)))
 m.write(startptr,'3f',*start);m.write(endptr,'3f',*end)
 result=m.call(0x41c550,{UC_X86_REG_EAX:base,UC_X86_REG_EDX:startptr,UC_X86_REG_EBX:endptr})
 expected=base+10*0x466 if port(start,end) else 0
 assert result==expected,(start,end,hex(result),hex(expected))
 cases.append(dict(start=start,end=end,target=10 if result else None))
mto=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes();c=Collision(mto,0xdaa6c,0xdd510,0xe0d30);approach=[0,652,115];exit=[0,656,115];hit=c.query(approach,exit)
r=dict(status='OBJECT0_FLAG3_PORTAL_SELECTOR_ORIGINAL_X86_MATCHES_PORT',routine='0x41C550',abi='EAX=worldObject; EDX=previous XYZ; EBX=current XYZ; return EAX=target object pointer or zero',target_index=10,target_name='CHMO_1',record_source_offset='0x2C8',plane_y=654,x_range=[-19,17],z_range=[104+margin,126],height_margin=margin,cases=cases,hit_cases=sum(c['target'] is not None for c in cases),source_activation_callsite='0x41D743 selector; 0x41D76B prior object->573A68; 0x41D778 target->573A0C; 0x41D77E invokes 0x41A11C',approach_segment=dict(start=approach,end=exit,collision_hit=hit),scope='Only actual object0 type6 flag3 selector; includes executable unusual bound-crossing behavior. Full CHMO1 resource activation is not executed.')
pathlib.Path('portal_segment_receipt.json').write_text(json.dumps(r,indent=2));print('PORTAL CASES',len(cases),'HITS',r['hit_cases'],'MARGIN',margin,'APPROACH COLLISION',hit)
