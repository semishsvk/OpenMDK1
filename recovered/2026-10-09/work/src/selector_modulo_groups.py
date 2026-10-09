import json,subprocess,collections
d=json.loads(subprocess.run(["python",r"F:\Remaster Framework\work\OpenMDK1\src\triangle_selector_audit.py"],capture_output=True,text=True,check=True).stdout)
counts={"HMO_1":21,"HMO_2":8,"HMO_3":7,"HMO_4":9,"HMO_5":7,"HMO_6":5,"HMO_8":10,"HMO_9":10,"HMO_10":7}
for h,n in counts.items():
 vals=d[h]["index_unique"]; pairs=collections.defaultdict(list)
 for x in vals:pairs[x%n].append(x)
 print(h,'N',n,'ordinals')
 for k in range(n):print(k,pairs[k])
