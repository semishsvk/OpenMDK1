import struct,pathlib,json
src=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO")
outdir=pathlib.Path(r"F:\Remaster Framework\work\OpenMDK1\decoded\level3_textures");outdir.mkdir(parents=True,exist_ok=True)
B=src.read_bytes();cnt=struct.unpack_from("<I",B,20)[0];manifest=[]
for bi in range(cnt):
 q=24+bi*12;hn=B[q:q+8].split(b"\0")[0].decode();s=struct.unpack_from("<I",B,q+8)[0];e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B);h=B[s:e];n=struct.unpack_from("<I",h,36)[0]
 for i in range(n):
  r=40+i*24;name=h[r:r+16].split(b"\0")[0].decode("ascii","replace");o=struct.unpack_from("<I",h,r+20)[0];w,hh=struct.unpack_from("<2H",h,o+20);pix=h[o+24:o+24+w*hh]
  fn=f"{hn}_{i:02d}_{name}.idx8";(outdir/fn).write_bytes(pix);manifest.append({"hmo":hn,"ordinal":i,"name":name,"width":w,"height":hh,"bytes":len(pix),"file":fn})
(outdir/"manifest.json").write_text(json.dumps(manifest,indent=2))
print("textures",len(manifest),"bytes",sum(x["bytes"] for x in manifest));print(json.dumps(manifest[:20],indent=2))
