import pathlib
root=pathlib.Path(r"F:\Remaster Framework\source\MDK")
needle=b"SYS_PAL"
for p in root.rglob("*"):
    if not p.is_file(): continue
    try:b=p.read_bytes()
    except: continue
    pos=0
    while True:
        pos=b.find(needle,pos)
        if pos<0:break
        lo=max(0,pos-64); hi=min(len(b),pos+256)
        print(str(p.relative_to(root)),pos,len(b),b[lo:hi].hex())
        pos+=1
