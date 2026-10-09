import struct, pathlib, hashlib, json
src=pathlib.Path(r'F:\Remaster Framework\source\MDK\FALL3D\FALL3D.BNI'); out=pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1\ir\KURT_FALL3D_structural.obj')
b=src.read_bytes(); cnt=struct.unpack_from('<I',b,4)[0]; ents=[]
for i in range(cnt):
 o=8+i*16; ents.append((b[o:o+12].split(b'\0')[0].decode('ascii','replace'),struct.unpack_from('<I',b,o+12)[0]))
idx=[i for i,x in enumerate(ents) if x[0]=='KURT'][0]; k=b[ents[idx][1]:ents[idx+1][1]]; starts=[44,3796,4800,5432,6100,7020,7688,8692,9276,9704,10372,12036,12428,13012,13680,14312,15232,16416]
lines=['# OpenMDK1 source-derived KURT']; vb=1; tv=tf=0; parts=[]
for s in starts:
 name=k[s:s+12].split(b'\0')[0].decode(); nv=struct.unpack_from('<I',k,s+24)[0]; vs=[struct.unpack_from('<3f',k,s+28+i*12) for i in range(nv)]; post=s+28+nv*12; nf=struct.unpack_from('<I',k,post)[0]; lines.append('o '+name)
 for x,y,z in vs: lines.append(f'v {x:.9g} {y:.9g} {z:.9g}')
 for j in range(nf):
  a,c,d,m=struct.unpack_from('<4H',k,post+4+j*36); assert max(a,c,d)<nv; lines.append(f'f {vb+a} {vb+c} {vb+d}')
 parts.append({'name':name,'vertices':nv,'triangles':nf}); vb+=nv; tv+=nv; tf+=nf
out.write_text('\n'.join(lines)+'\n'); manifest={'source':str(src),'source_sha256':hashlib.sha256(b).hexdigest(),'output':str(out),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'vertices':tv,'triangles':tf,'parts':parts}; pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1\evidence\kurt_manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({k:manifest[k] for k in ['source_sha256','output_sha256','vertices','triangles']},indent=2))
