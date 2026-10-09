import json,pathlib,re
p=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\mti_pen_record_probe_v1.json")
raw=p.read_bytes(); text=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
d=json.loads(text)
for r in d["pen_records"]:
 m=re.fullmatch(r"PEN_(\d+)",r["name"])
 if not m: continue
 n=int(m.group(1))
 if r["u32"]!=n:
  print(r["name"],"->",r["u32"],"record",r["i"],"sentinel",r["u16a"],r["u16b"],"f",r["f"],"off",r["off"])
