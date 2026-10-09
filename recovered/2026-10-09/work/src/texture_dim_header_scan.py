import struct,pathlib,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
dims={16,32,64,128,256,512}
for bi in range(cnt):
 q=24+bi*12;hn=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];n=struct.unpack_from("<I",h,36)[0]
 if not n:continue
 names=[h[40+i*24:40+(i+1)*24].split(b"\0")[0].decode("ascii","replace") for i in range(n)];offs=[struct.unpack_from("<I",h,60+i*24)[0] for i in range(n)];end=struct.unpack_from("<I",h,4)[0];arr=[]
 for i,o in enumerate(offs):
  z=offs[i+1] if i+1<n else end;d=h[o:z];hits=[]
  for p in range(0,len(d)-4,2):
   w,hh=struct.unpack_from("<2H",d,p)
   if w in dims and hh in dims and p+4+w*hh<=len(d):
    hits.append({"p":p,"w":w,"h":hh,"end":p+4+w*hh,"remaining":len(d)-(p+4+w*hh)})
  arr.append({"name":names[i],"size":len(d),"hits":hits[:30]})
 out[hn]=arr
print(json.dumps(out,indent=2))
