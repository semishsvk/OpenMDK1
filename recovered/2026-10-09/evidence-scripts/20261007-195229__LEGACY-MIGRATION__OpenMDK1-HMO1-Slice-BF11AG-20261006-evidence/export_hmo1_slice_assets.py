import pathlib,struct,json,hashlib,zlib,collections
from collision_port import Collision
root=pathlib.Path('slice_project');(root/'textures').mkdir(parents=True,exist_ok=True)
b=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes();assert hashlib.sha256(b).hexdigest()=='6f33536701f57a404f8b25aa5580502cd68389de9ae591b53b018f415f7193ff'
payload=0x94;container=payload+12;palette=b[payload+894904:payload+894904+768]
def png(path,w,h,rgb):
 def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
 raw=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
textures={}
for i in range(21):
 p=container+24+24*i;name=b[p:p+8].split(b'\0')[0].decode();off=container+4+struct.unpack_from('<I',b,p+20)[0];w,h=struct.unpack_from('<2H',b,off);pix=b[off+4:off+4+w*h];assert len(pix)==w*h and w*h>0
 rgb=b''.join(palette[v*3:v*3+3] for v in pix);png(root/'textures'/(name+'.png'),w,h,rgb);textures[name]=dict(width=w,height=h,raw_offset=off,path='textures/'+name+'.png')
names=[b[0xda9a0+i*10:0xda9a0+(i+1)*10].split(b'\0')[0].decode() for i in range(20)]
verts=[struct.unpack_from('<3f',b,0xe0d30+i*12) for i in range(234)]
faces=[]
for i in range(399):
 a,c,d,mat,*rest=struct.unpack_from('<4H6fI',b,0xdd510+i*36)
 if len({a,c,d})<3:continue
 assert max(a,c,d)<234
 mat=mat if mat<32768 else mat-65536
 assert mat<20,(i,mat)
 material=names[mat] if mat>=0 else 'PEN_'+str(-mat)
 faces.append(dict(indices=[a,c,d],material=material,uv=[[rest[0],rest[1]],[rest[2],rest[3]],[rest[4],rest[5]]],flags=rest[6],source_face=i))
nodes=[]
for i in range(248):
 o=0xdaa6c+i*44;plane=struct.unpack_from('<4f',b,o);neg,pos=struct.unpack_from('<2h',b,o+16);a,aa,c,cc=struct.unpack_from('<HhHh',b,o+20)
 nodes.append(dict(plane=plane,negative=neg,positive=pos,leaves=[[a,aa],[c,cc]]))
allfaces=[]
for i in range(399):
 o=0xdd510+i*36;allfaces.append(dict(indices=struct.unpack_from('<3H',b,o),flags=b[o+32]))
c=Collision(b,0xdaa6c,0xdd510,0xe0d30)
cases=[]
import random
rng=random.Random(771)
for i in range(300):
 start=tuple(rng.uniform(-500,500) for _ in range(3));end=tuple(rng.uniform(-500,500) for _ in range(3));hit=c.query(start,end);cases.append(dict(start=start,end=end,hit=list(hit[:2]) if hit else None,point=list(hit[2]) if hit else None))
waypoints=[];last=[-4,0,190]
for delta in [[8,0,0],[0,8,0],[-8,0,0],[0,-8,0],[0,0,8],[0,0,-8]]:
 p=[last[k]+delta[k] for k in range(3)]
 if c.query(last,p) is None and p not in waypoints and p!=[-4,0,190]:waypoints.append(p);last=p
 if len(waypoints)==3:break
if len(waypoints)<3:
 waypoints=[[-4,0,186],[-4,0,182],[-4,0,178]];last=[-4,0,190]
 for p in waypoints:assert c.query(last,p) is None;last=p
print('waypoints',waypoints)
waypoints=[[-220,-200,446],[-220,-200,442],[-220,-200,438]]
last=[-220,-200,450]
for p in waypoints:assert c.query(last,p) is None;last=p
ir=dict(schema='OpenMDK.ExperimentalSliceIR.v1',source_sha256=hashlib.sha256(b).hexdigest(),vertices=verts,faces=faces,textures=textures,nodes=nodes,collision_faces=allfaces,collision_cases=cases,seed=[-4,0,190,96],waypoints=waypoints,limitations=['Recovered RenderIR exporter from prior ChatGPT session is unavailable in accessible workspace. This adapter uses validated HMO1 packed collision faces for an experimental textured mesh, not full token-native render geometry.','UV values come from original face records and are normalized by texture dimensions; visual semantics not retail-oracle validated.','PEN materials use the original palette index as solid color.','Slice flight camera and beacon objective are experimental; no retail gameplay fidelity claim.'])
(root/'hmo1.json').write_text(json.dumps(ir));print('TEXTURES',len(textures),'FACES',len(faces),collections.Counter(f['material'] for f in faces));print('bounds',[(min(v[k] for v in verts),max(v[k] for v in verts)) for k in range(3)])
(root/'palette.json').write_text(json.dumps([list(palette[i*3:i*3+3]) for i in range(256)]))
