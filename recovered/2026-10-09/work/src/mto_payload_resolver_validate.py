import json, pathlib, struct, hashlib
src=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO")
B=src.read_bytes()
cnt=struct.unpack_from("<I",B,20)[0]
BASE=0x14
total=0
passed=0
fail=[]
summary={}
for bi in range(cnt):
    q=24+bi*12
    hname=B[q:q+8].split(b"\0")[0].decode("ascii","replace")
    s=struct.unpack_from("<I",B,q+8)[0]
    e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B)
    h=B[s:e]
    n=struct.unpack_from("<I",h,36)[0]
    rel=[struct.unpack_from("<I",h,40+i*24+20)[0] for i in range(n)]
    abs_off=[BASE+x for x in rel]
    end=BASE+struct.unpack_from("<I",h,4)[0]
    recs=[]
    for i,a in enumerate(abs_off):
        z=abs_off[i+1] if i+1<n else end
        seg=h[a:z]
        name=h[40+i*24:40+i*24+20].split(b"\0")[0].decode("ascii","replace")
        total+=1
        if len(seg)>=4:
            w,hgt=struct.unpack_from("<HH",seg,0)
            ok=(len(seg)==4+w*hgt)
        else:
            w=hgt=0; ok=False
        if ok: passed+=1
        else: fail.append({"hmo":hname,"ordinal":i,"name":name,"size":len(seg),"w":w,"h":hgt,"expected":4+w*hgt})
        recs.append({"ordinal":i,"name":name,"width":w,"height":hgt,"size":len(seg),"raw_indexed8":ok,"texel_sha256":hashlib.sha256(seg[4:]).hexdigest() if ok else None})
    summary[hname]={"count":n,"records":recs}
out={"schema":"OpenMDK.MTOPayloadResolver.v1","source":"LEVEL3O.MTO","pointer_base":"0x14","payload_layout":"u16le width + u16le height + width*height bytes indexed8","records_total":total,"records_pass":passed,"records_fail":len(fail),"failures":fail,"hmos":summary,"status":"STRUCTURAL_PASS" if total==passed else "FAIL"}
print(json.dumps(out,indent=2))
