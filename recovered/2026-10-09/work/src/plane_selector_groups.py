import struct,pathlib,math,collections,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes();cnt=struct.unpack_from("<I",B,20)[0];out={}
for bi in range(cnt):
 q=24+bi*12;name=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];mc=struct.unpack_from("<I",h,36)[0];geom=struct.unpack_from("<I",h,12)[0];best=[]
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from("<4f",h,o);n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000:rr.append(o)
  if len(rr)>len(best):best=rr
 if not best:continue
 p0=best[0];planes=[];pn=0
 while p0+(pn+1)*44<len(h):
  o=p0+pn*44;x,y,z,d=struct.unpack_from("<4f",h,o);n=x*x+y*y+z*z
  if not(all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000):break
  tail=struct.unpack_from("<14H",h,o+16);planes.append((tail[2],tail[3]));pn+=1
 pend=p0+pn*44;tn=struct.unpack_from("<I",h,pend)[0];tbase=pend+4
 sels=[struct.unpack_from("<H",h,tbase+i*36+34)[0]//16 for i in range(tn)]
 groups=[]
 for pi,(count,first) in enumerate(planes):
  if count and first<tn:
   vals=sels[first:min(first+count,tn)]
   if vals: groups.append((pi,count,first,collections.Counter(vals).most_common(4)))
 out[name]={"material_count":mc,"plane_count":pn,"triangle_count":tn,"planes_with_triangles":len(groups),"sample_plane_selector_groups":groups[:30]}
print(json.dumps(out,indent=2))
