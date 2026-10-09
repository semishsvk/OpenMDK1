import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); cnt=struct.unpack_from('<I',B,20)[0]
for bi in range(cnt):
 q=24+bi*12; name=B[q:q+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',B,q+8)[0]; e=struct.unpack_from('<I',B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; hdr=struct.unpack_from('<5I',h,0); start=hdr[3]
 best=[]
 for phase in range(44):
  rec=[]
  for o in range(start+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000: rec.append((o,struct.unpack_from('<14H',h,o+16)))
  if len(rec)>len(best): best=rec
 c0=collections.Counter(t[0] for _,t in best); c1=collections.Counter(t[1] for _,t in best); c2=collections.Counter(t[2] for _,t in best); c3=collections.Counter(t[3] for _,t in best)
 print(name,len(best),'field0 FFFF',c0[65535],'field1 FFFF',c1[65535],'field2',c2.most_common(8),'field3 range',min(c3) if c3 else None,max(c3) if c3 else None)
