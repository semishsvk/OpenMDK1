import pathlib,struct,json
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes();pat=struct.pack("<I",0x54d7b8);hits=[];p=0
while True:
 p=b.find(pat,p)
 if p<0:break
 hits.append(hex(p));p+=1
print(json.dumps(hits))
