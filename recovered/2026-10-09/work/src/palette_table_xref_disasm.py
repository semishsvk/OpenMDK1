import pathlib,struct
from capstone import *
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes();ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0];n=struct.unpack_from("<H",b,e+6)[0];opt=e+24;so=opt+struct.unpack_from("<H",b,e+20)[0];secs=[]
for i in range(n):
 o=so+i*40;name=b[o:o+8].rstrip(b"\0").decode();vs,va,rs,rp=struct.unpack_from("<4I",b,o+8);secs.append((name,va,vs,rp,rs))
def off2va(x):
 for _,va,vs,rp,rs in secs:
  if rp<=x<rp+rs:return ib+va+x-rp
def va2off(x):
 r=x-ib
 for _,va,vs,rp,rs in secs:
  if va<=r<va+rs:return rp+r-va
hits=[0x31680,0x31e46,0x33b9e,0x6c5dd,0x6c62f,0x6c77d,0x6c8a0,0x6ca1b];md=Cs(CS_ARCH_X86,CS_MODE_32)
for fo in hits:
 va=off2va(fo);st=va-48;print("\n=== ref",hex(fo),"VA",hex(va),"===")
 chunk=b[va2off(st):va2off(st)+128]
 for i in md.disasm(chunk,st):
  if va-40<=i.address<=va+56:print(f"{i.address:08X} {i.mnemonic:8} {i.op_str}")
