import json,pathlib
q=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\triangle_render_code_v1.json")
raw=q.read_bytes(); t=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
d=json.loads(t)
print("TOTALS",d["totals"])
for h,v in d["hmos"].items():
 print("\n",h)
 for n,hist in v["by_geometry_name"].items():
  if n.startswith("PEN_") or n.startswith("GLASS") or n=="NONE":
   print(n,hist)
