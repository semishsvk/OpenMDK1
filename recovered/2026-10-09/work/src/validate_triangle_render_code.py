import pathlib,struct,math,json,collections,re
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}; totals=collections.Counter()
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode()
 s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
 h=B[s:e]
 g0=struct.unpack_from("<I",h,12)[0]+4
 nc=struct.unpack_from("<I",h,g0)[0]
 names=[h[g0+4+i*10:g0+4+(i+1)*10].split(b"\0")[0].decode("ascii","replace") for i in range(nc)]
 aligned=(g0+4+nc*10+3)&~3
 pc=struct.unpack_from("<I",h,aligned)[0]; toff=aligned+4+pc*44; tn=struct.unpack_from("<I",h,toff)[0]; tb=toff+4
 by=collections.defaultdict(collections.Counter); samples=[]
 for i in range(tn):
  r=h[tb+i*36:tb+(i+1)*36]
  if len(r)<36: break
  f3u=struct.unpack_from("<H",r,6)[0]; f3=struct.unpack_from("<h",r,6)[0]
  gs=struct.unpack_from("<H",r,32)[0]
  name=names[gs] if gs<nc else f"OOR_{gs}"
  by[name][f3]+=1
  kind="ordinary"
  m=re.fullmatch(r"PEN_(\d+)",name)
  if m:
   pen=int(m.group(1)); kind="pen_exact" if f3==-pen else "pen_mismatch"
  elif name.startswith("GLASS"): kind="glass"
  elif name=="NONE": kind="none"
  totals[kind]+=1
  if len(samples)<80 and kind in ("pen_mismatch","glass"):
   samples.append({"tri":i,"name":name,"f3":f3,"f3_u16":f3u})
 out[hn]={"triangles":tn,"by_geometry_name":{k:dict(v.most_common()) for k,v in by.items()},"samples":samples}
print(json.dumps({"schema":"OpenMDK.TriangleRenderCode.v1","signed_f3_hypothesis":"negative values encode PEN/special render codes","totals":dict(totals),"hmos":out},indent=2))
