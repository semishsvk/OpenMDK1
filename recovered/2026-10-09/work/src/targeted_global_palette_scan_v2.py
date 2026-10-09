import pathlib,json,hashlib,heapq,collections,math
root=pathlib.Path(r"F:\Remaster Framework\source\MDK")
files=[
 root/"MDK95.EXE",root/"MDKD3D.EXE",root/"MDK3DFX.EXE",
 root/"TRAVERSE"/"TRAVSPRT.BNI",root/"FALL3D"/"FALL3D.BNI",
 root/"FALL3D"/"FALL3D_1.MTI",root/"FALL3D"/"FALL3D_2.MTI",root/"FALL3D"/"FALL3D_3.MTI",root/"FALL3D"/"FALL3D_4.MTI",root/"FALL3D"/"FALL3D_5.MTI",
 root/"TRAVERSE"/"LEVEL3"/"LEVEL3.CMI",root/"TRAVERSE"/"LEVEL3"/"LEVEL3S.MTI",
 root/"MISC"/"FINISH.BNI",root/"MISC"/"OPTIONS.BNI",root/"MISC"/"STATS.BNI",root/"MISC"/"STATS.MTI"
]
allowed=set(((i<<3)|(i>>2)) for i in range(32)); W=432
cands=[]
for p in files:
 if not p.exists() or p.stat().st_size<W: continue
 b=p.read_bytes(); flags=bytearray(1 if x in allowed else 0 for x in b)
 s=sum(flags[:W])
 # sample only windows with >=88% quantized, keep best by composite diversity score
 heap=[]
 def consider(off,score):
  if score < int(W*.88): return
  chunk=b[off:off+W]
  triples=[tuple(chunk[i:i+3]) for i in range(0,W,3)]
  uniq3=len(set(triples)); uniqb=len(set(chunk))
  dominant=max(collections.Counter(chunk).values())
  if uniq3<70 or uniqb<18 or dominant>W*.35: return
  rank=(score/W,uniq3,uniqb,-dominant,off)
  if len(heap)<80: heapq.heappush(heap,(rank,off,score,uniq3,uniqb,dominant))
  elif rank>heap[0][0]: heapq.heapreplace(heap,(rank,off,score,uniq3,uniqb,dominant))
 consider(0,s)
 for i in range(W,len(b)):
  s+=flags[i]-flags[i-W]
  consider(i-W+1,s)
 top=sorted(heap,reverse=True)
 chosen=[]
 for item in top:
  _,off,score,uniq3,uniqb,dom=item
  if any(abs(off-o)<W for o in [x["offset"] for x in chosen]): continue
  chunk=b[off:off+W]
  chosen.append({"file":str(p.relative_to(root)),"offset":off,"ratio":round(score/W,6),"unique_rgb":uniq3,"unique_bytes":uniqb,"dominant":dom,"sha256":hashlib.sha256(chunk).hexdigest(),"first24":chunk[:24].hex(),"last24":chunk[-24:].hex()})
  if len(chosen)>=10: break
 cands+=chosen
groups=collections.defaultdict(list)
for c in cands: groups[c["sha256"]].append({"file":c["file"],"offset":c["offset"]})
cands.sort(key=lambda x:(x["ratio"],x["unique_rgb"],x["unique_bytes"]),reverse=True)
print(json.dumps({"schema":"OpenMDK.TargetedGlobalPaletteScan.v2","candidates":cands,"shared_hashes":{h:v for h,v in groups.items() if len(v)>1}},indent=2))
