import pathlib,struct,json,hashlib
from PIL import Image
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3")
work=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1")
outdir=work/"decoded"/"palette_hypothesis_v1"
outdir.mkdir(parents=True,exist_ok=True)
M=(root/"LEVEL3O.MTO").read_bytes()
D=(root/"LEVEL3.DTI").read_bytes()
# Cross-level-validated DTI palette-like section: header[8]..header[9] = 772 = 4+768
hdr=struct.unpack_from("<10I",D,0); s8,e8=hdr[8],hdr[9]
base256=D[s8+4:e8]
assert len(base256)==768
global144=base256[:432]
cnt=struct.unpack_from("<I",M,20)[0]
wanted={"HMO_1":{"H1_FRONT","H1_BLD1","H1_FLR"},"HMO_4":{"H4_SKY","H4_MUD"},"HMO_9":{"H9_W1","H9_W3"},"HMO_10":{"H10_FLR","H10_MWAL"}}
manifest=[]
for bi in range(cnt):
 q=24+bi*12; hn=M[q:q+8].split(b"\0")[0].decode(); bs=struct.unpack_from("<I",M,q+8)[0]; be=struct.unpack_from("<I",M,24+(bi+1)*12+8)[0] if bi+1<cnt else len(M); h=M[bs:be]
 # verified local 112 palette starts at header field2 +4 correction
 local_start=struct.unpack_from("<I",h,8)[0]+4
 local=h[local_start:local_start+336]
 if len(local)!=336: continue
 palette=global144+local
 if len(palette)!=768: continue
 n=struct.unpack_from("<I",h,36)[0]
 for i in range(n):
  r=40+i*24; name=h[r:r+20].split(b"\0")[0].decode("ascii","replace")
  if hn not in wanted or name not in wanted[hn]: continue
  rel=struct.unpack_from("<I",h,r+20)[0]; a=20+rel; w,hh=struct.unpack_from("<HH",h,a); pix=h[a+4:a+4+w*hh]
  rgb=bytearray(w*hh*3)
  for j,idx in enumerate(pix):
   rgb[j*3:j*3+3]=palette[idx*3:idx*3+3]
  im=Image.frombytes("RGB",(w,hh),bytes(rgb))
  fn=f"{hn}_{i:02d}_{name}.png".replace("\\","_").replace("/","_")
  im.save(outdir/fn)
  manifest.append({"hmo":hn,"ordinal":i,"name":name,"width":w,"height":hh,"file":fn,"pixel_sha256":hashlib.sha256(bytes(rgb)).hexdigest()})
(outdir/"manifest.json").write_text(json.dumps({"schema":"OpenMDK.PaletteHypothesisPreview.v1","palette_model":"LEVEL3.DTI section first144 + HMO local112","fidelity_claim":False,"textures":manifest},indent=2),encoding="utf-8")
print(json.dumps({"count":len(manifest),"files":[x["file"] for x in manifest]},indent=2))
