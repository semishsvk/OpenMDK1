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
        if va<=r<va+rs:
            return rp+r-va
    raise ValueError(hex(x))
text=secs[0]
data=b[text[3]:text[3]+text[4]]
base=ib+text[1]
md=Cs(CS_ARCH_X86,CS_MODE_32)
targets={0x413B40,0x413B20}
calls=[]
for ins in md.disasm(data,base):
    if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
        try:t=int(ins.op_str,16)
        except:continue
        if t in targets:
            calls.append((ins.address,t))
print("CALLS",[(hex(a),hex(t)) for a,t in calls])
for a,t in calls:
    print("\nCALLER",hex(a),"->",hex(t))
    start=max(base,a-128)
    chunk=b[va2off(start):va2off(start)+256]
    for ins in md.disasm(chunk,start):
        if a-112 <= ins.address <= a+80:
            print(f"{ins.address:08X} {ins.mnemonic:8} {ins.op_str}")
