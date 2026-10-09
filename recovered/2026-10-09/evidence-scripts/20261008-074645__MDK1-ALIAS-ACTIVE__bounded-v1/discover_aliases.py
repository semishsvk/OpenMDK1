"""Candidate discovery only. A byte pattern or prologue match is not a semantic PASS."""
from pathlib import Path
import json,re,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from static_probe import load,ROOT,sha
b,sections=load();md=Cs(CS_ARCH_X86,CS_MODE_32);hits=[]
patterns=[('descriptor_type_minus_one',rb'\x83[\x78-\x7f]\x0c\xff'),
          ('triangle_word_write_plus6',rb'\x66\x89[\x40-\x7f]\x06'),
          ('descriptor_type_test',rb'\x83[\x78-\x7f]\x0c\x00')]
for name,vs,base,size,raw in sections:
    if name!='AUTO':continue
    text=b[raw:raw+size]
    for label,p in patterns:
        for m in re.finditer(p,text):
            at=m.start();anchor=text.rfind(bytes.fromhex('5589e5'),max(0,at-4096),at)
            if anchor<0:continue
            ins=list(md.disasm(text[anchor:at+96],base+anchor))
            if not any(i.address==base+at for i in ins):continue
            near=[{'va':hex(i.address),'hex':i.bytes.hex(),'op':i.mnemonic+' '+i.op_str} for i in ins if base+at-45<=i.address<base+at+80]
            hits.append({'kind':label,'va':hex(base+at),'anchor':hex(base+anchor),'context':near})
m=Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3S.MTI').read_bytes()
records=[]
for i in range(struct.unpack_from('<I',m,20)[0]):
    q=24+i*24;n=m[q:q+8].split(b'\0')[0].decode('ascii')
    if n in {'NONE','PEN_16','PEN_37','GLASS1'}:
        records.append({'name':n,'ordinal':i,'offset':q,'hex':m[q:q+24].hex(),'u32_at8':list(struct.unpack_from('<4I',m,q+8))})
out={'schema':'OpenMDK1.AliasCandidates.v1','source_sha256':sha(b),'mti_sha256':sha(m),'hits':hits,'source_materials':records}
with (ROOT/'alias-candidates.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
print('MATERIALS',json.dumps(records))
for h in hits:
    print('\nCANDIDATE',h['kind'],h['va'],'ANCHOR',h['anchor'])
    for i in h['context']:print(i['va'],i['hex'],i['op'])
