import pathlib,struct
from capstone import *
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes();ib=0x400000;e=struct.unpack_from("<I",b,0x3c)[0];n=struct.unpack_from("<H",b,e+6)[0];opt=e+24;so=opt+struct.unpack_from("<H",b,e+20)[0];secs=[]
for i in range(n):
 o=so+i*40;name=b[o:o+8].rstrip(b"\0").decode();vs,va,rs,rp=struct.unpack_from("<4I",b,o+8);secs.append((name,va,vs,rp,rs))
def vo(x):
 r=x-ib
 for _,va,vs,rp,rs in secs:
  if va<=r<va+rs:return rp+r-va
md=Cs(CS_ARCH_X86,CS_MODE_32)
for start,end in [(0x406b80,0x406c80),(0x413b20,0x413c40),(0x46d490,0x46d580)]:
 print("\nFUNC",hex(start))
 for i in md.disasm(b[vo(start):vo(start)+end-start],start):print(f"{i.address:08X} {i.mnemonic:8} {i.op_str}")
