import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
o=so
vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
targets={0x9e,0xa2,0xa6,0xaa,0xae,0xb2,0xc2,0xc6,0xca,0xce,0xd2,0xd6}
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
hits=[]
for ins in md.disasm(b[rp:rp+rs],ib+va):
    ds=[]
    for op in ins.operands:
        if op.type==X86_OP_MEM and op.mem.disp in targets:
            ds.append(op.mem.disp)
    if ds:hits.append((ins.address,ins.mnemonic,ins.op_str,ds))
print("HITS",len(hits))
for h in hits[:1200]:
    print(f"{h[0]:08X} {h[1]:8} {h[2]} DISP={[hex(x) for x in h[3]]}")
