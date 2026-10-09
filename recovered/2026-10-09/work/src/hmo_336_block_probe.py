import pathlib,struct,hashlib,json,collections
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes(); cnt=struct.unpack_from("<I",B,20)[0]
out={}
chunks=[]
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; a=struct.unpack_from("<I",h,8)[0]; z=struct.unpack_from("<I",h,12)[0]; c=h[a:z]; chunks.append(c)
 out[hn]={"a":a,"z":z,"length":len(c),"sha256":hashlib.sha256(c).hexdigest(),"unique":len(set(c)),"first64":c[:64].hex(),"last32":c[-32:].hex()}
print(json.dumps({"all_equal":all(c==chunks[0] for c in chunks[1:]),"unique_hashes":len(set(hashlib.sha256(c).hexdigest() for c in chunks)),"blocks":out},indent=2))
