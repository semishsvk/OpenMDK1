import struct,pathlib,re,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;name=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e]
 strings=[]
 for m in re.finditer(rb'[A-Z0-9_\.]{3,15}\x00',h[:4096]):
  strings.append({"off":m.start(),"text":m.group()[:-1].decode()})
 words=[struct.unpack_from("<I",h,o)[0] for o in range(0,min(256,len(h)-3),4)]
 out[name]={"size":len(h),"u32_0_64":words[:16],"strings_0_4096":strings[:80]}
print(json.dumps(out,indent=2))
