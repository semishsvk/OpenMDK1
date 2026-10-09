import pathlib,struct,json,math,hashlib
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}
all_ok=True
for bi in range(cnt):
 q=24+bi*12
 hn=B[q:q+8].split(b"\0")[0].decode()
 s=struct.unpack_from("<I",B,q+8)[0]
 e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
 h=B[s:e]
 p0=struct.unpack_from("<I",h,8)[0]
 g0=struct.unpack_from("<I",h,12)[0]
 # Independently determine verified plane stream/count
 best=[]
 for phase in range(44):
  rr=[]
  for o in range(g0+phase,len(h)-44,44):
   x,y,z,dv=struct.unpack_from("<4f",h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,dv)) and .999<n<1.001 and abs(dv)<10000: rr.append(o)
  if len(rr)>len(best): best=rr
 first_plane=best[0] if best else None
 known=struct.unpack_from("<I",h,first_plane-4)[0] if first_plane else None
 # Fixed observed boundary correction
 delta=4
 palette=h[p0+delta:p0+delta+336]
 gs=g0+delta
 c=struct.unpack_from("<I",h,gs)[0] if gs+4<=len(h) else 0xffffffff
 names=[]
 names_ok=True
 if c<=100:
  for i in range(c):
   rec=h[gs+4+i*10:gs+4+(i+1)*10]
   raw=rec.split(b"\0")[0]
   try: name=raw.decode("ascii")
   except: names_ok=False; break
   if not name or len(rec)!=10: names_ok=False; break
   names.append(name)
 else:
  names_ok=False
 names_end=gs+4+c*10 if c<=100 else gs
 aligned=(names_end+3)&~3
 pc=struct.unpack_from("<I",h,aligned)[0] if aligned+4<=len(h) else None
 computed_plane_start=aligned+4
 ok=(len(palette)==336 and names_ok and pc==known and computed_plane_start==first_plane)
 all_ok &= ok
 rgb=[list(palette[i:i+3]) for i in range(0,336,3)]
 out[hn]={
  "palette_start":p0+delta,"palette_end":p0+delta+336,"palette_sha256":hashlib.sha256(palette).hexdigest(),
  "rgb_count":len(rgb),"name_count":c,"names":names,"names_end":names_end,"aligned_plane_count_offset":aligned,
  "plane_count":pc,"known_plane_count":known,"computed_plane_start":computed_plane_start,"known_plane_start":first_plane,
  "status":"PASS" if ok else "FAIL"
 }
print(json.dumps({"schema":"OpenMDK.HMOPaletteGeometryBoundary.v2","palette_boundary_delta":4,"palette_layout":"112 x RGB888","geometry_layout":"u32 name_count + name_count*10 ASCII records + align4 + u32 plane_count","hmos":out,"status":"STRUCTURAL_PASS" if all_ok else "FAIL"},indent=2))
