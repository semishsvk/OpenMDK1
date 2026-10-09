import struct,pathlib,math,collections
p=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO'); b=p.read_bytes(); cnt=struct.unpack_from('<I',b,20)[0]
for bi in range(cnt):
 o=24+bi*12; name=b[o:o+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',b,o+8)[0]; e=struct.unpack_from('<I',b,24+(bi+1)*12+8)[0] if bi+1<cnt else len(b); h=b[s:e]
 # find counts 118 and candidate polygon tables: count followed by records with 3 plane floats + small integer-ish fields
 hits=[]
 for q in range(0,len(h)-8,4):
  if struct.unpack_from('<I',h,q)[0]==118: hits.append(q)
 print(name,'118hits',hits[:20])
 if name=='HMO_6':
  for q in hits:
   print('H6 hit',hex(q),'context',h[max(0,q-48):q+80].hex())
