"""Bounded references to observed material registries, not a whole-project RE."""
import struct,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from static_probe import load,ROOT,sha
b,secs=load();md=Cs(CS_ARCH_X86,CS_MODE_32);rows=[]
for target in [0x54b724,0x54b728,0x54b72c]:
    pattern=struct.pack('<I',target)
    for name,vs,base,size,raw in secs:
        if name!='AUTO':continue
        text=b[raw:raw+size];pos=0
        while True:
            p=text.find(pattern,pos)
            if p<0:break
            pos=p+1
            start=text.rfind(bytes.fromhex('5589e5'),max(0,p-5000),p)
            if start<0:continue
            ins=list(md.disasm(text[start:p+64],base+start))
            near=[(hex(i.address),i.bytes.hex(),i.mnemonic+' '+i.op_str) for i in ins if base+p-24<=i.address<=base+p+22]
            matched=any(i.address<=base+p and base+p+4<=i.address+i.size and hex(target) in i.op_str for i in ins)
            if not matched:continue
            rows.append({'target':hex(target),'operand_va':hex(base+p),'anchor':hex(base+start),'context':near})
for r in rows:
    print('\nREF',r['target'],r['operand_va'],'anchor',r['anchor'])
    for x in r['context']:print(*x)
out=ROOT/'namespace-xrefs.json'
with out.open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2)
print('SHA256',sha(out.read_bytes()))
