import pathlib,struct,json
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
# known PE mapping from dumpbin: DGROUP RVA 0x94000, raw ptr 0x92400
image=0x400000; rva0=0x94000; raw0=0x92400
addrs=[0x4975E4,0x4975FC,0x497608,0x497620,0x49765C,0x497668]
out={}
for va in addrs:
 off=raw0+((va-image)-rva0)
 raw=b[off:off+96]
 z=raw.find(b"\0")
 s=raw[:z if z>=0 else len(raw)].decode("latin1","replace")
 out[hex(va)]={"file_offset":off,"string":s,"first32":raw[:32].hex()}
print(json.dumps(out,indent=2))
