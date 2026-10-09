import pathlib,struct,hashlib,json
p=pathlib.Path(r"F:\Remaster Framework\source\MDK\MISC\mdkfont.fti")
raw=p.read_bytes()
obj=raw[4:]
count=struct.unpack_from("<I",obj,0)[0]
recs=[]
for i in range(count):
    o=4+i*12
    name=obj[o:o+8].split(b"\0")[0].decode("ascii","replace")
    off=struct.unpack_from("<I",obj,o+8)[0]
    recs.append((name,off))
idx=next(i for i,(n,_) in enumerate(recs) if n=="SYS_PAL")
name,off=recs[idx]
nxt=recs[idx+1][1]
seg=obj[off:nxt]
dti=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI").read_bytes()
dobj=dti[4:]
ptr=struct.unpack_from("<I",dobj,0x1c)[0]
pal=dobj[ptr+4:ptr+4+768]
out={
 "schema":"OpenMDK.SysPalFixed64.v1",
 "fti_declared_size":struct.unpack_from("<I",raw,0)[0],
 "fti_entry_count":count,
 "sys_pal_object_offset":off,
 "sys_pal_raw_offset":off+4,
 "next_object_offset":nxt,
 "payload_len":len(seg),
 "entries":len(seg)//3,
 "sha256":hashlib.sha256(seg).hexdigest(),
 "unique_rgb":len(set(tuple(seg[i:i+3]) for i in range(0,len(seg),3))),
 "first24":seg[:24].hex(),
 "matches_dti_first64":seg==pal[:192],
 "dti_first64_sha256":hashlib.sha256(pal[:192]).hexdigest(),
 "status":"STRUCTURAL_PASS" if len(seg)==192 else "FAIL"
}
print(json.dumps(out,indent=2))
