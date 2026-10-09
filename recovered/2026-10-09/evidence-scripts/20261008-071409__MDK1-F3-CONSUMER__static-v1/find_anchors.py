"""Find local prologue candidates and mapping-table references, read-only."""
from static_probe import load,offset,ROOT,sha
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
import struct,json
b,sections=load();md=Cs(CS_ARCH_X86,CS_MODE_32);rows=[]
for target in [0x40c25e,0x40c717,0x454f94]:
    at=offset(sections,target,1);start=b.rfind(bytes.fromhex('5589e5'),max(0,at-4096),at)
    if start<0:continue
    va=target-(at-start);size=at-start+160
    ins=list(md.disasm(b[start:start+size],va))
    row={'target':hex(target),'start':hex(va),'instructions':[(hex(i.address),i.bytes.hex(),i.mnemonic+' '+i.op_str) for i in ins]}
    rows.append(row)
    print('\nPROLOGUE_CANDIDATE',hex(target),'->',hex(va))
    for i in ins:
        if i.address<va+80 or target-135<=i.address<=target+100 or '0x54b724' in i.op_str:
            print(hex(i.address),i.bytes.hex(),i.mnemonic,i.op_str)
p=ROOT/'parent-consumer-anchors.json'
with p.open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2)
print('SHA256',sha(p.read_bytes()))
