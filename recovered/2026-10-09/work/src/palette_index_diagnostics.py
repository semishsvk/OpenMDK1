import pathlib,struct,json,collections
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3")
M=(root/"LEVEL3O.MTO").read_bytes(); D=(root/"LEVEL3.DTI").read_bytes()
hdr=struct.unpack_from("<10I",D,0); base=D[hdr[8]+4:hdr[9]]
cnt=struct.unpack_from("<I",M,20)[0]; out={}
for bi in range(cnt):
 q=24+bi*12; hn=M[q:q+8].split(b"\0")[0].decode(); s=struct.unpack_from("<I",M,q+8)[0]; e=struct.unpack_from("<I",M,24+(bi+1)*12+8)[0] if bi+1<cnt else len(M); h=M[s:e]
 local_start=struct.unpack_from("<I",h,8)[0]+4; local=h[local_start:local_start+336]
 palette=base[:432]+local
 n=struct.unpack_from("<I",h,36)[0]; idx=collections.Counter()
 for i in range(n):
  r=40+i*24; rel=struct.unpack_from("<I",h,r+20)[0]; a=20+rel; w,hh=struct.unpack_from("<HH",h,a); idx.update(h[a+4:a+4+w*hh])
 tops=[]
 for val,count in idx.most_common(24):
  rgb=list(palette[val*3:val*3+3]); base_rgb=list(base[val*3:val*3+3])
  tops.append({"index":val,"count":count,"segment":"global" if val<144 else "local","combined_rgb":rgb,"dti_base_rgb":base_rgb})
 out[hn]={"pixels":sum(idx.values()),"global_pixels":sum(c for v,c in idx.items() if v<144),"local_pixels":sum(c for v,c in idx.items() if v>=144),"top":tops}
print(json.dumps({"schema":"OpenMDK.PaletteIndexDiagnostics.v1","hmos":out},indent=2))
