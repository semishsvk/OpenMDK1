import pathlib,struct,json
p=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE");b=p.read_bytes()
e=struct.unpack_from("<I",b,0x3c)[0];n=struct.unpack_from("<H",b,e+6)[0];opt=e+24;imagebase=struct.unpack_from("<I",b,opt+28)[0];secs=[];so=opt+struct.unpack_from("<H",b,e+20)[0]
for i in range(n):
 o=so+i*40;name=b[o:o+8].rstrip(b"\0").decode();vs,va,rs,rp=struct.unpack_from("<4I",b,o+8);secs.append((name,va,vs,rp,rs))
needle=b"init_palette failed";fo=b.find(needle)
sec=next((x for x in secs if x[3]<=fo<x[3]+x[4]),None);rva=sec[1]+fo-sec[3];va=imagebase+rva;pat=struct.pack("<I",va);refs=[];q=0
while True:
 q=b.find(pat,q)
 if q<0:break
 refs.append(q);q+=1
def mapoff(x):
 for s in secs:
  if s[3]<=x<s[3]+s[4]:return {"section":s[0],"rva":hex(s[1]+x-s[3]),"va":hex(imagebase+s[1]+x-s[3])}
 return None
print(json.dumps({"imagebase":hex(imagebase),"string_file_offset":hex(fo),"string_rva":hex(rva),"string_va":hex(va),"refs":[{"file_offset":hex(x),**(mapoff(x) or {})} for x in refs],"sections":secs},indent=2))
