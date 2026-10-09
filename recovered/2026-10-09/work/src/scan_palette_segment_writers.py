import pathlib,struct
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
secs=[]
for i in range(n):
    o=so+i*40
    name=b[o:o+8].rstrip(b"\0").decode(errors="replace")
    vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
    secs.append((name,va,vs,rp,rs))
def off2va(x):
    for _,va,vs,rp,rs in secs:
        if rp<=x<rp+rs:return ib+va+x-rp
def scan_target(target):
    hits=[]
    for off in range(len(b)-5):
        if b[off]!=0xE8: continue
        va=off2va(off)
        if va is None: continue
        rel=struct.unpack_from("<i",b,off+1)[0]
        if va+5+rel==target:
            w=b[max(0,off-128):off]
            flags=[]
            pats={
              "EDX_80":b"\xBA\x50\x00\x00\x00",
              "EAX_64":b"\xB8\x40\x00\x00\x00",
              "EDX_112":b"\xBA\x70\x00\x00\x00",
              "EAX_144":b"\xB8\x90\x00\x00\x00",
              "EDX_192":b"\xBA\xC0\x00\x00\x00",
              "EAX_64B":b"\xB8\x40\x00\x00\x00"
            }
            for k,p in pats.items():
                if p in w: flags.append(k)
            if flags:
                hits.append((hex(va),flags,w[-64:].hex()))
    return hits
for t in [0x46D208,0x46D490,0x46D1D0]:
    print("\nTARGET",hex(t))
    for h in scan_target(t):
        print(h)
