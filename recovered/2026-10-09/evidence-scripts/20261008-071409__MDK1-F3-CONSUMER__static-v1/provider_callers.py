"""Discover immediate callers of the three observed descriptor providers."""
from static_probe import load,ROOT,sha
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
import struct,json
b,secs=load();md=Cs(CS_ARCH_X86,CS_MODE_32);rows=[]
for name,vs,base,size,raw in secs:
    if name!='AUTO':continue
    text=b[raw:raw+size]
    for p in range(len(text)-5):
        if text[p]!=0xe8:continue
        target=(base+p+5+struct.unpack_from('<i',text,p+1)[0])&0xffffffff
        if target not in {0x41a480,0x41a4d0,0x41a820}:continue
        start=text.rfind(bytes.fromhex('5589e5'),max(0,p-4096),p)
        if start<0:continue
        ins=list(md.disasm(text[start:p+50],base+start))
        if not any(i.address==base+p and i.mnemonic=='call' for i in ins):continue
        near=[{'va':hex(i.address),'bytes':i.bytes.hex(),'op':i.mnemonic+' '+i.op_str} for i in ins if base+p-90<=i.address<=base+p+35]
        rows.append({'call':hex(base+p),'target':hex(target),'prologue':hex(base+start),'context':near})
for r in rows:
    print('\nCALL',r['call'],'TARGET',r['target'],'PROLOGUE',r['prologue'])
    for i in r['context']:print(i['va'],i['bytes'],i['op'])
p=ROOT/'provider-callers.json'
with p.open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2)
print('SHA256',sha(p.read_bytes()))
