import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); cnt=struct.unpack_from('<I',B,20)[0]
for bi in range(cnt):
 q=24+bi*12; name=B[q:q+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',B,q+8)[0]; e=struct.unpack_from('<I',B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; start=struct.unpack_from('<I',h,12)[0]
 best=[]
 for phase in range(44):
  rec=[]
  for o in range(start+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000: rec.append(struct.unpack_from('<14H',h,o+16))
  if len(rec)>len(best):best=rec
 for fld in [0,1]:
  leaf=[t for t in best if t[fld]==65535]
  print(name,'f',fld,'leaf',len(leaf),'poly?',collections.Counter(t[2] for t in leaf).most_common(10),'f3',collections.Counter(t[3] for t in leaf).most_common(5))
