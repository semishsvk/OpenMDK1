import json,subprocess,re,pathlib,collections
p=subprocess.run(["python",r"F:\Remaster Framework\work\OpenMDK1\src\triangle_u16_audit.py"],capture_output=True,text=True,check=True)
d=json.loads(p.stdout)
cmi=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.CMI").read_bytes()
syms=[x.decode() for x in re.findall(rb'HMO_[0-9]+\$[A-Z0-9_]+',cmi[:8192])]
fam=collections.defaultdict(set)
for s in syms:
 h,x=s.split("$",1); fam[h].add(x.split("_")[0])
out={}
for h,v in d.items():
 f17=v["u16_top"][17]; uniq=v["u16_unique"][17]
 out[h]={"field17_unique":uniq,"field17_top":f17,"cmi_family_count":len(fam[h]),"cmi_families":sorted(fam[h])}
print(json.dumps(out,indent=2))
