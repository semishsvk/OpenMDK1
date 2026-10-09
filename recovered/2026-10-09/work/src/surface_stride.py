import struct,pathlib,collections,math
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]; base=0x3db0; n=875
# score strides by repeated structural fields: first u16 small, selected u16 small/ffff, zeros
for stride in range(8,65,4):
 if base+n*stride>len(h): continue
 score=0; samples=[]
 for i in range(n):
  r=h[base+i*stride:base+(i+1)*stride]; us=struct.unpack_from('<'+'H'*(stride//2),r)
  small=sum(v<4096 or v>=65500 for v in us)/len(us); score+=small
 print('stride',stride,'end',hex(base+n*stride),'avgsmall',round(score/n,3))
# inspect likely 32-byte records first 12
stride=32
for i in range(12): print(i,struct.unpack_from('<16H',h,base+i*stride))
print('after32 count/u32',hex(base+n*32),struct.unpack_from('<16I',h,base+n*32))
