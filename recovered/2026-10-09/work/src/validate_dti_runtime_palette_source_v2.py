import pathlib,struct,json,hashlib,collections
p=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI")
raw=p.read_bytes()
declared=struct.unpack_from("<I",raw,0)[0]
obj=raw[4:]
assert declared==len(obj)
ptr=struct.unpack_from("<I",obj,0x1c)[0]
count=struct.unpack_from("<I",obj,ptr)[0]
palette_start=ptr+4
palette=obj[palette_start:palette_start+768]
fixed_candidate=palette[:64*3]
dynamic192=palette[64*3:]
global80=dynamic192[:80*3]
tail112=dynamic192[80*3:]
def sha(x): return hashlib.sha256(x).hexdigest()
def uniq_rgb(x): return len(set(tuple(x[i:i+3]) for i in range(0,len(x),3)))
def yellow(x): return sum(1 for i in range(0,len(x),3) if tuple(x[i:i+3])==(255,255,0))
out={
 "schema":"OpenMDK.DTIRuntimePaletteSource.v2",
 "raw_file_size":len(raw),
 "declared_payload_size":declared,
 "loader_model":"file[0:4] length prefix stripped; internal offsets relative to file[4:]",
 "object_header_field_0x1c":ptr,
 "count_at_section":count,
 "count_interpretation":"u32 preceding 256xRGB888 palette; observed value 112, semantics not promoted",
 "palette_object_offset":palette_start,
 "palette_raw_file_offset":4+palette_start,
 "palette_len":len(palette),
 "palette_entries":len(palette)//3,
 "palette_sha256":sha(palette),
 "first64":{"entries":64,"sha256":sha(fixed_candidate),"unique_rgb":uniq_rgb(fixed_candidate),"yellow_entries":yellow(fixed_candidate),"first24":fixed_candidate[:24].hex()},
 "dynamic192":{"entries":192,"object_offset":palette_start+0xc0,"raw_file_offset":4+palette_start+0xc0,"sha256":sha(dynamic192),"unique_rgb":uniq_rgb(dynamic192),"yellow_entries":yellow(dynamic192),"first24":dynamic192[:24].hex()},
 "dynamic_first80":{"entries":80,"sha256":sha(global80),"unique_rgb":uniq_rgb(global80),"yellow_entries":yellow(global80),"first24":global80[:24].hex()},
 "dynamic_tail112":{"entries":112,"sha256":sha(tail112),"unique_rgb":uniq_rgb(tail112),"yellow_entries":yellow(tail112),"first24":tail112[:24].hex()},
 "runtime_copy_contract":{"source":"[0x54C678]+0xC0","destination":"0x5408E0","bytes":576,"entries":192,"confirmed_by":"MDK95.EXE 0x434787..0x4347B2"},
 "status":"STRUCTURAL_PASS" if len(palette)==768 and len(dynamic192)==576 else "FAIL"
}
print(json.dumps(out,indent=2))
