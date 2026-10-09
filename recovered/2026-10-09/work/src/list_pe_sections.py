import pathlib,struct
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
for i in range(n):
 o=so+i*40
 name=b[o:o+8].rstrip(b"\0").decode(errors="replace")
 vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
 ch=struct.unpack_from("<I",b,o+36)[0]
 print(i,name,hex(va),hex(vs),hex(rp),hex(rs),hex(ch))
