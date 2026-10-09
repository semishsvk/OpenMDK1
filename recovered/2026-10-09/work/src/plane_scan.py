import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]
# find all offsets where 4 consecutive floats look like normalized plane (norm ~=1, finite d)
hits=[]
for o in range(400,len(h)-16,4):
 x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
 if all(math.isfinite(v) for v in (x,y,z,d)) and .97<n<1.03 and abs(d)<10000: hits.append(o)
print('hits',len(hits)); print('first',hits[:80]); print('diffs',collections.Counter(b-a for a,b in zip(hits,hits[1:])).most_common(20))
# clusters by common 44/48/52/56-ish spacing
clusters=[]; cur=[]
for o in hits:
 if not cur or o-cur[-1] <= 80: cur.append(o)
 else:
  if len(cur)>=3: clusters.append(cur)
  cur=[o]
if len(cur)>=3:clusters.append(cur)
for c in clusters[:20]: print('cluster',hex(c[0]),hex(c[-1]),len(c),'diffs',collections.Counter(b-a for a,b in zip(c,c[1:])).most_common(5))
