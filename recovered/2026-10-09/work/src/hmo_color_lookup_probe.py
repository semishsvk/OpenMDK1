import pathlib,struct,hashlib,json,collections
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]
 a=struct.unpack_from("<I",h,8)[0]; z=struct.unpack_from("<I",h,12)[0]; blk=h[a:z]
 first=blk[:256]; tail=blk[256:]
 n=struct.unpack_from("<I",h,36)[0]
 tex=bytearray()
 for i in range(n):
  rel=struct.unpack_from("<I",h,40+i*24+20)[0]; p=20+rel; w,hh=struct.unpack_from("<HH",h,p); tex.extend(h[p+4:p+4+w*hh])
 used=sorted(set(tex))
 mapped=[first[x] for x in used] if len(first)==256 else []
 out[hn]={
   "block_len":len(blk),"first256_sha256":hashlib.sha256(first).hexdigest(),"tail80_sha256":hashlib.sha256(tail).hexdigest(),
   "first256_unique":len(set(first)),"tail80_unique":len(set(tail)),
   "identity_entries":sum(i==v for i,v in enumerate(first)),
   "texture_unique_indices":len(used),"texture_index_minmax":[min(used),max(used)] if used else None,
   "used_indices_all_addressable":all(x<256 for x in used),
   "mapped_unique":len(set(mapped)) if mapped else 0,
   "tail80_hex":tail.hex(),
   "first32":list(first[:32]),"last32":list(first[-32:])
 }
print(json.dumps({"schema":"OpenMDK.HMOColorLookupProbe.v1","hypothesis":"336-byte block = 256-byte lookup + 80-byte metadata","hmos":out},indent=2))
