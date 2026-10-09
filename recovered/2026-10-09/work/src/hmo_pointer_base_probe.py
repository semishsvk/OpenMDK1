import pathlib,struct,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]; BASE=20; out={}
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]
 hdr=list(struct.unpack_from("<5I",h,0)); probes=[]
 for j,x in enumerate(hdr):
  for label,pos in [("raw",x),("base20",BASE+x)]:
   if 0<=pos<len(h):
    probes.append({"field":j,"value":x,"mode":label,"pos":pos,"hex":h[pos:pos+48].hex(),"ascii":"".join(chr(c) if 32<=c<127 else "." for c in h[pos:pos+48])})
 out[hn]={"header":hdr,"probes":probes}
print(json.dumps(out,indent=2))
