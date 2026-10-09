"""Bounded discovery of direct callers and anchored source code for variant choice.
A candidate prologue is not itself a verified call graph or live runtime trace.
"""
import struct,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from static_probe import load,offset,ROOT,sha
b,secs=load();md=Cs(CS_ARCH_X86,CS_MODE_32);rows=[]
for name,vs,base,size,raw in secs:
    if name!='AUTO':continue
    text=b[raw:raw+size]
    for i in range(len(text)-5):
        if text[i]!=0xe8:continue
        target=(base+i+5+struct.unpack_from('<i',text,i+1)[0])&0xffffffff
        if target not in {0x46da6c,0x46daac,0x46e52c}:continue
        anchor=text.rfind(bytes.fromhex('5589e5'),max(0,i-8192),i)
        if anchor<0:continue
        instructions=list(md.disasm(text[anchor:i+64],base+anchor))
        if not any(x.address==base+i and x.mnemonic=='call' for x in instructions):continue
        rows.append({'call':hex(base+i),'target':hex(target),'anchor':hex(base+anchor),
          'context':[{'va':hex(x.address),'bytes':x.bytes.hex(),'op':x.mnemonic+' '+x.op_str} for x in instructions if base+i-100<=x.address<=base+i+40]})
with (ROOT/'variant-call-candidates.json').open('x',encoding='utf-8') as f:json.dump({'scope':'DISCOVERY_ONLY','source_sha256':sha(b),'calls':rows},f,indent=2)
for r in rows:
    print('CALL',r['call'],'TARGET',r['target'],'ANCHOR',r['anchor'])
    for x in r['context']:print(x['va'],x['bytes'],x['op'])
