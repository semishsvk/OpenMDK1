import pathlib,struct
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
secs=[]
for i in range(n):
    o=so+i*40; name=b[o:o+8].rstrip(b"\0").decode(errors="replace"); vs,va,rs,rp=struct.unpack_from("<4I",b,o+8); secs.append((name,va,vs,rp,rs))
def va2off(x):
    r=x-ib
    for _,va,vs,rp,rs in secs:
        if va<=r<va+max(vs,rs): return rp+r-va
    raise ValueError(hex(x))
for va in [0x494018,0x494280,0x494264]:
    off=va2off(va); chunk=b[off:off+180]; print(hex(va),repr(chunk.split(b"\0",1)[0].decode("latin1","replace")))
