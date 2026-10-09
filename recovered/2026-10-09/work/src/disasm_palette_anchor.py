import pathlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
b=pathlib.Path(r"F:\Remaster Framework\source\MDK\MDK95.EXE").read_bytes();imagebase=0x400000
# AUTO raw 0x400 maps RVA 0x1000
startva=0x46cf80;endva=0x46d140;startoff=0x400+(startva-imagebase-0x1000);code=b[startoff:startoff+(endva-startva)]
md=Cs(CS_ARCH_X86,CS_MODE_32)
for i in md.disasm(code,startva): print(f"{i.address:08X}  {i.mnemonic:7} {i.op_str}")
