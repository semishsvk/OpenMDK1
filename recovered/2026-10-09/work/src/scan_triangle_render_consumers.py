import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM
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
name,va,vs,rp,rs=next(s for s in secs if s[0]=="AUTO")
md=Cs(CS_ARCH_X86,CS_MODE_32)
md.detail=True
hits=[]
for ins in md.disasm(b[rp:rp+rs],ib+va):
    ds=[]
    for op in ins.operands:
        if op.type==X86_OP_MEM:
            disp=op.mem.disp
            if disp in (8,12,16,20,24,28,32,34):
                ds.append(disp)
    if 34 in ds:
        hits.append((ins.address,ins.mnemonic,ins.op_str,ds))
print("HIT_COUNT",len(hits))
for h in hits[:800]:
    print(f"{h[0]:08X} {h[1]:8} {h[2]} DISP={h[3]}")
