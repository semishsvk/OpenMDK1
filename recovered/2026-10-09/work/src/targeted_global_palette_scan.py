import pathlib,json,hashlib,heapq
root=pathlib.Path(r"F:\Remaster Framework\source\MDK")
files=[
 root/"MDK95.EXE",root/"MDKD3D.EXE",root/"MDK3DFX.EXE",
 root/"TRAVERSE"/"TRAVSPRT.BNI",
 root/"FALL3D"/"FALL3D.BNI",
 root/"FALL3D"/"FALL3D_1.MTI",root/"FALL3D"/"FALL3D_2.MTI",root/"FALL3D"/"FALL3D_3.MTI",root/"FALL3D"/"FALL3D_4.MTI",root/"FALL3D"/"FALL3D_5.MTI",
 root/"TRAVERSE"/"LEVEL3"/"LEVEL3.CMI",root/"TRAVERSE"/"LEVEL3"/"LEVEL3S.MTI",
 root/"MISC"/"FINISH.BNI",root/"MISC"/"OPTIONS.BNI",root/"MISC"/"STATS.BNI",root/"MISC"/"STATS.MTI"
]
allowed=set(((i<<3)|(i>>2)) for i in range(32))
W=432
out=[]
for p in files:
 if not p.exists() or p.stat().st_size<W: continue
 b=p.read_bytes()
 flags=bytearray(1 if x in allowed else 0 for x in b)
 s=sum(flags[:W])
 heap=[]
 def add(score,off):
  item=(score,off)
  if len(heap)<40: heapq.heappush(heap,item)
  elif item>heap[0]: heapq.heapreplace(heap,item)
 add(s,0)
 for i in range(W,len(b)):
  s+=flags[i]-flags[i-W]
  add(s,i-W+1)
 top=sorted(heap,reverse=True)
 chosen=[]
 for score,off in top:
  if any(abs(off-o)<W for _,o in chosen): continue
  chosen.append((score,off))
  if len(chosen)>=6: break
 for score,off in chosen:
  chunk=b[off:off+W]
  out.append({"file":str(p.relative_to(root)),"size":len(b),"offset":off,"score":score,"ratio":round(score/W,6),"sha256":hashlib.sha256(chunk).hexdigest(),"first24":chunk[:24].hex()})
out.sort(key=lambda x:x["ratio"],reverse=True)
print(json.dumps({"schema":"OpenMDK.TargetedGlobalPaletteScan.v1","window":W,"candidates":out},indent=2))
