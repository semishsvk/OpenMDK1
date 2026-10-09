import struct,pathlib,collections,math
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]
# plane run known: first plane 0x1b0, 349 records *44 => end 0x3d9c. inspect following region as u16/u32 and look for arrays around 875 elems.
end=0x1b0+349*44; print('plane_end',hex(end),'remaining',len(h)-end)
for base in [end,end+4,end+8,end+16,end+32]:
 print('\nbase',hex(base),'u32',struct.unpack_from('<16I',h,base),'u16',struct.unpack_from('<32H',h,base))
# candidate headers nearby: small integers <=5000
for o in range(end,min(len(h)-4,end+512),4):
 u=struct.unpack_from('<I',h,o)[0]
 if u<5000: print(hex(o),u)
