import struct,pathlib,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;hn=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];n=struct.unpack_from("<I",h,36)[0]
 if not n:continue
 names=[h[40+i*24:40+(i+1)*24].split(b"\0")[0].decode("ascii","replace") for i in range(n)];offs=[struct.unpack_from("<I",h,60+i*24)[0] for i in range(n)];end=struct.unpack_from("<I",h,4)[0];arr=[]
 for i,o in enumerate(offs):
  w,hh=struct.unpack_from("<2H",h,o+20); pixend=o+24+w*hh; nxt=offs[i+1] if i+1<n else end
  arr.append({"name":names[i],"off":o,"w":w,"h":hh,"pixend":pixend,"next":nxt,"next_minus_pixend":nxt-pixend,"bytes_at_pixend_28":h[pixend:pixend+28].hex(),"next_prefix_28":h[nxt:nxt+28].hex()})
 out[hn]=arr
print(json.dumps(out,indent=2))
