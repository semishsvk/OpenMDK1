import pathlib,struct,json,hashlib
from PIL import Image
root=pathlib.Path(r"F:\Remaster Framework\source\MDK")
work=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1")
outdir=work/"decoded"/"runtime_palette_v2"
outdir.mkdir(parents=True,exist_ok=True)

# fixed64 from SYS_PAL
fti=(root/"MISC"/"mdkfont.fti").read_bytes()
fobj=fti[4:]
cnt=struct.unpack_from("<I",fobj,0)[0]
recs=[]
for i in range(cnt):
    o=4+i*12
    name=fobj[o:o+8].split(b"\0")[0].decode("ascii","replace")
    off=struct.unpack_from("<I",fobj,o+8)[0]
    recs.append((name,off))
si=next(i for i,(n,_) in enumerate(recs) if n=="SYS_PAL")
fixed64=fobj[recs[si][1]:recs[si+1][1]]
assert len(fixed64)==192

# corrected LEVEL3.DTI palette relative to object after size prefix
dti=(root/"TRAVERSE"/"LEVEL3"/"LEVEL3.DTI").read_bytes()
dobj=dti[4:]
pp=struct.unpack_from("<I",dobj,0x1c)[0]+4
dpal=dobj[pp:pp+768]
assert len(dpal)==768
assert dpal[:192]==fixed64
global80=dpal[176*3:256*3]
assert len(global80)==240

# MTO textures + per-HMO local112
M=(root/"TRAVERSE"/"LEVEL3"/"LEVEL3O.MTO").read_bytes()
hcnt=struct.unpack_from("<I",M,20)[0]
wanted={"HMO_1":{"H1_FRONT","H1_BLD1","H1_FLR"},"HMO_4":{"H4_SKY","H4_MUD"},"HMO_9":{"H9_W1","H9_W3"},"HMO_10":{"H10_FLR","H10_MWAL"}}
manifest=[]
for bi in range(hcnt):
    q=24+bi*12
    hn=M[q:q+8].split(b"\0")[0].decode()
    bs=struct.unpack_from("<I",M,q+8)[0]
    be=struct.unpack_from("<I",M,24+(bi+1)*12+8)[0] if bi+1<hcnt else len(M)
    h=M[bs:be]
    local_ptr=struct.unpack_from("<I",h,8)[0]+4
    local112=h[local_ptr:local_ptr+336]
    if len(local112)!=336: continue
    palette=fixed64+local112+global80
    assert len(palette)==768
    n=struct.unpack_from("<I",h,36)[0]
    for i in range(n):
        r=40+i*24
        name=h[r:r+20].split(b"\0")[0].decode("ascii","replace")
        if hn not in wanted or name not in wanted[hn]: continue
        rel=struct.unpack_from("<I",h,r+20)[0]
        a=20+rel
        w,hh=struct.unpack_from("<HH",h,a)
        pix=h[a+4:a+4+w*hh]
        rgb=bytearray(w*hh*3)
        for j,idx in enumerate(pix):
            rgb[j*3:j*3+3]=palette[idx*3:idx*3+3]
        fn=f"{hn}_{i:02d}_{name}.png".replace("\\","_").replace("/","_")
        Image.frombytes("RGB",(w,hh),bytes(rgb)).save(outdir/fn)
        manifest.append({"hmo":hn,"ordinal":i,"name":name,"width":w,"height":hh,"file":fn,
                         "pixel_sha256":hashlib.sha256(bytes(rgb)).hexdigest()})
(outdir/"manifest.json").write_text(json.dumps({
 "schema":"OpenMDK.RuntimePalettePreview.v2",
 "palette_model":"SYS_PAL[0..63] + HMO local112[64..175] + LEVEL3.DTI global80[176..255]",
 "fixed64_sha256":hashlib.sha256(fixed64).hexdigest(),
 "global80_sha256":hashlib.sha256(global80).hexdigest(),
 "global80_first24":global80[:24].hex(),
 "fidelity_claim":False,
 "textures":manifest
},indent=2),encoding="utf-8")
print(json.dumps({"count":len(manifest),"files":[x["file"] for x in manifest],
                  "global80_sha256":hashlib.sha256(global80).hexdigest(),
                  "global80_unique_rgb":len(set(tuple(global80[i:i+3]) for i in range(0,len(global80),3)))},indent=2))
