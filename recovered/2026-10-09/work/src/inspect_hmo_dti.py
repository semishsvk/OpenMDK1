import struct,pathlib,math
D=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI').read_bytes()
for name,p in [('HMO_1',704),('HMO_2',744),('HMO_3',892),('HMO_4',932),('HMO_5',972),('HMO_6',1048),('HMO_7',1592),('HMO_8',1596),('HMO_9',1888),('HMO_10',2000)]:
 print('\n',name,hex(p))
 # interpret first up to 40 bytes as u32 and float
 for o in range(p,min(p+76,len(D)),4):
  u=struct.unpack_from('<I',D,o)[0]; f=struct.unpack_from('<f',D,o)[0]
  print(hex(o),u, f if math.isfinite(f) else None)
