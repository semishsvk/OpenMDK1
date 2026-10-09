import struct,pathlib,re,json,math
p=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO'); b=p.read_bytes(); cnt=struct.unpack_from('<I',b,20)[0]
ents=[]
for i in range(cnt):
 o=24+i*12; name=b[o:o+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',b,o+8)[0]; e=struct.unpack_from('<I',b,24+(i+1)*12+8)[0] if i+1<cnt else len(b); ents.append((name,s,e))

def printable_name(d,s):
 raw=d[s:s+12]; name=raw.split(b'\0')[0]; return bool(name) and all(32<=x<127 for x in name) and all(x==0 for x in raw[len(name):])
for name,s,e in ents:
 h=b[s:e]; c=[]
 for q in range(0,len(h)-64,4):
  if not printable_name(h,q): continue
  nv=struct.unpack_from('<I',h,q+24)[0]
  if not 3<=nv<=65535: continue
  post=q+28+nv*12
  if post+4>len(h): continue
  nf=struct.unpack_from('<I',h,post)[0]
  if not 1<=nf<=200000 or post+4+nf*36>len(h): continue
  ok=True
  for j in range(nf):
   a,x,y=struct.unpack_from('<3H',h,post+4+j*36)
   if max(a,x,y)>=nv: ok=False; break
  if ok: c.append((q,h[q:q+12].split(b'\0')[0].decode(),nv,nf))
 print(name,'embedded_meshes',len(c),'verts',sum(x[2] for x in c),'tris',sum(x[3] for x in c))
 print(' ',c[:12])
