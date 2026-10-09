import pathlib,struct,math,json,collections
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
tot=collections.Counter(); combos=collections.Counter(); by_hmo={}
samples=[]
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode()
 s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
 h=B[s:e]; mc=struct.unpack_from("<I",h,36)[0]
 mats=[]
 for mi in range(mc):
  r=40+mi*24; name=h[r:r+20].split(b"\0")[0].decode("ascii","replace"); rel=struct.unpack_from("<I",h,r+20)[0]; a=20+rel
  w,hh=struct.unpack_from("<HH",h,a); mats.append((name,w,hh))
 g0=struct.unpack_from("<I",h,12)[0]+4; nc=struct.unpack_from("<I",h,g0)[0]; aligned=(g0+4+nc*10+3)&~3
 pc=struct.unpack_from("<I",h,aligned)[0]; toff=aligned+4+pc*44; tn=struct.unpack_from("<I",h,toff)[0]; tb=toff+4
 st=collections.Counter()
 for i in range(tn):
  r=h[tb+i*36:tb+(i+1)*36]
  f3=struct.unpack_from("<h",r,6)[0]
  if f3<=0 or mc==0: continue
  raw=struct.unpack_from("<H",r,34)[0]; sel=raw//16; ordv=sel%mc; quot=sel//mc
  uv=struct.unpack_from("<6f",r,8); mx=max(abs(x) for x in uv)
  mode="unit" if mx<=2 else "pixelish" if mx<=2048 else "large"
  rels={
   "f3_eq_ord":f3==ordv,
   "f3_eq_ord1":f3==ordv+1,
   "f3_eq_q":f3==quot,
   "f3_eq_q1":f3==quot+1,
   "f3_eq_sel":f3==sel,
   "f3_eq_sel1":f3==sel+1
  }
  for k,v in rels.items():
   if v:tot[k]+=1
  tot["positive"]+=1; tot["mode_"+mode]+=1
  key=(hn,f3,ordv,quot,mode); combos[key]+=1
  st[(f3,ordv,quot,mode)]+=1
  if len(samples)<100:
   samples.append({"hmo":hn,"tri":i,"f3":f3,"selector_index":sel,"material_ordinal":ordv,"quotient":quot,"material":mats[ordv],"mode":mode,"uv":list(uv)})
 by_hmo[hn]=[{"f3":k[0],"ordinal":k[1],"quotient":k[2],"mode":k[3],"count":v} for k,v in st.most_common()]
print(json.dumps({"schema":"OpenMDK.PositiveF3TextureMapping.v1","totals":dict(tot),"hmos":by_hmo,"samples":samples},indent=2))
