import pathlib,struct,json,hashlib,collections
dti=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI").read_bytes()
evp=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\hmo_palette_geometry_boundary_v2.json")
raw=evp.read_bytes(); text=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8"); ev=json.loads(text)
sec_start,sec_end=3372,4144
hdr=dti[sec_start:sec_start+4]
pal=dti[sec_start+4:sec_end]
global144=pal[:144*3]
tail112=pal[144*3:]
allowed=set(((i<<3)|(i>>2)) for i in range(32))
def sha(x): return hashlib.sha256(x).hexdigest()
matches=[]
for hn,h in ev["hmos"].items():
 if h["palette_sha256"]==sha(tail112): matches.append(hn)
print(json.dumps({
 "schema":"OpenMDK.DTIFullPaletteProbe.v1",
 "section":[sec_start,sec_end],
 "section_len":sec_end-sec_start,
 "header_hex":hdr.hex(),
 "header_u32":struct.unpack("<I",hdr)[0],
 "palette_offset":sec_start+4,
 "palette_len":len(pal),
 "palette_entries":len(pal)//3,
 "rgb555_expanded_ratio":sum(x in allowed for x in pal)/len(pal),
 "unique_rgb":len(set(tuple(pal[i:i+3]) for i in range(0,len(pal),3))),
 "palette_sha256":sha(pal),
 "global144":{"len":len(global144),"entries":144,"sha256":sha(global144),"unique_rgb":len(set(tuple(global144[i:i+3]) for i in range(0,len(global144),3)))},
 "tail112":{"len":len(tail112),"entries":112,"sha256":sha(tail112),"unique_rgb":len(set(tuple(tail112[i:i+3]) for i in range(0,len(tail112),3))),"matching_hmos":matches},
 "hmo_palette_hashes":{hn:h["palette_sha256"] for hn,h in ev["hmos"].items()},
 "status":"STRUCTURAL_PASS" if len(pal)==768 and sum(x in allowed for x in pal)==768 else "INCONCLUSIVE"
},indent=2))
