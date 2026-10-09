import struct,pathlib,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;hn=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];n=struct.unpack_from("<I",h,36)[0]
 if not n:continue
 names=[h[40+i*24:40+(i+1)*24].split(b"\0")[0].decode("ascii","replace") for i in range(n)];offs=[struct.unpack_from("<I",h,60+i*24)[0] for i in range(n)];end=struct.unpack_from("<I",h,4)[0];arr=[]
 for i,o in enumerate(offs):
  z=offs[i+1] if i+1<n else end;d=h[o:z];w,hh=struct.unpack_from("<2H",d,20) if len(d)>=24 else (0,0);expect=32+w*hh
  arr.append({"name":names[i],"size":len(d),"w":w,"h":hh,"expected_20hdr_pixels_8tail":expect,"exact":expect==len(d),"delta":len(d)-expect})
 out[hn]=arr
print(json.dumps(out,indent=2))
