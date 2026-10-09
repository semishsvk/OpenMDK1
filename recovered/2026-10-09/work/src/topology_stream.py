import struct,pathlib,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]; base=0x3db0
# Inspect u16 stream: split at values >= 0xff00; report segment lengths/content patterns.
us=list(struct.unpack_from('<'+str((len(h)-base)//2)+'H',h,base))
segs=[]; cur=[]
for i,v in enumerate(us):
 cur.append(v)
 if v>=0xff00:
  segs.append(cur); cur=[]
print('segments',len(segs),'first20')
for s in segs[:20]: print(len(s),s)
print('lengths',collections.Counter(map(len,segs)).most_common(20)); print('sentinels',collections.Counter(s[-1] for s in segs).most_common(20))
# cumulative byte positions for first 875 sentinel-terminated entries
pos=base
for i,s in enumerate(segs[:875]): pos += 2*len(s)
print('end875',hex(pos),'next_u32',struct.unpack_from('<8I',h,pos))
