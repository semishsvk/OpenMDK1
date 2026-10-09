"""Deterministic read-only LEVEL3 parser, following the observed 0x419ee0 layout.
No normalization that drops multiplicity, aliases, inactive records or provenance.
"""
from pathlib import Path
import hashlib,math,struct
SOURCE=Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3')
PINS={'LEVEL3O.MTO':'6f33536701f57a404f8b25aa5580502cd68389de9ae591b53b018f415f7193ff',
 'LEVEL3S.MTI':'f5e77aae64ad9afe74962b5a93a85983eaa59f71fa4dbc1691fe0c5f74bb6694'}
def sha(b):return hashlib.sha256(b).hexdigest()
def take(b,o,n):
    if o<0 or n<0 or o+n>len(b):raise ValueError('SOURCE_BOUNDS')
    return b[o:o+n]
def unpack(b,o,fmt):return struct.unpack(fmt,take(b,o,struct.calcsize(fmt)))
def u32(b,o):return unpack(b,o,'<I')[0]
def name(raw):return raw.split(b'\0',1)[0].decode('ascii')
def corpus():
    data={n:(SOURCE/n).read_bytes() for n in PINS}
    if any(sha(data[n])!=h for n,h in PINS.items()):raise ValueError('SOURCE_PIN_MISMATCH')
    b,m=data['LEVEL3O.MTO'],data['LEVEL3S.MTI'];n=u32(b,20)
    if not 1<=n<=64:raise ValueError('DIRECTORY_BUDGET')
    ends=[u32(b,32+12*i) for i in range(n)]+[len(b)]
    if ends!=sorted(set(ends)) or ends[0]<24+n*12:raise ValueError('DIRECTORY_ORDER')
    primary=[]
    for i in range(u32(m,20)):
        q=24+24*i;raw=take(m,q,24)
        primary.append({'name':name(raw[:8]),'kind':u32(raw,8),'value':u32(raw,12),'ordinal':i})
    if len(primary)>1024:raise ValueError('PRIMARY_COUNT_BUDGET')
    parts=[]
    for i in range(n):
        h=take(b,ends[i],ends[i+1]-ends[i]);g=u32(h,12)+4;nc=u32(h,g)
        if not 1<=nc<=512:raise ValueError('NAME_COUNT')
        names=[name(take(h,g+4+10*j,10)) for j in range(nc)]
        ppos=(g+4+nc*10+3)&~3;pc=u32(h,ppos);pb=ppos+4
        if not 1<=pc<=10000:raise ValueError('PLANE_BUDGET')
        tp=pb+44*pc;tc=u32(h,tp);tb=tp+4
        if not 1<=tc<=10000:raise ValueError('TRIANGLE_BUDGET')
        vp=tb+tc*36;nv=u32(h,vp);vb=vp+4
        if nv>10000:raise ValueError('VERTEX_BUDGET')
        vertices=[unpack(h,vb+j*12,'<3f') for j in range(nv)]
        if not all(math.isfinite(v) for xyz in vertices for v in xyz):raise ValueError('NONFINITE_VERTEX')
        tris=[]
        for j in range(tc):
            raw=take(h,tb+j*36,36);vs=unpack(raw,0,'<3H');code=unpack(raw,6,'<h')[0]
            if max(vs)>=nv or (code>=0 and code>=nc):raise ValueError('REFERENCE_OUT_OF_RANGE')
            a,bb,c=[vertices[v] for v in vs];ab=[bb[k]-a[k] for k in range(3)];ac=[c[k]-a[k] for k in range(3)]
            cross=(ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0])
            tris.append({'index':j,'raw_file_offset':ends[i]+tb+j*36,'f3':code,
                'name':names[code] if code>=0 else None,'vertices':vs,'flag32':u32(raw,32),
                'zero_area':cross==(0,0,0),'raw_hex':raw.hex()})
        planes=[]
        for j in range(pc):
            raw=take(h,pb+j*44,44);coeff=unpack(raw,0,'<4f');children=unpack(raw,16,'<2h')
            if not all(math.isfinite(v) for v in coeff):raise ValueError('NONFINITE_PLANE')
            if any(ch>=pc for ch in children):raise ValueError('CHILD_OUT_OF_RANGE')
            ranges=[unpack(raw,o,'<Hh') for o in (20,24)]
            for count,start in ranges:
                if count and (start<0 or start+count>tc):raise ValueError('FACE_RANGE_OUT_OF_BOUNDS')
            planes.append({'index':j,'coeff':coeff,'children':children,'ranges':ranges,
                 'object_links':unpack(raw,36,'<2I')})
        parts.append({'name':name(take(b,24+12*i,8)),'names':names,'planes':planes,'triangles':tris,
             'vertices':vertices,'plane_bytes':take(h,pb,44*pc),'triangle_bytes':take(h,tb,36*tc),
             'plane_raw_file_offset':ends[i]+pb,'triangle_raw_file_offset':ends[i]+tb})
    return parts,primary

def initialized_flags(raw):return raw|0x30 if raw&2 else raw

def potential_selected(part):
    # A union is not a particular camera's visibility. It identifies records ever
    # submitted by either side range in the source BSP tree rooted at node 0.
    visit=[];seen=set();active=set();depth=0
    def walk(i,ancestors):
        if i<0:return
        if i in ancestors:raise ValueError('BSP_CYCLE')
        if i in seen:raise ValueError('BSP_MULTIPLE_PARENT')
        seen.add(i);visit.append(i)
        p=part['planes'][i]
        for count,start in p['ranges']:
            active.update(range(start,start+count))
        for child in p['children']:walk(child,ancestors|{i})
    walk(0,set())
    return seen,active
