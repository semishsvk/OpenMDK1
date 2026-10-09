import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
o=so
vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
ins=list(md.disasm(b[rp:rp+rs],ib+va))
hits=[]
for i,x in enumerate(ins):
    mem28=[]
    for op in x.operands:
        if op.type==X86_OP_MEM and op.mem.disp==0x28 and op.mem.base:
            mem28.append(op.mem.base)
    if not mem28: continue
    for base in mem28:
        found=[]
        for j in range(max(0,i-30),min(len(ins),i+31)):
            if j==i: continue
            y=ins[j]
            for op in y.operands:
                if op.type==X86_OP_MEM and op.mem.base==base and op.mem.disp==0x10:
                    found.append(y.address)
        if found:
            hits.append((x.address,base,found[:6]))
print("HITS",len(hits))
for a,bv,fs in hits[:200]:
    print(hex(a),"base",md.reg_name(bv),"near10",[hex(z) for z in fs])
