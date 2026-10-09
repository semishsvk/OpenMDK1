import pathlib,struct,json,hashlib
root=pathlib.Path(r"F:\Remaster Framework\source\MDK")
mto_path=root/"TRAVERSE"/"LEVEL3"/"LEVEL3O.MTO"
dti_path=root/"TRAVERSE"/"LEVEL3"/"LEVEL3.DTI"
fti_path=root/"MISC"/"mdkfont.fti"
exe_path=root/"MDK95.EXE"
M=mto_path.read_bytes(); D=dti_path.read_bytes(); F=fti_path.read_bytes(); X=exe_path.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()

# SYS_PAL fixed64 from FTI, whose loader copies 0xC0 bytes to 0x540820.
fo=F[4:]; fc=struct.unpack_from("<I",fo,0)[0]; frecs=[]
for i in range(fc):
    q=4+i*12
    frecs.append((fo[q:q+8].split(b"\0")[0].decode("ascii","replace"),struct.unpack_from("<I",fo,q+8)[0]))
si=next(i for i,x in enumerate(frecs) if x[0]=="SYS_PAL")
fixed64=fo[frecs[si][1]:frecs[si+1][1]]

# DTI loader strips the raw 4-byte size prefix. Internal offsets use D[4:] object base.
do=D[4:]
dptr=struct.unpack_from("<I",do,0x1c)[0]
dcount=struct.unpack_from("<I",do,dptr)[0]
dpal=do[dptr+4:dptr+4+768]
global80=dpal[176*3:256*3]

# Each MTO HMO streamed block likewise presents raw block[4:] as runtime blob base.
hcnt=struct.unpack_from("<I",M,20)[0]
hmos={}
all_ok=True
for i in range(hcnt):
    q=24+i*12
    name=M[q:q+8].split(b"\0")[0].decode()
    s=struct.unpack_from("<I",M,q+8)[0]
    e=struct.unpack_from("<I",M,24+(i+1)*12+8)[0] if i+1<hcnt else len(M)
    h=M[s:e]
    raw_palette_field=struct.unpack_from("<I",h,8)[0]
    raw_geom_field=struct.unpack_from("<I",h,12)[0]
    runtime_blob_base_delta=4
    runtime_field40_delta=runtime_blob_base_delta+raw_palette_field
    local=h[runtime_field40_delta:runtime_field40_delta+336]
    geometry_delta=runtime_blob_base_delta+raw_geom_field
    ok=(len(local)==336 and runtime_field40_delta+336==geometry_delta)
    all_ok &= ok
    hmos[name]={
      "block_start":s,"block_size":e-s,
      "raw_header_palette_field_at_0x08":raw_palette_field,
      "raw_header_geometry_field_at_0x0c":raw_geom_field,
      "runtime_blob_base_delta":4,
      "runtime_object_field_0x40_delta":runtime_field40_delta,
      "local_palette_entries":len(local)//3,
      "local_palette_sha256":sha(local),
      "geometry_metadata_delta":geometry_delta,
      "palette_end_equals_geometry_start":runtime_field40_delta+336==geometry_delta,
      "status":"PASS" if ok else "FAIL"
    }

out={
 "schema":"OpenMDK.RuntimePaletteComposition.v1",
 "evidence_state":"STRUCTURAL",
 "sources":{
   "MDK95.EXE_sha256":sha(X),
   "LEVEL3O.MTO_sha256":sha(M),
   "LEVEL3.DTI_sha256":sha(D),
   "mdkfont.fti_sha256":sha(F)
 },
 "loader_contract":{
   "dti":"LEVEL3.DTI is loaded after stripping 4-byte raw length prefix; object[0x1c]+4 is palette base",
   "mto":"LEVEL3O.MTO index is streamed blockwise after each block's 4-byte prefix; 0x41AB44 returns that runtime blob base",
   "runtime_hmo_field40":"0x432376..0x432384: object+0x40 = blob_base + blob[+4]",
   "runtime_hmo_palette_write":"0x432240..0x43227A and 0x432A08..0x432A40: copy 3*count bytes to runtime index64 and call writer(start=64,count)",
   "runtime_dti_dynamic_copy":"0x434787..0x4347B2: copy 0x240 bytes from DTI palette source +0xC0 to runtime index64, then full 256-entry write",
   "fixed64_init":"SYS_PAL 0xC0-byte payload copied to 0x540820"
 },
 "composition":{
   "indices_0_63":{"source":"MISC/mdkfont.fti:SYS_PAL","entries":64,"sha256":sha(fixed64),"status":"STRUCTURAL_PASS"},
   "indices_64_175":{"source":"active HMO local palette via runtime object+0x40","entries":112,"status":"STRUCTURAL_PASS"},
   "indices_176_255":{"source":"LEVEL3.DTI corrected palette entries 176..255","entries":80,"sha256":sha(global80),"unique_rgb":len(set(tuple(global80[j:j+3]) for j in range(0,len(global80),3))),"status":"STRUCTURAL_PASS"}
 },
 "dti":{
   "declared_payload_size":struct.unpack_from("<I",D,0)[0],
   "object_header_0x1c":dptr,
   "count_at_palette_section":dcount,
   "corrected_palette_raw_offset":4+dptr+4,
   "fixed64_matches_SYS_PAL":dpal[:192]==fixed64,
   "placeholder_entries_64_143_unique_rgb":len(set(tuple(dpal[j:j+3]) for j in range(64*3,144*3,3))),
   "global80_sha256":sha(global80)
 },
 "hmos":hmos,
 "status":"STRUCTURAL_PASS" if all_ok and len(fixed64)==192 and len(global80)==240 and dpal[:192]==fixed64 else "FAIL",
 "not_verified":["UV transform/normalization/wrap/filter semantics","GLASS1 render-state semantics","original-runtime visual fidelity"],
 "promotion_rule":"Palette composition may be used for deterministic renderer binding, but does not by itself promote LEVEL3 to FIDELITY_VERIFIED."
}
print(json.dumps(out,indent=2))
