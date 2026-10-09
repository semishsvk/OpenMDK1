import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
secs=[]
for i in range(n):
    o=so+i*40; name=b[o:o+8].rstrip(b"\0").decode(errors="replace"); vs,va,rs,rp=struct.unpack_from("<4I",b,o+8); secs.append((name,va,vs,rp,rs))
def va2off(x):
    r=x-ib
    for _,va,vs,rp,rs in secs:
        if va<=r<va+rs:return rp+r-va
    raise ValueError(hex(x))
md=Cs(CS_ARCH_X86,CS_MODE_32)
for start,size in [(0x419EE0,0x500),(0x40B4DC,0x280),(0x4320D0,0x180)]:
    print("\n===",hex(start),"===")
    off=va2off(start)
    for ins in md.disasm(b[off:off+size],start):
        txt=f"{ins.address:08X} {ins.mnemonic:8} {ins.op_str}"
        if "+ 0x40]" in ins.op_str or "+0x40]" in ins.op_str or ins.address in range(start,start+size):
            print(txt)
