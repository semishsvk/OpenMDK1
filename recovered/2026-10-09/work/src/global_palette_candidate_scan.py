import pathlib,json,hashlib,collections
root=pathlib.Path(r"F:\Remaster Framework\source\MDK")
allowed=set(((i<<3)|(i>>2)) for i in range(32))
wins=(432,768)
results=[]
for p in root.rglob("*"):
    if not p.is_file():
        continue
    try:
        b=p.read_bytes()
    except:
        continue
    if len(b)<432:
        continue
    vals=bytearray(1 if x in allowed else 0 for x in b)
    for W in wins:
        if len(b)<W: continue
        s=sum(vals[:W])
        best=[]
        # keep local/top candidates only
        if s>=int(W*.94): best.append((s,0))
        for i in range(W,len(b)):
            s+=vals[i]-vals[i-W]
            if s>=int(W*.94):
                best.append((s,i-W+1))
        if best:
            # unique strongest positions, suppress nearby duplicates
            best.sort(reverse=True)
            chosen=[]
            for score,off in best:
                if any(abs(off-o)<W for _,o in chosen): continue
                chosen.append((score,off))
                if len(chosen)>=8: break
            for score,off in chosen:
                chunk=b[off:off+W]
                results.append({"file":str(p.relative_to(root)),"window":W,"offset":off,"score":score,"ratio":score/W,"sha256":hashlib.sha256(chunk).hexdigest(),"first24":chunk[:24].hex()})
results.sort(key=lambda x:(x["ratio"],x["window"]),reverse=True)
print(json.dumps({"schema":"OpenMDK.GlobalPaletteCandidateScan.v1","allowed":"RGB555 expanded channel values","root":str(root),"candidates":results[:200]},indent=2))
