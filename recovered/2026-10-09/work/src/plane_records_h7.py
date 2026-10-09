import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); s=5365624; h=B[s:s+52780]
# HMO7 dominant phase 36; inspect records whose plane begins at rec+? find normalized quadruple position within 44-byte record
phase=36
for base in range(phase,phase+44*12,44):
 vals=[]
 for j in range(11):
  u=struct.unpack_from('<I',h,base+j*4)[0]; f=struct.unpack_from('<f',h,base+j*4)[0]; vals.append((u,f))
 print(hex(base), ' '.join(f'{u:08x}/{f:.4g}' for u,f in vals))
