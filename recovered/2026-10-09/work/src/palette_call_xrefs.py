import pathlib,struct,json
from capstone import *
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes();ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0];n=struct.unpack_from("<H",b,e+6)[0];opt=e+24;so=opt+struct.unpack_from("<H",b,e+20)[0];secs=[]
for i in range(n):
 o=so+i*40;name=b[o:o+8].rstrip(b"\0").decode();vs,va,rs,rp=struct.unpack_from("<4I",b,o+8);secs.append((name,va,vs,rp,rs))
def off2va(x):
 for _,va,vs,rp,rs in secs:
  if rp<=x<rp+rs:return ib+va+x-rp
def vo(x):
 r=x-ib
 for _,va,vs,rp,rs in secs:
  if va<=r<va+rs:return rp+r-va
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
textsec=secs[0];data=b[textsec[3]:textsec[3]+textsec[4]];base=ib+textsec[1];refs={hex(t):[] for t in (0x46d1d0,0x46d208)}
for ins in md.disasm(data,base):
 if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
  try:t=int(ins.op_str,16)
  except:continue
  if hex(t) in refs:refs[hex(t)].append(ins.address)
print(json.dumps(refs,indent=2))
for t,addrs in refs.items():
 for a in addrs:
  print("\nCALLER",hex(a),"->",t)
  st=max(base,a-96);chunk=b[vo(st):vo(st)+192]
  for i in md.disasm(chunk,st):
   if a-80<=i.address<=a+48:print(f"{i.address:08X} {i.mnemonic:8} {i.op_str}")
