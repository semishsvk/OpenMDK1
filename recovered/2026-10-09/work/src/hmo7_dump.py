import struct,pathlib,math
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); s=5365624; e=5418404; h=B[s:e]
for base in [0,32,48,64,400]:
 print('\nBASE',base,hex(base))
 for o in range(base,min(base+256,len(h)),4):
  raw=h[o:o+4]; u=struct.unpack('<I',raw)[0]; f=struct.unpack('<f',raw)[0]; asc=''.join(chr(x) if 32<=x<127 else '.' for x in raw)
  print(f'{o:06x} {u:10d} {f: .7g} {asc}')
