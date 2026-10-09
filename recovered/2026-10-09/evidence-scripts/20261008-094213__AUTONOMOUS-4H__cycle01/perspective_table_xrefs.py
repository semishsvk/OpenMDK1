"""Bounded reciprocal-table and alternate-table references for perspective span proof."""
import json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM
from static_probe import load,ROOT,PIN,sha
b,segs=load();md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;rows=[]
for target in (0x54dc30,0x49bce4):
 pat=struct.pack('<I',target)
 for name,vs,base,size,off in segs:
  if name!='AUTO':continue
  raw=b[off:off+size];pos=0
  while True:
   p=raw.find(pat,pos)
   if p<0:break
   pos=p+1
   anchor=raw.rfind(bytes.fromhex('5589e5'),max(0,p-3000),p)
   if anchor<0:continue
   ins=list(md.disasm(raw[anchor:p+50],base+anchor))
   found=next((i for i in ins if i.address<=base+p and base+p+4<=i.address+i.size and any(o.type==X86_OP_MEM and o.mem.disp==target or o.type==X86_OP_IMM and o.imm==target for o in i.operands)),None)
   if not found:continue
   rows.append({'target':hex(target),'instruction':hex(found.address),'anchor':hex(base+anchor),'context':[{'va':hex(i.address),'op':i.mnemonic+' '+i.op_str,'bytes':i.bytes.hex()} for i in ins if base+p-55<=i.address<base+p+35]})
p=ROOT/'perspective-table-xrefs.json'
with p.open('x',encoding='utf-8') as f:json.dump({'source_exe_sha256':PIN,'scope':'ANCHORED_DISCOVERY_ONLY','references':rows},f,indent=2)
for r in rows:
 if r['target']=='0x54dc30' and int(r['instruction'],16)>=0x470000:continue
 print('REF',r['target'],r['instruction'],'ANCHOR',r['anchor']);print('\n'.join(i['va']+' '+i['op'] for i in r['context']))
print('SOURCE_REFERENCES',len(rows))
