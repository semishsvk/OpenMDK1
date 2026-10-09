import struct,pathlib,math,collections,json
D=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI').read_bytes()
# directory gives start offsets; use next start as boundary. Decode candidate 40-byte records observed at HMO1..6.
starts=[('HMO_1',704),('HMO_2',744),('HMO_3',892),('HMO_4',932),('HMO_5',972),('HMO_6',1048),('HMO_7',1592),('HMO_8',1596),('HMO_9',1888),('HMO_10',2000),('CHMO_1',2040)]
for i,(name,s) in enumerate(starts[:-1]):
 e=starts[i+1][1]; size=e-s; print(name,'range',s,e,'bytes',size)
 # test 40-byte records: first 4 u32 + 6 floats? identify records whose final 6 dwords form plausible coords
 for stride in [36,40]:
  n=size//stride; good=0
  for j in range(n):
   o=s+j*stride
   vals=struct.unpack_from('<'+('I'*(stride//4)),D,o)
   fs=[struct.unpack('<f',struct.pack('<I',x))[0] for x in vals]
   if sum(math.isfinite(x) and abs(x)<10000 for x in fs)>=4: good+=1
  print(' stride',stride,'n',n,'good',good,'rem',size%stride)
