import pathlib,struct,json,hashlib
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE")
out={}
def sha(x): return hashlib.sha256(x).hexdigest()
for n in range(3,9):
 p=root/f"LEVEL{n}"/f"LEVEL{n}.DTI"
 if not p.exists():
  out[f"LEVEL{n}"]={"missing":True}; continue
 b=p.read_bytes()
 hdr=list(struct.unpack_from("<10I",b,0))
 s=hdr[8] if len(hdr)>8 else None
 e=hdr[9] if len(hdr)>9 else None
 rec={"size":len(b),"header10":hdr,"section_start":s,"section_end":e,"section_len":e-s if s is not None and e is not None else None}
 if s is not None and e is not None and 0<=s<e<=len(b):
  sec=b[s:e]; rec["section_sha256"]=sha(sec); rec["section_first16"]=sec[:16].hex()
  if len(sec)>=772:
   pal=sec[4:4+768]
   rec["palette256_sha256"]=sha(pal)
   rec["global144_sha256"]=sha(pal[:432])
   rec["tail112_sha256"]=sha(pal[432:])
   rec["global144_first24"]=pal[:24].hex()
   rec["global144_unique_rgb"]=len(set(tuple(pal[i:i+3]) for i in range(0,432,3)))
   rec["tail112_unique_rgb"]=len(set(tuple(pal[i:i+3]) for i in range(432,768,3)))
 out[f"LEVEL{n}"]=rec
hashes={}
for lev,r in out.items():
 h=r.get("global144_sha256")
 if h: hashes.setdefault(h,[]).append(lev)
print(json.dumps({"schema":"OpenMDK.CrossLevelDTIPaletteProbe.v1","levels":out,"global144_groups":hashes},indent=2))
