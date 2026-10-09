"""Bounded raw-pattern discovery; candidate disassembly is not proof by itself."""
import re,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from static_probe import load,sha,ROOT,PIN,SOURCE
b,sections=load();md=Cs(CS_ARCH_X86,CS_MODE_32);hits=[]
for name,vs,base,size,raw in sections:
    if name!='AUTO':continue
    t=b[raw:raw+size]
    patterns=[('dword_plus4_then_sar16',rb'\x8b[\x40-\x7f]\x04'),('signed_word_plus6',rb'\x0f\xbf[\x40-\x7f]\x06')]
    for mode,p in patterns:
        for m in re.finditer(p,t):
            start=m.start();ins=list(md.disasm(t[start:start+96],base+start))
            if not ins:continue
            if mode=='dword_plus4_then_sar16':
                register=ins[0].op_str.split(',')[0]
                target=next((i for i in ins[1:12] if i.mnemonic=='sar' and i.op_str==register+', 0x10'),None)
                if target is None:continue
            hits.append({'mode':mode,'va':hex(base+start),'rows':[hex(i.address)+' '+i.bytes.hex()+' '+i.mnemonic+' '+i.op_str for i in ins[:14]]})
if sha(SOURCE.read_bytes())!=PIN:raise RuntimeError('SOURCE_CHANGED')
out=ROOT/'consumer-candidates.json'
with out.open('x',encoding='utf-8') as f:json.dump({'source_sha256':PIN,'claim':'DISCOVERY_ONLY','hits':hits},f,indent=2)
print('HITS',len(hits),'SHA256',sha(out.read_bytes()))
for h in hits:
    print('\nCANDIDATE',h['va'],h['mode'])
    print('\n'.join(h['rows']))
