import pathlib,struct,re,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]
 pal=struct.unpack_from("<I",h,8)[0]; geom=struct.unpack_from("<I",h,12)[0]
 # Find first verified plane record from geom exactly as current decoder does
 best=[]; bestphase=0
 import math
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,dv=struct.unpack_from("<4f",h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,dv)) and .999<n<1.001 and abs(dv)<10000: rr.append(o)
  if len(rr)>len(best): best,bestphase=rr,phase
 first_plane=best[0] if best else geom
 pre=h[geom:first_plane]
 strings=[]
 for m in re.finditer(rb"[A-Z0-9_\.]{2,20}\x00",pre):
  strings.append({"off":m.start(),"text":m.group()[:-1].decode("ascii","replace")})
 # aligned u32 around each string
 annotated=[]
 for st in strings:
  off=st["off"]; base=max(0,off-8); end=min(len(pre),off+32)
  annotated.append({"text":st["text"],"off":off,"hex":pre[base:end].hex(),"u32_before":list(struct.unpack_from("<2I",pre,off-8)) if off>=8 else None})
 out[hn]={"palette_start":pal,"geom_start":geom,"plane_start":first_plane,"pre_plane_len":len(pre),"best_phase":bestphase,"strings":strings,"annotated":annotated,"pre_hex":pre.hex()}
print(json.dumps(out,indent=2))
