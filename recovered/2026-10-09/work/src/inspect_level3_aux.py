import struct,pathlib,re,math,collections
for fn in ['LEVEL3.CMI','LEVEL3S.SNI','LEVEL3O.SNI','LEVEL3S.MTI']:
 p=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3')/fn; d=p.read_bytes(); print('\n###',fn,len(d)); print('u32[0:16]',struct.unpack_from('<16I',d,0));
 ss=[]
 for m in re.finditer(rb'[\x20-\x7e]{4,24}\x00',d[:min(len(d),8192)]): ss.append((m.start(),m.group()[:-1].decode('ascii','replace')))
 print('strings',ss[:40])
