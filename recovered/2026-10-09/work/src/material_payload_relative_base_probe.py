import struct, pathlib, json, hashlib
src=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO")
B=src.read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
BASE=0x14
out={}
for bi in range(cnt):
    q=24+bi*12
    name=B[q:q+8].split(b"\0")[0].decode("ascii","replace")
    s=struct.unpack_from("<I",B,q+8)[0]
    e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
    h=B[s:e]
    n=struct.unpack_from("<I",h,36)[0]
    table_end=40+n*24
    rel=[struct.unpack_from("<I",h,40+i*24+20)[0] for i in range(n)]
    abs_off=[BASE+x for x in rel]
    payload_end_rel=struct.unpack_from("<I",h,4)[0]
    payload_end_abs=BASE+payload_end_rel
    rec=[]
    for i,a in enumerate(abs_off):
        z=abs_off[i+1] if i+1<n else payload_end_abs
        seg=h[a:z]
        matname=h[40+i*24:40+i*24+20].split(b"\0")[0].decode("ascii","replace")
        rec.append({"i":i,"name":matname,"rel_offset":rel[i],"abs_offset":a,"size":len(seg),"sha256":hashlib.sha256(seg).hexdigest(),"first16":seg[:16].hex()})
    out[name]={
      "material_count":n,
      "table_end":table_end,
      "first_rel_offset":rel[0] if rel else None,
      "first_abs_offset":abs_off[0] if abs_off else None,
      "first_abs_equals_table_end": bool(abs_off and abs_off[0]==table_end),
      "payload_end_rel":payload_end_rel,
      "payload_end_abs":payload_end_abs,
      "payload_end_in_block":payload_end_abs<=len(h),
      "strictly_increasing":all(abs_off[i]<abs_off[i+1] for i in range(len(abs_off)-1)),
      "records":rec
    }
print(json.dumps(out,indent=2))
