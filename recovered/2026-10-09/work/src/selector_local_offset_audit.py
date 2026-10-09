import struct,pathlib,math,collections,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;name=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];geom=struct.unpack_from("<I",h,12)[0];best=[]
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from("<4f",h,o);n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000:rr.append(o)
  if len(rr)>len(best):best=rr
 if not best:continue
 p0=best[0];pn=0
 while p0+(pn+1)*44<len(h):
  o=p0+pn*44;x,y,z,d=struct.unpack_from("<4f",h,o);n=x*x+y*y+z*z
  if not(all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000):break
  pn+=1
 pend=p0+pn*44;tn=struct.unpack_from("<I",h,pend)[0];tbase=pend+4;his=[]
 for i in range(tn):
  if tbase+(i+1)*36>len(h):break
  his.append(struct.unpack_from("<H",h,tbase+i*36+34)[0])
 uniq=sorted(set(his)); samples=[]
 for x in uniq[:20]:
  samples.append({"off":x,"in_block":x+16<=len(h),"bytes":h[x:x+16].hex() if x+16<=len(h) else None})
 out[name]={"block_size":len(h),"max_selector":max(uniq),"all_local_in_range":all(x+16<=len(h) for x in uniq),"samples":samples}
print(json.dumps(out,indent=2))
