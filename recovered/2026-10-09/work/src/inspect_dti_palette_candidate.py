import pathlib,struct,json,hashlib,re
p=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI")
b=p.read_bytes(); off=3908
start=max(0,off-256); end=min(len(b),off+240+256)
chunk=b[start:end]
strings=[]
for m in re.finditer(rb"[ -~]{4,}",chunk):
 strings.append({"abs_off":start+m.start(),"text":m.group().decode("ascii","replace")})
print(json.dumps({
 "file_size":len(b),
 "candidate_offset":off,
 "candidate_sha256":hashlib.sha256(b[off:off+240]).hexdigest(),
 "before64":b[off-64:off].hex(),
 "candidate_first64":b[off:off+64].hex(),
 "candidate_last64":b[off+176:off+240].hex(),
 "after64":b[off+240:off+304].hex(),
 "strings_nearby":strings[:80],
 "mod36":off%36,
 "mod24":off%24,
 "mod16":off%16,
 "mod12":off%12,
 "u32_before":[struct.unpack_from("<I",b,x)[0] for x in range(max(0,off-32),off,4)]
},indent=2))
