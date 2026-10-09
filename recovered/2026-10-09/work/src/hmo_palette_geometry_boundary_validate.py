import pathlib,struct,json,math
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
allowed=set(((i<<3)|(i>>2)) for i in range(32))
out={}
all_ok=True
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]
 p0=struct.unpack_from("<I",h,8)[0]; g0=struct.unpack_from("<I",h,12)[0]
 # Get independently known plane count by phase scan
 best=[]; known_plane_count=None
 for phase in range(44):
  rr=[]
  for o in range(g0+phase,len(h)-44,44):
   x,y,z,dv=struct.unpack_from("<4f",h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,dv)) and .999<n<1.001 and abs(dv)<10000: rr.append(o)
  if len(rr)>len(best): best=rr
 if best:
  first=best[0]
  # known count is u32 just before first plane
  known_plane_count=struct.unpack_from("<I",h,first-4)[0]
 candidates=[]
 for delta in range(0,33):
  ps=p0+delta; pe=ps+336
  gs=g0+delta
  if pe>len(h) or gs+4>len(h): continue
  pal=h[ps:pe]
  if len(pal)!=336 or any(v not in allowed for v in pal): continue
  c=struct.unpack_from("<I",h,gs)[0]
  if c>100: continue
  names_start=gs+4; names_end=names_start+c*10
  if names_end+4>len(h): continue
  names=[]; valid=True
  for i in range(c):
   rec=h[names_start+i*10:names_start+(i+1)*10]
   raw=rec.split(b"\0")[0]
   try: name=raw.decode("ascii")
   except: valid=False; break
   if not name or any(ord(ch)<32 or ord(ch)>126 for ch in name): valid=False; break
   names.append(name)
  if not valid: continue
  pc=struct.unpack_from("<I",h,names_end)[0]
  candidates.append({"delta":delta,"palette_start":ps,"palette_end":pe,"name_count":c,"names":names,"plane_count":pc,"matches_known_plane_count":pc==known_plane_count})
 good=[x for x in candidates if x["matches_known_plane_count"]]
 ok=len(good)==1
 all_ok &= ok
 out[hn]={"nominal_palette_ptr":p0,"nominal_geom_ptr":g0,"known_plane_count":known_plane_count,"candidates":candidates,"selected":good[0] if len(good)==1 else None,"status":"PASS" if ok else "FAIL"}
print(json.dumps({"schema":"OpenMDK.HMOPaletteGeometryBoundary.v1","palette_layout":"112 x RGB888 values constrained to RGB555-expanded channel values","hmos":out,"status":"STRUCTURAL_PASS" if all_ok else "FAIL"},indent=2))
