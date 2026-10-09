import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
o=so; vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
targets={0x9c,0xc0}
hits=[]
for ins in md.disasm(b[rp:rp+rs],ib+va):
 for op in ins.operands:
  if op.type==X86_OP_MEM and op.mem.disp in targets:
   hits.append((ins.address,ins.mnemonic,ins.op_str,op.mem.disp,md.reg_name(op.mem.base)))
print("HITS",len(hits))
for h in hits[:1000]:
 print(f"{h[0]:08X} {h[1]:8} {h[2]} disp={hex(h[3])} base={h[4]}")
