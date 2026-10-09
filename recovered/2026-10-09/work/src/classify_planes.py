import struct,pathlib,math,collections,json
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); cnt=struct.unpack_from('<I',B,20)[0]; report={}
for bi in range(cnt):
 q=24+bi*12; name=B[q:q+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',B,q+8)[0]; e=struct.unpack_from('<I',B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; start=struct.unpack_from('<I',h,12)[0]
 best=None
 for phase in range(44):
  rec=[]
  for o in range(start+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000:
    tail=struct.unpack_from('<14H',h,o+16); rec.append((o,tail))
  if best is None or len(rec)>len(best[1]): best=(phase,rec)
 phase,recs=best; flags=collections.Counter((r[1][0],r[1][1],r[1][2],r[1][3]) for r in recs)
 ids=[r[1][0] for r in recs]
 report[name]={'phase':phase,'records':len(recs),'id_min':min(ids) if ids else None,'id_max':max(ids) if ids else None,'top_flags':[(list(k),v) for k,v in flags.most_common(8)]}
 print(name,'phase',phase,'records',len(recs),'id',report[name]['id_min'],report[name]['id_max'],'flags',flags.most_common(5))
pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1\evidence\plane_record_report.json').write_text(json.dumps(report,indent=2))
