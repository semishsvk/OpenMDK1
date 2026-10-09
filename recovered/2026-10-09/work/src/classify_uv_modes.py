import pathlib,struct,math,json,collections
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}
global_stats=collections.Counter()
for bi in range(cnt):
 q=24+bi*12
 hn=B[q:q+8].split(b"\0")[0].decode()
 s=struct.unpack_from("<I",B,q+8)[0]
 e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
 h=B[s:e]
 mc=struct.unpack_from("<I",h,36)[0]
 mats=[]
 for mi in range(mc):
  r=40+mi*24
  name=h[r:r+20].split(b"\0")[0].decode("ascii","replace")
  rel=struct.unpack_from("<I",h,r+20)[0]
  a=20+rel
  w,hh=struct.unpack_from("<HH",h,a)
  mats.append((name,w,hh))
 g0=struct.unpack_from("<I",h,12)[0]+4
 name_count=struct.unpack_from("<I",h,g0)[0]
 names=[h[g0+4+i*10:g0+4+(i+1)*10].split(b"\0")[0].decode("ascii","replace") for i in range(name_count)]
 aligned=(g0+4+name_count*10+3)&~3
 pc=struct.unpack_from("<I",h,aligned)[0]
 tcount_off=aligned+4+pc*44
 tn=struct.unpack_from("<I",h,tcount_off)[0]
 tbase=tcount_off+4
 stat=collections.Counter(); by_f3=collections.Counter(); by_gname=collections.Counter(); by_q=collections.Counter(); samples=[]
 for i in range(tn):
  rec=h[tbase+i*36:tbase+(i+1)*36]
  if len(rec)<36: break
  v0,v1,v2,f3=struct.unpack_from("<4H",rec,0)
  uv=struct.unpack_from("<6f",rec,8)
  gsel=struct.unpack_from("<H",rec,32)[0]
  raw=struct.unpack_from("<H",rec,34)[0]
  sel=raw//16
  ordv=sel%mc if mc else None
  quot=sel//mc if mc else None
  finite=all(math.isfinite(x) for x in uv)
  mx=max(abs(x) for x in uv) if finite else float("inf")
  if not finite: mode="nonfinite"
  elif all(x==0 for x in uv): mode="zero"
  elif mx<=2.0: mode="unit"
  elif mx<=2048.0: mode="pixelish"
  else: mode="large"
  stat[mode]+=1; global_stats[mode]+=1
  by_f3[(str(f3),mode)]+=1
  gn=names[gsel] if gsel<len(names) else f"OOR_{gsel}"
  by_gname[(gn,mode)]+=1
  by_q[(str(quot),mode)]+=1
  if len(samples)<40 and mode in ("unit","pixelish","large"):
   mat=mats[ordv] if ordv is not None and ordv<len(mats) else None
   samples.append({"tri":i,"mode":mode,"f3":f3,"geometry_name":gn,"raw_selector":raw,"selector_index":sel,"quotient":quot,"material":mat,"uv":list(uv)})
 def nest(counter):
  z={}
  for (k,m),v in counter.items(): z.setdefault(k,{})[m]=v
  return z
 out[hn]={"material_count":mc,"triangles":tn,"modes":dict(stat),"by_f3":nest(by_f3),"by_geometry_name":nest(by_gname),"by_selector_quotient":nest(by_q),"samples":samples}
print(json.dumps({"schema":"OpenMDK.UVModeClassification.v1","thresholds":{"unit":"maxabs<=2","pixelish":"2<maxabs<=2048","large":"maxabs>2048"},"global_modes":dict(global_stats),"hmos":out},indent=2))
