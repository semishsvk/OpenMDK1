import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes()
ib=0x400000
e=struct.unpack_from("<I",b,0x3c)[0]; n=struct.unpack_from("<H",b,e+6)[0]; opt=e+24; so=opt+struct.unpack_from("<H",b,e+20)[0]
o=so
vs,va,rs,rp=struct.unpack_from("<4I",b,o+8)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
ins=list(md.disasm(b[rp:rp+rs],ib+va))
rows=[]
for i,x in enumerate(ins):
    refs=[]
    for op in x.operands:
        if op.type==X86_OP_MEM and op.mem.disp==0x20 and op.mem.base:
            refs.append(op.mem.base)
    if not refs: continue
    for base in refs:
        near=set(); ctx=[]
        for j in range(max(0,i-80),min(len(ins),i+81)):
            y=ins[j]
            for op in y.operands:
                if op.type==X86_OP_MEM and op.mem.base==base and -0x20<=op.mem.disp<=0x180:
                    near.add(op.mem.disp); ctx.append((y.address,y.mnemonic,y.op_str,op.mem.disp))
        score=sum(v in near for v in (0x0c,0x10,0x14,0x18,0x1c,0x24,0x28,0x2c,0x30,0x40))
        if score>=2:
            rows.append((score,x.address,md.reg_name(base),x.mnemonic,x.op_str,sorted(near),ctx))
rows.sort(key=lambda r:(-r[0],r[1]))
print("ROWS",len(rows))
for score,a,base,mn,op,near,ctx in rows[:120]:
    print("\nADDR",hex(a),"base",base,"score",score,mn,op,"near",near)
    for ca,cm,co,cd in ctx:
        if a-64<=ca<=a+80:
            print(f"  {ca:08X} {cm:8} {co} disp={hex(cd)}")
