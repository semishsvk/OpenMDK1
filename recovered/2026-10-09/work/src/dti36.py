import struct,pathlib,math
D=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI').read_bytes()
starts=[('HMO_1',704),('HMO_2',744),('HMO_3',892),('HMO_4',932),('HMO_5',972),('HMO_6',1048),('HMO_7',1592),('HMO_8',1596),('HMO_9',1888),('HMO_10',2000),('CHMO_1',2040)]
for i,(name,s) in enumerate(starts[:-1]):
 e=starts[i+1][1]; n=(e-s-4)//36
 print('\n',name,'records',n,'prefix',struct.unpack_from('<I',D,s)[0])
 for j in range(n):
  o=s+4+j*36; u=struct.unpack_from('<4I',D,o); f=struct.unpack_from('<5f',D,o+16)
  print(j,u,f)
