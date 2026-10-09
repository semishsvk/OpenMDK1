import pathlib,collections,json,math
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3");out={}
for p in root.iterdir():
 if not p.is_file():continue
 b=p.read_bytes();hits=[]
 for o in range(0,max(0,len(b)-768),16):
  d=b[o:o+768];low=sum(x<=63 for x in d)/768;u=len(set(d))
  if low>=.98 and u>=32:
   c=collections.Counter(d);ent=-sum((v/768)*math.log2(v/768) for v in c.values());hits.append((round(low,3),round(ent,3),u,o))
 hits=sorted(hits,reverse=True)[:20];out[p.name]=[{"offset":o,"low63_ratio":lo,"entropy":en,"unique":u} for lo,en,u,o in hits]
print(json.dumps(out,indent=2))
