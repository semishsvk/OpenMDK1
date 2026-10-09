import struct,pathlib,math,json,hashlib
src=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO")
B=src.read_bytes(); cnt=struct.unpack_from("<I",B,20)[0]; BASE=20
out={"schema":"OpenMDK.Level3TriangleTextureBinding.v1","source_sha256":hashlib.sha256(B).hexdigest(),"parts":[]}
tot=bound=special=bad_sel=bad_payload=bad_uv=0
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]
 n=struct.unpack_from("<I",h,36)[0]
 mats=[]
 for mi in range(n):
  name=h[40+mi*24:40+mi*24+20].split(b"\0")[0].decode("ascii","replace"); rel=struct.unpack_from("<I",h,40+mi*24+20)[0]; a=BASE+rel; w,hh=struct.unpack_from("<HH",h,a); z=a+4+w*hh
  mats.append({"ordinal":mi,"name":name,"w":w,"h":hh,"payload_ok":z<=len(h),"texel_sha256":hashlib.sha256(h[a+4:z]).hexdigest() if z<=len(h) else None})
 geom=struct.unpack_from("<I",h,12)[0]; best=[]
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from("<4f",h,o); nn=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<nn<1.001 and abs(d)<10000: rr.append(o)
  if len(rr)>len(best): best=rr
 if not best:
  out["parts"].append({"hmo":hn,"material_count":n,"status":"BLOCKED_NO_PLANE_STREAM"}); continue
 p0=best[0]; pn=0
 while p0+(pn+1)*44<len(h):
  o=p0+pn*44; x,y,z,d=struct.unpack_from("<4f",h,o); nn=x*x+y*y+z*z
  if not(all(math.isfinite(v) for v in (x,y,z,d)) and .999<nn<1.001 and abs(d)<10000): break
  pn+=1
 pend=p0+pn*44; tn=struct.unpack_from("<I",h,pend)[0]; tbase=pend+4
 stats={"hmo":hn,"material_count":n,"triangles":tn,"planes":pn,"bound":0,"special_no_material_table":0,"selector_not_div16":0,"payload_fail":0,"uv_nonfinite":0,"material_histogram":{}}
 for ti in range(tn):
  rec=h[tbase+ti*36:tbase+(ti+1)*36]
  if len(rec)<36: break
  tot+=1; raw=struct.unpack_from("<H",rec,34)[0]; uv=struct.unpack_from("<6f",rec,8)
  if raw%16: bad_sel+=1; stats["selector_not_div16"]+=1
  if not all(math.isfinite(v) for v in uv): bad_uv+=1; stats["uv_nonfinite"]+=1
  if n==0:
   special+=1; stats["special_no_material_table"]+=1; continue
  idx=raw//16; ordv=idx%n; mat=mats[ordv]
  if not mat["payload_ok"]: bad_payload+=1; stats["payload_fail"]+=1; continue
  bound+=1; stats["bound"]+=1; stats["material_histogram"][mat["name"]]=stats["material_histogram"].get(mat["name"],0)+1
 out["parts"].append(stats)
out.update({"triangles_total":tot,"triangles_bound":bound,"triangles_special_no_material_table":special,"selector_not_div16":bad_sel,"payload_fail":bad_payload,"uv_nonfinite":bad_uv,"status":"STRUCTURAL_PASS" if bound+special==tot and bad_sel==0 and bad_payload==0 and bad_uv==0 else "FAIL","claim":"triangle -> selector_index -> HMO material ordinal -> deterministic indexed8 payload and finite 6-float UV tuple; color lookup, UV scale/wrap semantics, HMO7 semantics and original-runtime fidelity remain separate gates"})
print(json.dumps(out,indent=2))
