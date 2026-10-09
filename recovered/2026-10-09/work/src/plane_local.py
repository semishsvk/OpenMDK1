import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]
# plane begins at 0x1dc, next at 0x208 => record start appears 0x1b0, plane offset +44? derive actual record stride from plane hits around there
for o in range(0x1b0,0x400,4):
 x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
 if .999<n<1.001 and all(math.isfinite(v) for v in (x,y,z,d)):
  print(hex(o),x,y,z,d,'prev44',h[o-44:o].hex())
