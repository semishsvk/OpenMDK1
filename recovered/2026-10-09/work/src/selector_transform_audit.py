import json,subprocess,collections
p=subprocess.run(["python",r"F:\Remaster Framework\work\OpenMDK1\src\triangle_selector_audit.py"],capture_output=True,text=True,check=True)
d=json.loads(p.stdout)
counts={"HMO_1":21,"HMO_2":8,"HMO_3":7,"HMO_4":9,"HMO_5":7,"HMO_6":5,"HMO_7":0,"HMO_8":10,"HMO_9":10,"HMO_10":7}
out={}
for h,v in d.items():
 vals=v["index_unique"]; n=counts[h]
 if not n: out[h]={"material_count":n,"selectors":vals}; continue
 out[h]={"material_count":n,"selector_count":len(vals),"max":max(vals),"mod_unique":sorted(set(x%n for x in vals)),"low3_unique":sorted(set(x&7 for x in vals)),"low4_unique":sorted(set(x&15 for x in vals)),"block32":sorted(set(x//32 for x in vals)),"res32":sorted(set(x%32 for x in vals))}
print(json.dumps(out,indent=2))
