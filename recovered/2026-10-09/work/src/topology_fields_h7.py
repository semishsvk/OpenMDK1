import struct,pathlib,math,collections
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); s=5365624; h=B[s:s+52780]; start=400; phase=32
recs=[]
for o in range(start+phase,len(h)-44,44):
 x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
 if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000: recs.append((o,struct.unpack_from('<14H',h,o+16)))
print('records',len(recs))
for k in range(14):
 vals=[t[k] for _,t in recs]; non=[v for v in vals if v!=65535]; mono=sum(b>=a for a,b in zip(non,non[1:]))/max(1,len(non)-1); print(k,'ffff',vals.count(65535),'minmax', (min(non),max(non)) if non else None,'uniq',len(set(non)),'mono',round(mono,3),'top',collections.Counter(vals).most_common(6))
print('first20')
for o,t in recs[:20]: print(hex(o),t)
