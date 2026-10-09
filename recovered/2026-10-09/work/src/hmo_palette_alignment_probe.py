import pathlib,struct,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
allowed=set(((i<<3)|(i>>2)) for i in range(32))
out={}
for bi in range(cnt):
 q=24+bi*12
 hn=B[q:q+8].split(b"\0")[0].decode()
 s=struct.unpack_from("<I",B,q+8)[0]
 e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
 h=B[s:e]
 a=struct.unpack_from("<I",h,8)[0]
 z=struct.unpack_from("<I",h,12)[0]
 blk=h[a:z]
 bad=[i for i,v in enumerate(blk) if v not in allowed]
 best=(0,0)
 start=0
 seq=list(blk)+[127]
 for i,v in enumerate(seq):
  if i<len(blk) and v in allowed:
   continue
  if i-start>best[1]-best[0]:
   best=(start,i)
  start=i+1
 aligns=[]
 for off in range(12):
  usable=len(blk)-off
  triples=usable//3
  vals=blk[off:off+triples*3]
  badn=sum(v not in allowed for v in vals)
  aligns.append({"off":off,"triples":triples,"bad_bytes":badn,"remainder":usable%3})
 out[hn]={"len":len(blk),"bad_positions":bad[:40],"bad_count":len(bad),"best_quantized_run":list(best),"best_run_len":best[1]-best[0],"alignments":aligns,"first32":list(blk[:32]),"last32":list(blk[-32:])}
print(json.dumps({"schema":"OpenMDK.HMOPaletteAlignmentProbe.v1","allowed":"5bit expansion (v<<3)|(v>>2)","hmos":out},indent=2))
