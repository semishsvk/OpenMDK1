import struct,pathlib,collections,math
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]; base=0x3db0
# Hypothesis: 875 fixed 36-byte topology records; observed sentinel at last u16 and leading zeros arise from this.
for stride in [34,36,38]:
 end=base+875*stride; print('stride',stride,'end',hex(end),'remaining',len(h)-end)
 if end<len(h)-32: print('u32',struct.unpack_from('<8I',h,end))
# 36-byte structural distributions
stride=36
cols=[collections.Counter() for _ in range(18)]
for i in range(875):
 us=struct.unpack_from('<18H',h,base+i*stride)
 for j,v in enumerate(us): cols[j][v]+=1
for j,c in enumerate(cols): print(j,c.most_common(8),'uniq',len(c))
