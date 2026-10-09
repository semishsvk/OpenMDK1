import pathlib,collections,math,json,hashlib,heapq
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3")
files=[root/"LEVEL3S.MTI",root/"LEVEL3.CMI",root/"LEVEL3O.MTO",root/"LEVEL3.DTI"]
allowed=set(((i<<3)|(i>>2)) for i in range(32))
W=240
out=[]
for p in files:
 if not p.exists(): continue
 b=p.read_bytes()
 flags=bytearray(1 if x in allowed else 0 for x in b)
 if len(b)<W: continue
 s=sum(flags[:W]); heap=[]
 def consider(off,score):
  if score < int(W*.97): return
  chunk=b[off:off+W]
  triples=[tuple(chunk[i:i+3]) for i in range(0,W,3)]
  uniq3=len(set(triples)); uniqb=len(set(chunk)); dom=max(collections.Counter(chunk).values())
  if uniq3<50 or uniqb<20 or dom>W*.22: return
  rank=(score,uniq3,uniqb,-dom)
  item=(rank,off,score,uniq3,uniqb,dom)
  if len(heap)<120: heapq.heappush(heap,item)
  elif rank>heap[0][0]: heapq.heapreplace(heap,item)
 consider(0,s)
 for i in range(W,len(b)):
  s+=flags[i]-flags[i-W]
  consider(i-W+1,s)
 chosen=[]
 for rank,off,score,uniq3,uniqb,dom in sorted(heap,reverse=True):
  if any(abs(off-x["offset"])<W for x in chosen): continue
  ch=b[off:off+W]
  chosen.append({"file":p.name,"offset":off,"ratio":round(score/W,6),"unique_rgb":uniq3,"unique_bytes":uniqb,"dominant":dom,"sha256":hashlib.sha256(ch).hexdigest(),"first24":ch[:24].hex(),"last24":ch[-24:].hex()})
  if len(chosen)>=12: break
 out.extend(chosen)
out.sort(key=lambda x:(x["ratio"],x["unique_rgb"],x["unique_bytes"]),reverse=True)
groups=collections.defaultdict(list)
for x in out: groups[x["sha256"]].append({"file":x["file"],"offset":x["offset"]})
print(json.dumps({"schema":"OpenMDK.Level3Global80PaletteScan.v1","window":W,"candidates":out,"shared":{k:v for k,v in groups.items() if len(v)>1}},indent=2))
