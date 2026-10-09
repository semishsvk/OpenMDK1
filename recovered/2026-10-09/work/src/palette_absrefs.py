import pathlib,struct,json
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
for t in (0x46d1d0,0x46d208):
 pat=struct.pack("<I",t);hits=[];p=0
 while True:
  p=b.find(pat,p)
  if p<0:break
  hits.append(hex(p));p+=1
 print(hex(t),hits)
