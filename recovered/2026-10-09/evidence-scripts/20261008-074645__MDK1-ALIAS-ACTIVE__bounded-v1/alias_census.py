"""Locate the exact 22 nonpayload references without guessing how they render."""
from verify_f3_contract import MTO,MTI,MTO_PIN,u32,name
from static_probe import ROOT,sha
import struct,json
b=MTO.read_bytes();m=MTI.read_bytes();assert sha(b)==MTO_PIN
primary={name(m[24+24*i:32+24*i]):(u32(m,32+24*i),u32(m,36+24*i)) for i in range(u32(m,20))}
rows=[];parts=[]
for i in range(u32(b,20)):
    q=24+12*i;hn=name(b[q:q+8]);s=u32(b,q+8);e=u32(b,q+20) if i+1<u32(b,20) else len(b);h=b[s:e]
    g=u32(h,12)+4;nc=u32(h,g);names=[name(h[g+4+j*10:g+14+j*10]) for j in range(nc)]
    pcpos=(g+4+10*nc+3)&~3;pc=u32(h,pcpos);tp=pcpos+4+44*pc;tc=u32(h,tp);tb=tp+4;vp=tb+36*tc;nv=u32(h,vp);vb=vp+4;ip=vb+12*nv;ic=u32(h,ip);ib=ip+4
    if ib>len(h):raise ValueError('INDEX_BOUNDS')
    parts.append({'hmo':hn,'pc':pc,'tc':tc,'nv':nv,'index_header':ic,'index_bytes':len(h)-ib,
       'first_planes':[list(struct.unpack_from('<11I',h,pcpos+4+j*44)) for j in range(min(pc,3))],
       'first_tail_words':list(struct.unpack_from('<16H',h,ib))})
    for j in range(tc):
        pos=tb+36*j;verts=struct.unpack_from('<3H',h,pos);code=struct.unpack_from('<h',h,pos+6)[0]
        if code>=0 and names[code] in primary and primary[names[code]][0]==0xffffffff:
            rows.append({'hmo':hn,'record':j,'code':code,'name':names[code],'pen':primary[names[code]][1],
              'vertices':verts,'flag_u32':u32(h,pos+32),'record_hex':h[pos:pos+36].hex(),
              'vertex_positions':[struct.unpack_from('<3f',h,vb+12*v) if v<nv else None for v in verts]})
with (ROOT/'alias-reference-census.json').open('x',encoding='utf-8') as f:json.dump({'rows':rows,'parts':parts},f,indent=2)
print('ALIAS_COUNT',len(rows))
for r in rows:print(json.dumps(r))
print('PART_LAYOUT',json.dumps(parts[:2],indent=2))
