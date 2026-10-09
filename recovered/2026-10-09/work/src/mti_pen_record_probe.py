import pathlib,struct,json,re,hashlib
p=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3S.MTI")
b=p.read_bytes()
count=struct.unpack_from("<I",b,20)[0]
recs=[]
for i in range(count):
    o=24+i*24
    name=b[o:o+8].split(b"\0")[0].decode("ascii","replace")
    u16a,u16b=struct.unpack_from("<HH",b,o+8)
    u32=struct.unpack_from("<I",b,o+12)[0]
    f=struct.unpack_from("<f",b,o+16)[0]
    off=struct.unpack_from("<I",b,o+20)[0]
    nextoff=struct.unpack_from("<I",b,24+(i+1)*24+20)[0] if i+1<count else len(b)
    if name.startswith("PEN_"):
        seg=b[off:nextoff] if off < len(b) and nextoff>=off else b""
        recs.append({"i":i,"name":name,"u16a":u16a,"u16b":u16b,"u32":u32,"f":f,"off":off,"next":nextoff,"payload_len":len(seg),"payload_first32":seg[:32].hex(),"payload_sha256":hashlib.sha256(seg).hexdigest() if seg else None})
print(json.dumps({"schema":"OpenMDK.MTIPenRecordProbe.v1","count":count,"pen_records":recs},indent=2))
