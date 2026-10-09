import json,pathlib
root=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\evidence")
def load(name):
 p=root/name; raw=p.read_bytes()
 text=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
 return json.loads(text)
scan=load("level3_global80_palette_scan_v1.json")
pal=load("hmo_palette_geometry_boundary_v2.json")
cont=load("global_palette_container_probe_v1.json")
blocks=cont["mto"]["blocks"]
size=cont["files"]["LEVEL3O.MTO"]["size"]
ranges=[]
for i,b in enumerate(blocks):
 start=b["off"]; end=blocks[i+1]["off"] if i+1<len(blocks) else size
 h=pal["hmos"][b["name"]]
 ranges.append((b["name"],start,end,start+h["palette_start"],start+h["palette_end"]))
out=[]
for c in scan["candidates"]:
 x=dict(c); x["classification"]="NON_MTO"
 if c["file"]=="LEVEL3O.MTO":
  off=c["offset"]; x["classification"]="MTO_OTHER"
  for hn,bs,be,ps,pe in ranges:
   if bs<=off<be:
    x["hmo"]=hn; x["block_offset"]=off-bs
    if off>=ps and off+scan["window"]<=pe:
     x["classification"]="INSIDE_LOCAL_112_PALETTE"
     x["local_palette_abs"]=[ps,pe]
    elif off<pe and off+scan["window"]>ps:
     x["classification"]="OVERLAPS_LOCAL_112_PALETTE"
     x["local_palette_abs"]=[ps,pe]
    break
 out.append(x)
print(json.dumps({"schema":"OpenMDK.Global80CandidateClassification.v1","ranges":[{"hmo":a,"block":[b,c],"palette":[d,e]} for a,b,c,d,e in ranges],"candidates":out},indent=2))
