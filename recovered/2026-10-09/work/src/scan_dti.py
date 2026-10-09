import struct,pathlib
p=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI'); d=p.read_bytes()
print('size',len(d),'header',struct.unpack_from('<10I',d,0))
# dump first 10 named HMO records from known directory region around 0x194
for o in range(0x194,0x274,16):
 raw=d[o:o+16]; print(hex(o),raw[:8].split(b'\0')[0],struct.unpack_from('<II',raw,8))
# discover aligned offsets pointing inside file, frequency by target neighborhood
ptrs=[]
for o in range(0,len(d)-4,4):
 v=struct.unpack_from('<I',d,o)[0]
 if 0<v<len(d) and v%4==0: ptrs.append((o,v))
print('aligned ptr-like',len(ptrs)); print(ptrs[:100])
