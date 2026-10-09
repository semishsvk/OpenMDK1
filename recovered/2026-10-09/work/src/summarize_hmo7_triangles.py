import json,subprocess,sys
base=r"F:\Remaster Framework\work\OpenMDK1\src"
def run(name):
 p=subprocess.run(["python",base+"\\"+name],capture_output=True)
 raw=p.stdout
 text=raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else raw.decode("utf-8")
 return json.loads(text)
sel=run("triangle_selector_audit.py")["HMO_7"]
flags=run("triangle_flag_audit.py")["HMO_7"]
u16=run("triangle_u16_audit.py")["HMO_7"]
print("selector",json.dumps(sel,indent=2))
print("flags",json.dumps(flags,indent=2))
print("u16_unique",u16["u16_unique"])
print("u16_top")
for i,x in enumerate(u16["u16_top"]): print(i,x)
