import pathlib,struct,json,hashlib
SRC=pathlib.Path(r"F:\Remaster Framework\source\MDK\FALL3D\FALL3D.BNI")
OUT=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\kurtanim_structural.json")
b=SRC.read_bytes()
base=0x4a04
size=91644
d=b[base:base+size]
track_count=struct.unpack_from("<I",d,8)[0]
offsets=list(struct.unpack_from("<%dI"%(track_count+1),d,12))
tracks=[]
for i in range(1,track_count+1):
 s=offsets[i]
 e=offsets[i+1] if i<track_count else len(d)
 x=d[s:e]
 name=x[8:20].split(b"\0")[0].decode("ascii","replace")
 vc=struct.unpack_from("<I",x,20)[0]
 tracks.append({"index":i,"name":name,"offset":s,"end":e,"size":e-s,"vertex_count":vc})
receipt={"schema":"OpenMDK.KurtAnimStructural.v1","source":str(SRC),"source_sha256":hashlib.sha256(b).hexdigest(),"resource_offset":base,"resource_size":size,"timing_raw":list(struct.unpack_from("<2I",d,0)),"track_count":track_count,"offsets":offsets,"tracks":tracks,"confirmed_decoder_contract":{"runtime_update":"MDK95.EXE:0x4555BC","frame_part_decoder":"MDK95.EXE:0x455890","keyframe_decoder":"MDK95.EXE:0x455C48","delta":"signed int8 XYZ * per-track scale added to previous vertex"},"unknown":["exact track frame-stream header boundaries","keyframe/delta opcode layout","scale field offset semantics"]}
OUT.write_text(json.dumps(receipt,indent=2))
print(json.dumps({"tracks":len(tracks),"track_count":track_count,"first":tracks[:4],"sha256":receipt["source_sha256"]},indent=2))
