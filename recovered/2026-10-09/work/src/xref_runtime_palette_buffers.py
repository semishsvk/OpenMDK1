import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
secs=[]
for i in range(n):
    o=so+i*40
    name=b[o:o+8].rstrip(b"\0").decode(errors="replace")
    vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
    secs.append((name,va,vs,rp,rs))
def off2va(x):
    for _,va,vs,rp,rs in secs:
        if rp<=x<rp+rs:return ib+va+x-rp
def va2off(x):
    r=x-ib
    for _,va,vs,rp,rs in secs:
        if va<=r<va+rs:return rp+r-va
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32)
for target in [0x54BF34,0x4ED758]:
    pat=struct.pack("<I",target)
    hits=[]; p=0
    while True:
        p=b.find(pat,p)
        if p<0:break
        va=off2va(p)
        if va:hits.append((p,va))
        p+=1
    print("\nTARGET",hex(target),"HITS",[(hex(o),hex(v)) for o,v in hits])
    for _,va in hits:
        st=va-36; off=va2off(st)
        if off is None:continue
        print("\n==",hex(va),"==")
        for ins in md.disasm(b[off:off+96],st):
            if va-28<=ins.address<=va+36:
                print(f"{ins.address:08X} {ins.mnemonic:8} {ins.op_str}")
