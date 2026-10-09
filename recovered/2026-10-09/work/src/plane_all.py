import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); cnt=struct.unpack_from('<I',B,20)[0]
for bi in range(cnt):
 q=24+bi*12; name=B[q:q+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',B,q+8)[0]; e=struct.unpack_from('<I',B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; hdr=struct.unpack_from('<5I',h,0); start=hdr[3] if hdr[3]<len(h) else 0
 hits=[]
 for o in range(start,len(h)-16,4):
  x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
  if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000: hits.append(o)
 # phase score for 44-byte records
 phases=[]
 for phase in range(44):
  hs=[o for o in hits if (o-phase)%44==0]; phases.append((len(hs),phase))
 best=max(phases)
 print(name,'scan_from',start,'unitplanes',len(hits),'best44',best)
