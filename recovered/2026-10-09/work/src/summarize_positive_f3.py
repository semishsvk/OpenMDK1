import json,pathlib
q=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\positive_f3_texture_mapping_v1.json")
raw=q.read_bytes(); t=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
d=json.loads(t)
print("TOTALS",d["totals"])
for h,rows in d["hmos"].items():
 print("\n",h)
 for r in rows[:20]: print(r)
