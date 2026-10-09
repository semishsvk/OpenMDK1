import pathlib,struct,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
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
 rgb=[tuple(blk[i:i+3]) for i in range(0,len(blk),3)]
 out[hn]={"block_len":len(blk),"rgb_count":len(rgb),"unique_rgb":len(set(rgb)),"exact_gray":sum(r==g==b for r,g,b in rgb),"near_gray_le8":sum(max(r,g,b)-min(r,g,b)<=8 for r,g,b in rgb),"channel_min":[min(c[i] for c in rgb) for i in range(3)],"channel_max":[max(c[i] for c in rgb) for i in range(3)],"first20_rgb":[list(c) for c in rgb[:20]],"last10_rgb":[list(c) for c in rgb[-10:]]}
print(json.dumps({"schema":"OpenMDK.HMO336PaletteHypothesis.v1","status":"HYPOTHESIS","interpretation":"336 bytes as 112 RGB888 triples","hmos":out},indent=2))
