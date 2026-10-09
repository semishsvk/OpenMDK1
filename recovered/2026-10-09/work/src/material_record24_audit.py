import struct,pathlib,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;hn=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];n=struct.unpack_from("<I",h,36)[0]; recs=[]
 for i in range(n):
  r=h[40+i*24:40+(i+1)*24]; recs.append({"i":i,"hex":r.hex(),"ascii":r.split(b"\0")[0].decode("ascii","replace"),"u32":list(struct.unpack("<6I",r))})
 out[hn]=recs
print(json.dumps(out,indent=2))
