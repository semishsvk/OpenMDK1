import struct,pathlib,math,collections,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;hn=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];n=struct.unpack_from("<I",h,36)[0]
 if not n:continue
 names=[h[40+i*24:40+(i+1)*24].split(b"\0")[0].decode("ascii","replace") for i in range(n)]
 geom=struct.unpack_from("<I",h,12)[0];best=[]
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from("<4f",h,o);nn=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<nn<1.001 and abs(d)<10000:rr.append(o)
  if len(rr)>len(best):best=rr
 if not best:continue
 p0=best[0];pn=0
 while p0+(pn+1)*44<len(h):
  o=p0+pn*44;x,y,z,d=struct.unpack_from("<4f",h,o);nn=x*x+y*y+z*z
  if not(all(math.isfinite(v) for v in (x,y,z,d)) and .999<nn<1.001 and abs(d)<10000):break
  pn+=1
 pend=p0+pn*44;tn=struct.unpack_from("<I",h,pend)[0];tbase=pend+4;stats=[{"name":names[i],"tri":0,"uv_nonzero":0,"selectors":collections.Counter()} for i in range(n)]
 for i in range(tn):
  if tbase+(i+1)*36>len(h):break
  rec=h[tbase+i*36:tbase+(i+1)*36]; sel=struct.unpack_from("<H",rec,34)[0]//16; ord=sel%n; uv=struct.unpack_from("<6f",rec,8); st=stats[ord];st["tri"]+=1;st["uv_nonzero"]+=int(any(v!=0 for v in uv));st["selectors"][sel]+=1
 for st in stats:st["uv_ratio"]=round(st["uv_nonzero"]/st["tri"],4) if st["tri"] else None;st["selectors"]=dict(st["selectors"])
 out[hn]=stats
print(json.dumps(out,indent=2))
