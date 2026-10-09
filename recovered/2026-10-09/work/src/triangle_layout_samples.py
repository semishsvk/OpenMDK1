import struct,pathlib,math,json
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
 pend=p0+pn*44;tn=struct.unpack_from("<I",h,pend)[0];tbase=pend+4
 samples=[]
 for i in range(min(tn,12)):
  rec=h[tbase+i*36:tbase+(i+1)*36]; a,b,c,f=struct.unpack_from("<4H",rec); dw=struct.unpack_from("<7I",rec,8); fl=struct.unpack_from("<6f",rec,8); last=struct.unpack_from("<2H",rec,32)
  samples.append({"tri":i,"v":[a,b,c],"f3":f,"dwords":list(dw),"floats6":list(fl),"last2":list(last)})
 out[name]=samples
print(json.dumps(out,indent=2))
