import pathlib,struct,math,json,collections,hashlib
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}
tot=valid=oor=0
for bi in range(cnt):
 q=24+bi*12
 hn=B[q:q+8].split(b"\0")[0].decode()
 s=struct.unpack_from("<I",B,q+8)[0]
 e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
 h=B[s:e]
 g0=struct.unpack_from("<I",h,12)[0]
 # known plane stream
 best=[]
 for phase in range(44):
  rr=[]
  for o in range(g0+phase,len(h)-44,44):
   x,y,z,dv=struct.unpack_from("<4f",h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,dv)) and .999<n<1.001 and abs(dv)<10000: rr.append(o)
  if len(rr)>len(best): best=rr
 if not best: continue
 first=best[0]
 pc=struct.unpack_from("<I",h,first-4)[0]
 # recover geometry name table immediately before plane count from verified v2 layout
 palette_ptr=struct.unpack_from("<I",h,8)[0]+4
 palette_end=palette_ptr+336
 geom_meta=struct.unpack_from("<I",h,12)[0]+4
 name_count=struct.unpack_from("<I",h,geom_meta)[0]
 names=[]
 for i in range(name_count):
  rec=h[geom_meta+4+i*10:geom_meta+4+(i+1)*10]
  names.append(rec.split(b"\0")[0].decode("ascii","replace"))
 # triangle stream
 plane_start=first
 pend=plane_start+pc*44
 tn=struct.unpack_from("<I",h,pend)[0]
 tbase=pend+4
 hist=collections.Counter(); bad=[]; mapped=collections.Counter()
 for ti in range(tn):
  rec=h[tbase+ti*36:tbase+(ti+1)*36]
  if len(rec)<36: break
  vals=struct.unpack_from("<18H",rec)
  idx=vals[16]
  tot+=1
  hist[idx]+=1
  if idx < name_count:
   valid+=1; mapped[names[idx]]+=1
  else:
   oor+=1
   if len(bad)<12: bad.append({"tri":ti,"field16":idx})
 out[hn]={
  "name_count":name_count,"names":names,"triangles":tn,
  "field16_histogram":dict(sorted(hist.items())),
  "in_range":sum(v for k,v in hist.items() if k<name_count),
  "out_of_range":sum(v for k,v in hist.items() if k>=name_count),
  "mapped_name_histogram":dict(mapped),
  "bad_samples":bad
 }
print(json.dumps({
 "schema":"OpenMDK.TriangleGeometryNameSelectorProbe.v1",
 "source_sha256":hashlib.sha256(B).hexdigest(),
 "triangles_total":tot,"field16_in_range":valid,"field16_out_of_range":oor,
 "hmos":out,
 "status":"STRUCTURAL_PASS" if tot==valid else "MIXED"
},indent=2))
