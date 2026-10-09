import pathlib,struct,json,hashlib,collections
D=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI").read_bytes()
ptr=struct.unpack_from("<I",D,0x1c)[0]
count=struct.unpack_from("<I",D,ptr)[0]
source=ptr+4
dyn_start=source+0xc0
dyn=D[dyn_start:dyn_start+0x240]
first80=dyn[:80*3]; tail112=dyn[80*3:]
def sha(x):return hashlib.sha256(x).hexdigest()
def uniq(x):return len(set(tuple(x[i:i+3]) for i in range(0,len(x),3)))
print(json.dumps({
 "schema":"OpenMDK.DTIRuntimePaletteSource.v1",
 "dti_header_offset_0x1c":ptr,
 "count_at_ptr":count,
 "runtime_source_offset":source,
 "copy_source_offset":dyn_start,
 "copy_len":len(dyn),
 "entries":len(dyn)//3,
 "dynamic192_sha256":sha(dyn),
 "dynamic192_unique_rgb":uniq(dyn),
 "first80":{"offset":[dyn_start,dyn_start+240],"sha256":sha(first80),"unique_rgb":uniq(first80),"first24":first80[:24].hex()},
 "tail112":{"offset":[dyn_start+240,dyn_start+576],"sha256":sha(tail112),"unique_rgb":uniq(tail112),"first24":tail112[:24].hex()},
 "status":"STRUCTURAL_PASS" if len(dyn)==576 else "FAIL"
},indent=2))
