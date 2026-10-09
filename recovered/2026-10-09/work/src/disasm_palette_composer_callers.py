import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]
n=struct.unpack_from("<H",b,e+6)[0]
opt=e+24
so=opt+struct.unpack_from("<H",b,e+20)[0]
secs=[]
for i in range(n):
    o=so+i*40
    name=b[o:o+8].rstrip(b"\0").decode(errors="replace")
    vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
    secs.append((name,va,vs,rp,rs))
def va2off(x):
    r=x-ib
    for _,va,vs,rp,rs in secs:
        if va<=r<va+rs:return rp+r-va
    raise ValueError(hex(x))
calls=[0x409224,0x40f605,0x410275,0x41d132,0x41d80f,0x41dedf,0x41ec2a,0x4205d3,0x420b6f,0x4297b3,0x42cd82,0x433dda]
md=Cs(CS_ARCH_X86,CS_MODE_32)
for a in calls:
    print("\n=== CALL",hex(a),"===")
    st=a-112
    try:off=va2off(st)
    except:continue
    chunk=b[off:off+208]
    for ins in md.disasm(chunk,st):
        if a-96<=ins.address<=a+64:
            mark=" <-- CALL" if ins.address==a else ""
            print(f"{ins.address:08X} {ins.mnemonic:8} {ins.op_str}{mark}")
