import pathlib,struct,re,json
root=pathlib.Path(r"F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3")
M=(root/"LEVEL3O.MTO").read_bytes(); C=(root/"LEVEL3.CMI").read_bytes(); T=(root/"LEVEL3S.MTI").read_bytes()
cnt=struct.unpack_from("<I",M,20)[0]; names=[]
for bi in range(cnt):
 q=24+bi*12;s=struct.unpack_from("<I",M,q+8)[0];e=struct.unpack_from("<I",M,24+(bi+1)*12+8)[0] if bi+1<cnt else len(M);h=M[s:e];n=struct.unpack_from("<I",h,36)[0]
 for i in range(n):
  x=h[40+i*24:40+(i+1)*24].split(b"\0")[0]
  if x and all(32<=b<127 for b in x): names.append(x.decode())
out={}
for name in sorted(set(names)):
 b=name.encode(); co=[];to=[];p=0
 while True:
  p=C.find(b,p)
  if p<0:break
  co.append(p);p+=1
 p=0
 while True:
  p=T.find(b,p)
  if p<0:break
  to.append(p);p+=1
 out[name]={"CMI":co[:8],"MTI":to[:8]}
print(json.dumps(out,indent=2))
