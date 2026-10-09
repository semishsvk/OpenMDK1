import struct,pathlib,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;hn=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];n=struct.unpack_from("<I",h,36)[0];ext=struct.unpack_from("<I",h,60)[0]
 offs=[struct.unpack_from("<I",h,40+i*24+20)[0] for i in range(n)]
 seg=[(offs[i+1] if i+1<n else struct.unpack_from("<I",h,4)[0])-offs[i] for i in range(n)] if n else []
 out[hn]={"count":n,"extent":ext,"offsets":offs,"first_eq_extent":bool(n and offs[0]==ext),"strictly_increasing":all(offs[i]<offs[i+1] for i in range(len(offs)-1)),"segment_sizes":seg,"payload_end_header_u32_04":struct.unpack_from("<I",h,4)[0],"block_size":len(h)}
print(json.dumps(out,indent=2))
