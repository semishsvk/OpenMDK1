import pathlib,struct,re,json,collections,math
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3");out={}
for fn in ["LEVEL3O.SNI","LEVEL3S.SNI"]:
 b=(root/fn).read_bytes(); strings=[{"off":m.start(),"s":m.group().decode("ascii","replace")} for m in re.finditer(rb'[A-Za-z0-9_.$-]{4,40}',b[:262144])][:200]
 out[fn]={"size":len(b),"head_hex":b[:128].hex(),"u32_head":list(struct.unpack_from("<32I",b,0)),"strings":strings}
print(json.dumps(out,indent=2))
