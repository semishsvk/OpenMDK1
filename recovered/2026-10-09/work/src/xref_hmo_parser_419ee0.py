import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
secs=[]
for i in range(n):
    o=so+i*40; name=b[o:o+8].rstrip(b"\0").decode(errors="replace"); vs,va,rs,rp=struct.unpack_from("<4I",b,o+8); secs.append((name,va,vs,rp,rs))
def off2va(x):
    for _,va,vs,rp,rs in secs:
        if rp<=x<rp+rs:return ib+va+x-rp
def va2off(x):
    r=x-ib
    for _,va,vs,rp,rs in secs:
        if va<=r<va+rs:return rp+r-va
target=0x419EE0
hits=[]
for off in range(len(b)-5):
    if b[off]!=0xE8: continue
    va=off2va(off)
    if va is None: continue
    rel=struct.unpack_from("<i",b,off+1)[0]
    if va+5+rel==target:hits.append((off,va))
print("HITS",[(hex(o),hex(v)) for o,v in hits])
md=Cs(CS_ARCH_X86,CS_MODE_32)
for _,a in hits:
    st=a-128; off=va2off(st)
    if off is None:continue
    print("\n=== CALL",hex(a),"===")
    for ins in md.disasm(b[off:off+240],st):
        if a-112<=ins.address<=a+96:
            mark=" <-- CALL" if ins.address==a else ""
            print(f"{ins.address:08X} {ins.mnemonic:8} {ins.op_str}{mark}")
