import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]
# field3 is monotonic unique 0..874-ish: likely cumulative index offset. Analyze delta vs field2.
rec=[]
for o in range(432,len(h)-44,44):
 x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
 if .999<n<1.001 and all(math.isfinite(v) for v in (x,y,z,d)):
  t=struct.unpack_from('<14H',h,o+16); rec.append((o,t))
print('n',len(rec))
for i,(o,t) in enumerate(rec[:80]):
 nxt=rec[i+1][1][3] if i+1<len(rec) else None; delta=(nxt-t[3]) if nxt is not None else None
 print(i,hex(o),'id',t[0],'link',t[1],'count',t[2],'off',t[3],'delta',delta)
print('delta==count',sum(1 for i in range(len(rec)-1) if rec[i+1][1][3]-rec[i][1][3]==rec[i][1][2]),'of',len(rec)-1)
