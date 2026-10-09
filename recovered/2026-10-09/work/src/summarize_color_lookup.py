import json, pathlib
p=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\hmo_color_lookup_probe_v1.json")
raw=p.read_bytes()
text=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
d=json.loads(text)
hs=d["hmos"]
print("HMOs",len(hs))
print("blocklens",sorted(set(v["block_len"] for v in hs.values())))
print("first256_unique",{k:v["first256_unique"] for k,v in hs.items()})
print("mapped_unique",{k:v["mapped_unique"] for k,v in hs.items()})
print("tail80_unique",{k:v["tail80_unique"] for k,v in hs.items()})
print("identity_entries",{k:v["identity_entries"] for k,v in hs.items()})
