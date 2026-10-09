import pathlib,struct,json,hashlib,collections,math
p=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI")
b=p.read_bytes()
sec_start=3372; sec_end=4144; pal_start=sec_end-240
pal=b[pal_start:sec_end]
allowed=set(((i<<3)|(i>>2)) for i in range(32))
triples=[tuple(pal[i:i+3]) for i in range(0,len(pal),3)]
def h(x): return hashlib.sha256(x).hexdigest()
print(json.dumps({
 "schema":"OpenMDK.DTIGlobal80BoundaryProbe.v1",
 "section":[sec_start,sec_end],
 "section_len":sec_end-sec_start,
 "palette_start":pal_start,
 "palette_end":sec_end,
 "palette_len":len(pal),
 "rgb_count":len(triples),
 "rgb555_expanded_ratio":sum(x in allowed for x in pal)/len(pal),
 "unique_rgb":len(set(triples)),
 "unique_bytes":len(set(pal)),
 "dominant_byte_count":max(collections.Counter(pal).values()),
 "sha256":h(pal),
 "first24":pal[:24].hex(),
 "last24":pal[-24:].hex(),
 "bytes_before32":b[pal_start-32:pal_start].hex(),
 "u32_at_section_start":[struct.unpack_from("<I",b,sec_start+i*4)[0] for i in range(12)],
 "u32_before_palette":[struct.unpack_from("<I",b,pal_start-32+i*4)[0] for i in range(8)],
 "next_section_first32":b[sec_end:sec_end+32].hex(),
 "scan_candidate_3908_sha256":h(b[3908:3908+240]),
 "status":"STRUCTURAL_SUPPORT" if len(pal)==240 and sum(x in allowed for x in pal)==240 and len(set(triples))>=70 else "INCONCLUSIVE"
},indent=2))
