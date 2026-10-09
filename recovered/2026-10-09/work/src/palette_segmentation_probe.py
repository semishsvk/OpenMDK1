import json,re,pathlib,struct,collections,math
root=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence")
meta=json.loads((root/"geom_prematerial_metadata_probe_v1.json").read_text(encoding="utf-16" if (root/"geom_prematerial_metadata_probe_v1.json").read_bytes().startswith(b"\xff\xfe") else "utf-8"))
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
out={}
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]
 pal0=struct.unpack_from("<I",h,8)[0]; pal1=struct.unpack_from("<I",h,12)[0]; pal=h[pal0:pal1]
 names=[x["text"] for x in meta[hn]["strings"]]
 pens=[int(m.group(1)) for x in names if (m:=re.fullmatch(r"PEN_(\d+)",x))]
 pen_info=[]
 for p in pens:
  rec={"pen":p,"segment":"local_144_255" if p>=144 else "global_0_143"}
  if p>=144 and p<=255:
   i=(p-144)*3; rec["rgb"]=list(pal[i:i+3]); rec["local_offset"]=p-144
  pen_info.append(rec)
 # texture index usage
 n=struct.unpack_from("<I",h,36)[0]; hist=collections.Counter()
 for mi in range(n):
  rel=struct.unpack_from("<I",h,40+mi*24+20)[0]; a=20+rel; w,hh=struct.unpack_from("<HH",h,a); hist.update(h[a+4:a+4+w*hh])
 out[hn]={
  "geom_name_count":len(names),"names":names,"pens":pen_info,
  "texture_pixels_total":sum(hist.values()),"texture_unique_indices":len(hist),
  "pixels_global_0_143":sum(v for k,v in hist.items() if k<144),
  "pixels_local_144_255":sum(v for k,v in hist.items() if k>=144),
  "used_local_indices":len([k for k in hist if k>=144]),
  "used_global_indices":len([k for k in hist if k<144]),
  "top_indices":hist.most_common(20)
 }
print(json.dumps({"schema":"OpenMDK.PaletteSegmentationProbe.v1","hypothesis":"palette[0:144] global + per-HMO palette[144:256] stored as 336-byte RGB888 block","hmos":out},indent=2))
