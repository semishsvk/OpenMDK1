import struct,pathlib,json
B=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO").read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
BASE=0x14
out={}
for bi in range(cnt):
    q=24+bi*12
    hn=B[q:q+8].split(b"\0")[0].decode("ascii","replace")
    s=struct.unpack_from("<I",B,q+8)[0]
    e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
    h=B[s:e]
    n=struct.unpack_from("<I",h,36)[0]
    if not n:
        out[hn]={"count":0}
        continue
    last_rel=struct.unpack_from("<I",h,40+(n-1)*24+20)[0]
    a=BASE+last_rel
    w,hh=struct.unpack_from("<HH",h,a)
    image_end=a+4+w*hh
    section_end=BASE+struct.unpack_from("<I",h,4)[0]
    footer=h[image_end:section_end]
    out[hn]={"last_name":h[40+(n-1)*24:40+(n-1)*24+20].split(b"\0")[0].decode("ascii","replace"),"w":w,"h":hh,"image_end":image_end,"section_end":section_end,"footer_len":len(footer),"footer_hex":footer.hex(),"footer_u32":list(struct.unpack("<7I",footer)) if len(footer)==28 else []}
print(json.dumps(out,indent=2))
