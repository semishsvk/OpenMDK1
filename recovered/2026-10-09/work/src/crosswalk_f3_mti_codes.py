import pathlib,struct,math,json,collections
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3")
M=(root/"LEVEL3O.MTO").read_bytes()
T=(root/"LEVEL3S.MTI").read_bytes()

# MTI code namespace
tc=struct.unpack_from("<I",T,20)[0]
by_code=collections.defaultdict(list)
mti_records=[]
for i in range(tc):
    o=24+i*24
    name=T[o:o+8].split(b"\0")[0].decode("ascii","replace")
    u16a,u16b=struct.unpack_from("<HH",T,o+8)
    code=struct.unpack_from("<I",T,o+12)[0]
    f=struct.unpack_from("<f",T,o+16)[0]
    off=struct.unpack_from("<I",T,o+20)[0]
    rec={"i":i,"name":name,"u16a":u16a,"u16b":u16b,"code":code,"f":f,"off":off}
    mti_records.append(rec); by_code[code].append(rec)

# all triangle signed f3
hcnt=struct.unpack_from("<I",M,20)[0]
neg=collections.Counter(); pos=collections.Counter(); zero=0
per_hmo={}
for bi in range(hcnt):
    q=24+bi*12; hn=M[q:q+8].split(b"\0")[0].decode()
    s=struct.unpack_from("<I",M,q+8)[0]; e=struct.unpack_from("<I",M,24+(bi+1)*12+8)[0] if bi+1<hcnt else len(M)
    h=M[s:e]
    g0=struct.unpack_from("<I",h,12)[0]+4; nc=struct.unpack_from("<I",h,g0)[0]
    aligned=(g0+4+nc*10+3)&~3; pc=struct.unpack_from("<I",h,aligned)[0]
    toff=aligned+4+pc*44; tn=struct.unpack_from("<I",h,toff)[0]; tb=toff+4
    c=collections.Counter()
    for i in range(tn):
        f3=struct.unpack_from("<h",h,tb+i*36+6)[0]
        c[f3]+=1
        if f3<0:neg[-f3]+=1
        elif f3>0:pos[f3]+=1
        else:zero+=1
    per_hmo[hn]=dict(c)

mapped={}; unmapped={}
mapped_tri=0; neg_tri=sum(neg.values())
for code,count in sorted(neg.items()):
    names=[r["name"] for r in by_code.get(code,[])]
    if names:
        mapped[str(code)]={"triangles":count,"records":names}
        mapped_tri+=count
    else:
        unmapped[str(code)]=count

special=[r for r in mti_records if r["name"] in ("GLASS1","GLASS2","GLASS3","GLASS4","MIRRLOW","MIRRMED","BLACK","DARK","SHADOW","WHITE","BCYAN","NONE")]
print(json.dumps({
 "schema":"OpenMDK.TriangleF3MTICrosswalk.v1",
 "mti_record_count":tc,
 "negative_f3_unique_codes":len(neg),
 "negative_f3_triangles":neg_tri,
 "negative_f3_mapped_triangles":mapped_tri,
 "negative_f3_mapping_ratio":mapped_tri/neg_tri if neg_tri else 0,
 "mapped_codes":mapped,
 "unmapped_codes":unmapped,
 "positive_f3":dict(sorted(pos.items())),
 "zero_f3_triangles":zero,
 "special_mti_records":special,
 "per_hmo_signed_f3":per_hmo
},indent=2))
