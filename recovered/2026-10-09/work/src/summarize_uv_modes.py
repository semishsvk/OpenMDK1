import json,pathlib
p=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\uv_mode_classification_v1.json")
raw=p.read_bytes(); t=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
d=json.loads(t)
print("GLOBAL",d["global_modes"])
for h,v in d["hmos"].items():
 print("\n",h,"modes",v["modes"])
 bf=v["by_f3"]
 ranked=sorted(bf.items(),key=lambda kv:-sum(kv[1].values()))[:12]
 print("f3",ranked)
 bq=v["by_selector_quotient"]
 rankedq=sorted(bq.items(),key=lambda kv:-sum(kv[1].values()))[:12]
 print("q",rankedq)
