import struct,pathlib,math,statistics
B=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes(); h=B[5365624:5418404]; pbase=0x1b0; pn=349; tbase=0x3db0; tn=875; vbase=tbase+tn*36; nv=struct.unpack_from('<I',h,vbase)[0]; print('vertex_count',nv,'vbase',hex(vbase)); verts=[struct.unpack_from('<3f',h,vbase+4+i*12) for i in range(nv)]; print('firstverts',verts[:8]); print('AABB',tuple(min(v[k] for v in verts) for k in range(3)),tuple(max(v[k] for v in verts) for k in range(3)))
tris=[]; bad=0
for i in range(tn):
 a,b,c,flag=struct.unpack_from('<4H',h,tbase+i*36); tris.append((a,b,c,flag)); bad+=max(a,b,c)>=nv
print('triangles',len(tris),'bad_indices',bad,'flaguniq',len(set(t[3] for t in tris)))
# plane table record: first_index/count map each plane to triangles; residual abs(n dot v + d), both sign conventions reported
res1=[];res2=[]; checked=0
for i in range(pn):
 o=pbase+i*44; nx,ny,nz,d=struct.unpack_from('<4f',h,o); tail=struct.unpack_from('<14H',h,o+16); count,first=tail[2],tail[3]
 for ti in range(first,first+count):
  if ti>=tn: continue
  for vi in tris[ti][:3]:
   x,y,z=verts[vi]; res1.append(abs(nx*x+ny*y+nz*z+d)); res2.append(abs(nx*x+ny*y+nz*z-d)); checked+=1
print('checked_vertices',checked,'res +d median/max',statistics.median(res1),max(res1),'res -d median/max',statistics.median(res2),max(res2)); print('within1e-3 +d',sum(x<1e-3 for x in res1),'/',len(res1))
