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
    return None
def off2va(x):
    for _,va,vs,rp,rs in secs:
        if rp<=x<rp+rs:return ib+va+x-rp
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32)
for call in [0x410275,0x41D132,0x4297B3,0x42CD82]:
    off=va2off(call)
    lo=max(0,off-900)
    cand=[]
    p=lo
    while p<=off-3:
        if b[p:p+3] in (b"\x55\x8b\xec",b"\x55\x89\xe5"):
            v=off2va(p)
            if v:cand.append((p,v))
        p+=1
    start=cand[-1][1] if cand else call-128
    print("\n=== CALL",hex(call),"FUNC_START?",hex(start),"===")
    so2=va2off(start)
    if so2 is None:continue
    for ins in md.disasm(b[so2:so2+min(1400,off-so2+160)],start):
        if ins.address>call+96:break
        mark=" <-- CALL" if ins.address==call else ""
        print(f"{ins.address:08X} {ins.mnemonic:8} {ins.op_str}{mark}")
