"""Read-only MDK95 byte observations. No native game code is executed.
Outputs are new files in this isolated evidence run, never the game worktree.
"""
from pathlib import Path
import argparse, hashlib, json, struct
import capstone
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
SOURCE=Path(r'F:\Remaster Framework\source\MDK\MDK95.EXE')
PIN='e57bd63ba6af1ce201e3dd28a352e36ffa737267a9be0ed733fb81e6c40ba788'
ROOT=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def load():
    b=SOURCE.read_bytes()
    if sha(b)!=PIN:raise ValueError('SOURCE_FINGERPRINT_CHANGED')
    pe=struct.unpack_from('<I',b,0x3c)[0]
    if b[pe:pe+4]!=b'PE\0\0':raise ValueError('NOT_PE')
    opt=pe+24
    if struct.unpack_from('<H',b,opt)[0]!=0x10b:raise ValueError('NOT_PE32')
    base=struct.unpack_from('<I',b,opt+28)[0]
    st=opt+struct.unpack_from('<H',b,pe+20)[0]
    sections=[]
    for i in range(struct.unpack_from('<H',b,pe+6)[0]):
        q=st+40*i
        vs,va,rs,rp=struct.unpack_from('<4I',b,q+8)
        sections.append((b[q:q+8].rstrip(b'\0').decode(),vs,base+va,rs,rp))
    return b,sections

def offset(sections,va,size):
    matches=[rp+va-start for _,vs,start,rs,rp in sections if start<=va and va+size<=start+rs]
    if len(matches)!=1:raise ValueError('UNBACKED_OR_AMBIGUOUS_CODE_RANGE')
    return matches[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('va',type=lambda s:int(s,0));p.add_argument('size',type=lambda s:int(s,0));a=p.parse_args()
    if not 1<=a.size<=8192:raise ValueError('BYTE_BUDGET_EXCEEDED')
    b,sections=load();off=offset(sections,a.va,a.size);raw=b[off:off+a.size]
    rows=[{'va':hex(i.address),'bytes':i.bytes.hex(),'op':i.mnemonic+' '+i.op_str} for i in Cs(CS_ARCH_X86,CS_MODE_32).disasm(raw,a.va)]
    report={'schema':'OpenMDK1.StaticCodeObservation.v1','source_sha256':PIN,'source':str(SOURCE),
       'game_executed':False,'capstone':capstone.__version__,'virtual_address':hex(a.va),'file_offset':off,
       'raw_sha256':sha(raw),'raw_hex':raw.hex(),'bytes_requested':a.size,
       'instructions':rows,'alignment_scope':'Caller-specified start; semantics only where a control-flow anchor is independently established.'}
    if sha(SOURCE.read_bytes())!=PIN:raise ValueError('SOURCE_CHANGED_DURING_READ')
    out=ROOT/f'code_{a.va:08x}_{a.size:x}.json'
    with out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print('ARTIFACT',out,'SHA256',sha(out.read_bytes()))
    for row in rows:print(row['va'],row['bytes'],row['op'])
if __name__=='__main__':main()
