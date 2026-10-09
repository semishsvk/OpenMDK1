import pathlib,struct
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3S.MTI").read_bytes()
count=struct.unpack_from("<I",b,20)[0]
for i in range(max(0,count-25),count):
 o=24+i*24
 name=b[o:o+8].split(b"\0")[0].decode("ascii","replace")
 u16a,u16b=struct.unpack_from("<HH",b,o+8)
 u32=struct.unpack_from("<I",b,o+12)[0]
 f=struct.unpack_from("<f",b,o+16)[0]
 off=struct.unpack_from("<I",b,o+20)[0]
 print(i,repr(name),"u16",u16a,u16b,"u32",u32,"f",f,"off",off)
