import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM,X86_OP_IMM
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
o=so
name=b[o:o+8].rstrip(b"\0").decode(errors="replace"); vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
insns=list(md.disasm(b[rp:rp+rs],ib+va))
cand=[]
for i,ins in enumerate(insns):
    has24=False
    if ins.mnemonic in ("add","imul","lea"):
        if "0x24" in ins.op_str:
            has24=True
    if not has24: continue
    lo=max(0,i-80); hi=min(len(insns),i+81)
    disps=set()
    for q in insns[lo:hi]:
        for op in q.operands:
            if op.type==X86_OP_MEM:
                disps.add(op.mem.disp)
    if 0x28 in disps and 0x10 in disps:
        cand.append((ins.address,ins.mnemonic,ins.op_str,sorted(x for x in disps if 0<=x<=0x60)))
print("CANDIDATES",len(cand))
for x in cand[:200]:
    print(hex(x[0]),x[1],x[2],"disps",x[3])
