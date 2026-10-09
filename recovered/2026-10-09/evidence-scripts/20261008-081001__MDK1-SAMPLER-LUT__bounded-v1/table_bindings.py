"""Bounded code references to the two four-entry sampler callback tables.
Prefer actual memory operands over false opcode starts inside an instruction.
"""
import struct,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86_const import X86_OP_MEM
from static_probe import load,ROOT,sha
b,ss=load();md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;hits=[]
for target in [0x54dc00,0x54dc04,0x54dc08,0x54dc0c,0x54dc10,0x54dc14,0x54dc18,0x54dc1c,0x54dc20,0x54dc24,0x54dc28,0x54dc2c]:
    pat=struct.pack('<I',target)
    for n,vs,base,size,raw in ss:
        if n!='AUTO':continue
        text=b[raw:raw+size];p=0
        while True:
            p=text.find(pat,p)
            if p<0:break
            for delta in (2,1,3):
                start=p-delta
                ins=next(md.disasm(text[start:start+15],base+start),None)
                if ins and any(o.type==X86_OP_MEM and o.mem.disp==target for o in ins.operands):
                    context=[(hex(i.address),i.bytes.hex(),i.mnemonic+' '+i.op_str) for i in md.disasm(text[start:start+45],base+start)]
                    hits.append({'target':hex(target),'va':hex(ins.address),'op':ins.mnemonic+' '+ins.op_str,'context':context})
                    break
            p+=1
for h in hits:
    print('TABLE_REF',h['target'],h['va'],h['op'])
    for row in h['context']:print(*row)
with (ROOT/'table-binding-candidates.json').open('x',encoding='utf-8') as f:json.dump(hits,f,indent=2)
