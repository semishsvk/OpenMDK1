import struct,pathlib,json,hashlib
src=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO")
B=src.read_bytes(); cnt=struct.unpack_from("<I",B,20)[0]; BASE=0x14
out={"schema":"OpenMDK.MTOTexturePayload.v1","source":str(src),"source_sha256":hashlib.sha256(B).hexdigest(),"pointer_base":"0x14","payload_layout":"u16le width, u16le height, width*height indexed8 texels","hmos":{}}
total=passed=0; footer_pass=0
for bi in range(cnt):
 q=24+bi*12; hn=B[q:q+8].split(b"\0")[0].decode("ascii","replace"); s=struct.unpack_from("<I",B,q+8)[0]; e=struct.unpack_from("<I",B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; n=struct.unpack_from("<I",h,36)[0]
 recs=[]
 for i in range(n):
  name=h[40+i*24:40+i*24+20].split(b"\0")[0].decode("ascii","replace"); rel=struct.unpack_from("<I",h,40+i*24+20)[0]; a=BASE+rel; w,hh=struct.unpack_from("<HH",h,a); z=a+4+w*hh; tex=h[a+4:z]; ok=(z<=len(h) and len(tex)==w*hh); total+=1; passed+=int(ok)
  recs.append({"ordinal":i,"name":name,"relative_offset":rel,"absolute_offset":a,"width":w,"height":hh,"texel_count":len(tex),"texel_sha256":hashlib.sha256(tex).hexdigest(),"layout_ok":ok})
 footer=None
 if n:
  last=recs[-1]; image_end=last["absolute_offset"]+4+last["width"]*last["height"]; sec_end=BASE+struct.unpack_from("<I",h,4)[0]; f=h[image_end:sec_end]; sig=(hn+".MAT").encode(); fok=(len(f)==28 and f.startswith(sig+b"\0")); footer_pass+=int(fok)
  footer={"length":len(f),"signature":f[:12].split(b"\0")[0].decode("ascii","replace"),"hex":f.hex(),"ok":fok}
 out["hmos"][hn]={"material_count":n,"records":recs,"footer":footer}
out.update({"records_total":total,"records_pass":passed,"records_fail":total-passed,"footer_hmos_expected":9,"footer_hmos_pass":footer_pass,"status":"STRUCTURAL_PASS" if total==passed and footer_pass==9 else "FAIL","claim":"deterministic HMO material ordinal -> embedded indexed8 texture payload; palette/render-state/runtime fidelity remain separate gates"})
print(json.dumps(out,indent=2))
