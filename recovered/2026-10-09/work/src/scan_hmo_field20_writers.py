import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
o=so
name=b[o:o+8].rstrip(b"\0").decode(errors="replace"); vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
ins=list(md.disasm(b[rp:rp+rs],ib+va))
hits=[]
for i,x in enumerate(ins):
    w=[]
    for oi,op in enumerate(x.operands):
        if op.type==X86_OP_MEM and op.mem.disp==0x20:
            # Capstone access flags are not always populated; first operand of mov/fstp/etc is normally destination.
            iswrite=bool(getattr(op,"access",0)&CS_AC_WRITE) or (oi==0 and x.mnemonic in ("mov","lea","fstp","stosd","and","or","add","sub","xor"))
            if iswrite:
                w.append((op.mem.base,op.mem.index))
    if not w: continue
    for base,index in w:
        lo=max(0,i-24); hi=min(len(ins),i+25)
        nearby=set()
        same=[]
        for y in ins[lo:hi]:
            for op in y.operands:
                if op.type==X86_OP_MEM and op.mem.base==base:
                    if -0x20<=op.mem.disp<=0x180:
                        nearby.add(op.mem.disp)
                        same.append((y.address,y.mnemonic,y.op_str,op.mem.disp))
        score=sum(1 for xoff in (0x0c,0x10,0x18,0x1c,0x24,0x28,0x40) if xoff in nearby)
        if score>=2:
            hits.append({"addr":x.address,"mn":x.mnemonic,"op":x.op_str,"base":md.reg_name(base),"nearby":sorted(nearby),"score":score,"context":same})
hits.sort(key=lambda x:(-x["score"],x["addr"]))
print("HITS",len(hits))
for h in hits[:100]:
    print("\n",hex(h["addr"]),h["mn"],h["op"],"base",h["base"],"score",h["score"],"near",h["nearby"])
    for row in h["context"]:
        if h["addr"]-48<=row[0]<=h["addr"]+64:
            print(f"  {row[0]:08X} {row[1]:8} {row[2]} disp={hex(row[3])}")
