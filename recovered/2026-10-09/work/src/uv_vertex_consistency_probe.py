import struct,pathlib,math,json,collections,hashlib
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}; total_obs=0; same_exact=0; conflicts=0
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]
 geom=struct.unpack_from("<I",h,12)[0]; best=[]
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,dv=struct.unpack_from("<4f",h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,dv)) and .999<n<1.001 and abs(dv)<10000: rr.append(o)
  if len(rr)>len(best): best=rr
 if not best: continue
 p0=best[0]; pn=0
 while p0+(pn+1)*44<len(h):
  o=p0+pn*44; x,y,z,dv=struct.unpack_from("<4f",h,o); n=x*x+y*y+z*z
  if not(all(math.isfinite(v) for v in (x,y,z,dv)) and .999<n<1.001 and abs(dv)<10000): break
  pn+=1
 pend=p0+pn*44; tn=struct.unpack_from("<I",h,pend)[0]; tbase=pend+4
 # key by (vertex index, triangle selector high) to allow material seams
 seen={}; obs=exact=conf=0; seam_vertices=collections.Counter()
 for ti in range(tn):
  rec=h[tbase+ti*36:tbase+(ti+1)*36]
  if len(rec)<36: break
  a,b,c,_=struct.unpack_from("<4H",rec,0); uv=struct.unpack_from("<6f",rec,8); sel=struct.unpack_from("<H",rec,34)[0]//16
  for vi,pair in zip((a,b,c),((uv[0],uv[1]),(uv[2],uv[3]),(uv[4],uv[5]))):
   key=(vi,sel); obs+=1
   if key in seen:
    old=seen[key]
    if pair==old: exact+=1
    else:
     conf+=1
     seam_vertices[vi]+=1
   else: seen[key]=pair
 total_obs+=obs; same_exact+=exact; conflicts+=conf
 out[hn]={"triangle_count":tn,"uv_observations":obs,"repeat_exact":exact,"repeat_conflict":conf,"repeat_consistency":round(exact/(exact+conf),6) if exact+conf else None,"unique_vertex_selector_keys":len(seen),"conflict_vertices":len(seam_vertices)}
print(json.dumps({"schema":"OpenMDK.UVVertexConsistencyProbe.v1","source_sha256":hashlib.sha256(B).hexdigest(),"hmos":out,"totals":{"observations":total_obs,"repeat_exact":same_exact,"repeat_conflict":conflicts,"repeat_consistency":round(same_exact/(same_exact+conflicts),6) if same_exact+conflicts else None},"status":"STRUCTURAL_SUPPORT" if same_exact>conflicts else "INCONCLUSIVE"},indent=2))
