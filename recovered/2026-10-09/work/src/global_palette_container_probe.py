import pathlib,struct,json,re,hashlib
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3")
files=[root/"LEVEL3O.MTO",root/"LEVEL3S.MTI",root/"LEVEL3.CMI"]
out={}
for p in files:
 b=p.read_bytes()
 entry={"size":len(b),"sha256":hashlib.sha256(b).hexdigest()}
 # Top-level first 256 bytes
 entry["first256_hex"]=b[:256].hex()
 # ASCII strings in first 4096
 entry["strings_first4096"]=[{"off":m.start(),"s":m.group()[:-1].decode("ascii","replace")} for m in re.finditer(rb"[A-Z0-9_\.]{3,20}\x00",b[:4096])][:100]
 out[p.name]=entry
# MTO top-level block offsets/table gap
b=(root/"LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",b,20)[0]
blocks=[]
for i in range(cnt):
 q=24+i*12
 name=b[q:q+8].split(b"\0")[0].decode()
 off=struct.unpack_from("<I",b,q+8)[0]
 blocks.append({"i":i,"name":name,"off":off})
table_end=24+cnt*12
first=blocks[0]["off"]
result={"schema":"OpenMDK.GlobalPaletteContainerProbe.v1","files":out,"mto":{"count":cnt,"table_end":table_end,"blocks":blocks,"gap_len":first-table_end,"gap_hex":b[table_end:first].hex()}}
print(json.dumps(result,indent=2))
