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
 pend=p0+pn*44;tn=struct.unpack_from("<I",h,pend)[0];tbase=pend+4; vals=[]
 for i in range(tn):
  if tbase+(i+1)*36>len(h):break
  lo,hi=struct.unpack_from("<2H",h,tbase+i*36+32); vals.append((lo,hi))
 his=[x[1] for x in vals]; idx=[x//16 for x in his if x%16==0]
 out[name]={"triangles":tn,"lo_unique":sorted(set(x[0] for x in vals)),"hi_unique_count":len(set(his)),"hi_minmax":[min(his),max(his)],"all_hi_div16":all(x%16==0 for x in his),"index_unique":sorted(set(idx)),"index_max":max(idx) if idx else None}
print(json.dumps(out,indent=2))
