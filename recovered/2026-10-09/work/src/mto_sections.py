import struct,pathlib,math,collections
p=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO'); b=p.read_bytes(); cnt=struct.unpack_from('<I',b,20)[0]
for bi in range(cnt):
 o=24+bi*12; name=b[o:o+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',b,o+8)[0]; e=struct.unpack_from('<I',b,24+(bi+1)*12+8)[0] if bi+1<cnt else len(b); h=b[s:e]
 hdr=struct.unpack_from('<5I',h,0); cuts=sorted(set([0,len(h)]+[x for x in hdr if 0<x<len(h)])); print('\n',name,'hdr',hdr,'cuts',cuts)
 for a,z in zip(cuts,cuts[1:]):
  seg=h[a:z]; plausible=0; total=len(seg)//12
  for q in range(0,len(seg)-12,12):
   xyz=struct.unpack_from('<3f',seg,q)
   if all(math.isfinite(v) and abs(v)<10000 for v in xyz) and any(abs(v)>0.001 for v in xyz): plausible+=1
  print(' ',a,z,'bytes',z-a,'float3_plausible',plausible,'/',total)
