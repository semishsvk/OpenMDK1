import pathlib,struct,string
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
secs=[]
for i in range(n):
    o=so+i*40
    name=b[o:o+8].rstrip(b"\0").decode(errors="replace")
    vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
    secs.append((name,va,vs,rp,rs))
def va2off(x):
    r=x-ib
    for _,va,vs,rp,rs in secs:
        if va<=r<va+max(vs,rs):
            oo=rp+r-va
            if 0<=oo<len(b): return oo
    return None
def cstr_at_va(v):
    o=va2off(v)
    if o is None:return None
    chunk=b[o:o+120]
    raw=chunk.split(b"\0",1)[0]
    if len(raw)<4:return None
    try:s=raw.decode("latin1")
    except:return None
    if sum(ch in string.printable and ch not in "\r\n\t\x0b\x0c" for ch in s)/len(s)<.9:return None
    return s
calls=[0x409224,0x40f605,0x410275,0x41d132,0x41d80f,0x41dedf,0x41ec2a,0x4205d3,0x420b6f,0x4297b3,0x42cd82,0x433dda]
for a in calls:
    off=va2off(a)
    if off is None:continue
    lo=max(0,off-160); hi=min(len(b),off+48)
    found={}
    for p in range(lo,hi-3):
        v=struct.unpack_from("<I",b,p)[0]
        s=cstr_at_va(v)
        if s is not None:
            found[v]=s
    print("\nCALL",hex(a))
    for v,s in sorted(found.items()):
        print(hex(v),repr(s))
