"""Targeted discovery of original pixel loops and LUT provider references."""
import struct,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from static_probe import load,ROOT,sha
b,secs=load();md=Cs(CS_ARCH_X86,CS_MODE_32);rows=[]
for target in [0x54ec20,0x54ec24,0x54ec48,0x54ebd4,0x540b20]:
    pattern=struct.pack('<I',target)
    for name,vs,base,size,raw in secs:
        if name!='AUTO':continue
        text=b[raw:raw+size];pos=0
        while True:
            p=text.find(pattern,pos)
            if p<0:break
            pos=p+1;found=None
            for width in (1,2,3):
                s=p-width;ins=list(md.disasm(text[s:p+4],base+s))
                if len(ins)==1 and hex(target) in ins[0].op_str:found=s;break
            if found is None:continue
            context=[{'va':hex(i.address),'bytes':i.bytes.hex(),'op':i.mnemonic+' '+i.op_str}
                for i in md.disasm(text[found:found+96],base+found)]
            rows.append({'target':hex(target),'instruction_va':hex(base+found),'context':context})
for r in rows:
    if int(r['instruction_va'],16) in range(0x46daac,0x46e940):continue
    print('\nREF',r['target'],r['instruction_va'])
    for i in r['context'][:12]:print(i['va'],i['bytes'],i['op'])
p=ROOT/'pixel-xref-candidates.json'
with p.open('x',encoding='utf-8') as f:json.dump({'source_sha256':sha(b),'claim':'DISCOVERY_ONLY','references':rows},f,indent=2)
print('REFERENCES',len(rows),'SHA256',sha(p.read_bytes()))
