import struct,pathlib,math,json,hashlib
src=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO'); B=src.read_bytes(); cnt=struct.unpack_from('<I',B,20)[0]; allv=[]; allf=[]; rep=[]
for bi in range(cnt):
 q=24+bi*12; name=B[q:q+8].split(b'\0')[0].decode(); s=struct.unpack_from('<I',B,q+8)[0]; e=struct.unpack_from('<I',B,24+(bi+1)*12+8)[0] if bi+1<cnt else len(B); h=B[s:e]; geom=struct.unpack_from('<I',h,12)[0]
 # choose phase maximizing normalized plane records at stride44
 best=[]; bestphase=0
 for phase in range(44):
  rr=[]
  for o in range(geom+phase,len(h)-44,44):
   x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
   if all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000: rr.append(o)
  if len(rr)>len(best): best,bestphase=rr,phase
 if not best: continue
 # require contiguous 44 sequence from first to last
 p0=best[0]; pn=0
 while p0+(pn+1)*44<len(h):
  o=p0+pn*44; x,y,z,d=struct.unpack_from('<4f',h,o); n=x*x+y*y+z*z
  if not(all(math.isfinite(v) for v in (x,y,z,d)) and .999<n<1.001 and abs(d)<10000): break
  pn+=1
 pend=p0+pn*44; tn=struct.unpack_from('<I',h,pend)[0]; tbase=pend+4; vpos=tbase+tn*36
 if vpos+4>len(h): print(name,'bad t range'); continue
 nv=struct.unpack_from('<I',h,vpos)[0]; vbase=vpos+4
 if vbase+nv*12>len(h): print(name,'bad v range',pn,tn,nv); continue
 verts=[struct.unpack_from('<3f',h,vbase+i*12) for i in range(nv)]; tris=[struct.unpack_from('<4H',h,tbase+i*36) for i in range(tn)]; bad=sum(max(t[:3])>=nv for t in tris)
 baseidx=len(allv)+1; allv+=verts; allf += [(baseidx+a,baseidx+b,baseidx+c) for a,b,c,_ in tris if max(a,b,c)<nv]
 rep.append({'hmo':name,'planes':pn,'triangles':tn,'vertices':nv,'bad_indices':bad,'plane_start':p0})
 print(name,'planes',pn,'tris',tn,'verts',nv,'bad',bad)
out=pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1\ir\LEVEL3_world_structural.obj'); lines=['# OpenMDK1 LEVEL3 MTO source-derived structural world mesh']+[f'v {x} {y} {z}' for x,y,z in allv]+[f'f {a} {b} {c}' for a,b,c in allf]; out.write_text('\n'.join(lines)+'\n'); print('TOTAL verts',len(allv),'tris',len(allf),'sha',hashlib.sha256(out.read_bytes()).hexdigest()); pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1\evidence\level3_world_manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(B).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'vertices':len(allv),'triangles':len(allf),'parts':rep},indent=2))
