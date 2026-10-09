import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); cnt=struct.unpack_from('<I',B,20)[0]
for bi in range(cnt):
 q=24+bi*12; name=B[q:q+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',B,q+8)[0]; e=struct.unpack_from('<I',B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; geom=struct.unpack_from('<I',h,12)[0]
 best=[]
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000: rr.append(o)
  if len(rr)>len(best):best=rr
 p0=best[0]; pn=0
 while p0+(pn+1)*44<len(h):
  o=p0+pn*44; x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
  if not(all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000):break
  pn+=1
 pend=p0+pn*44; tn=struct.unpack_from('<I',h,pend)[0]; tb=pend+4
 flags=collections.Counter(); tail16=collections.Counter(); leafcats=collections.Counter(); leaftris=0
 for pi in range(pn):
  t=struct.unpack_from('<14H',h,p0+pi*44+16); count,first=t[2],t[3]; leaf=(t[0]==65535 or t[1]==65535)
  for ti in range(first,first+count):
   a,b,c,fl,*rest=struct.unpack_from('<18H',h,tb+ti*36); flags[fl]+=1; tail16[(rest[12],rest[13])]+=1
   if leaf: leaftris+=1; leafcats[(fl,rest[12],rest[13])]+=1
 print(name,'T',tn,'flags',flags.most_common(8),'tail',tail16.most_common(8),'leafMapped',leaftris,'leafcats',leafcats.most_common(8))
