import json, collections, pathlib
p=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence\iter2\material_payload_classify.json")
raw=p.read_bytes()
text=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
data=json.loads(text)
sizes=collections.Counter()
heads=collections.defaultdict(collections.Counter)
rows=[]
for hmo, arr in data.items():
    for rec in arr:
        size=rec["size"]
        sizes[size]+=1
        heads[size][tuple(rec.get("u32_head", []))]+=1
        rows.append((hmo,rec["i"],rec["name"],size,rec.get("u32_head",[]),rec["head"][:32],rec["entropy"]))
print("SIZE_CLASSES", sizes.most_common())
for size,count in sizes.most_common():
    print("\nSIZE",size,"N",count,"MINUS4",size-4)
    print("U32_HEADS",heads[size].most_common(5))
    print("SAMPLES")
    for row in [r for r in rows if r[3]==size][:6]:
        print(row)
