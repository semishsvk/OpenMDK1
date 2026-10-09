import json,pathlib,re
p=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\mti_pen_record_probe_v1.json")
raw=p.read_bytes(); text=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
d=json.loads(text); rs=d["pen_records"]
vals=[]
bad=[]
for r in rs:
 m=re.fullmatch(r"PEN_(\d+)",r["name"])
 if not m: continue
 n=int(m.group(1)); vals.append(n)
 if not (r["u32"]==n and r["u16a"]==65535 and r["u16b"]==65535 and r["f"]==0.0 and r["off"]==0 and r["payload_len"]==0):
  bad.append((r["name"],r))
print("count",len(vals))
print("minmax",(min(vals),max(vals)))
print("unique",len(set(vals)))
print("values",sorted(vals))
print("bad",len(bad),bad[:5])
print("global_count",sum(v<144 for v in vals),"local_count",sum(v>=144 for v in vals))
