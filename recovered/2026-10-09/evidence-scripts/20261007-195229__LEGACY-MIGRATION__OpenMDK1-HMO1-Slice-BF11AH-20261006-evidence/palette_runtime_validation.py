from mdk_machine import *
import json
m=Machine();u=m.uc;dti=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3.DTI').read_bytes();mto=pathlib.Path(r'F:\Remaster Framework\source\MDK\TRAVERSE\LEVEL3\LEVEL3O.MTO').read_bytes()
u.mem_map(0x1000000,0x1000000);u.mem_write(0x1000000,dti);u.mem_map(0x2000000,0x1000000);u.mem_write(0x2000000,mto)
# Exact section-relative DTI addressing from 0x41B2BE..0x41B2DE.
section=4+struct.unpack_from('<I',dti,4+0x1c)[0];count=struct.unpack_from('<I',dti,section)[0];palette_offset=section+4
print('PALETTE SECTION',hex(section),'COUNT',count,'OFFSET',hex(palette_offset))
u.mem_write(0x5735e4,dti[palette_offset:palette_offset+768]);u.mem_write(0x5735e4,b'\0\0\0')
local=0x94+struct.unpack_from('<I',mto,0x94+4)[0]
u.mem_write(0x5736a4,mto[local:local+3*count])
m.write(0x581e28,'I',0x4701d0)
# Original RGB565 callback selected at 0x47407F..0x474095; conditional format.
m.call(0x4709d8,{UC_X86_REG_EAX:0,UC_X86_REG_EDX:256,UC_X86_REG_EBX:0x5735e4})
# EAX base palette index64, EDX source entry count, EBX original RGB triple block.
m.call(0x4709d8,{UC_X86_REG_EAX:64,UC_X86_REG_EDX:count,UC_X86_REG_EBX:0x2000000+local})
bgra=bytes(u.mem_read(0x581828,1024));rgb=bytes(v for i in range(256) for v in [bgra[4*i+2],bgra[4*i+1],bgra[4*i]])
raw=bytes(u.mem_read(0x5735e4,768));assert rgb[64*3:(64+count)*3]==raw[64*3:(64+count)*3]
pathlib.Path('hmo1_runtime_palette.rgb').write_bytes(raw)
r=dict(status='CANONICAL_DTI_PLUS_HMO1_PALETTE_RECONSTRUCTED_ORIGINAL_CONVERSION_EXECUTED',dti_palette_raw_offset=palette_offset,local_palette_raw_offset=local,local_color_count=count,local_destination_index=64,rgb_sha256=hashlib.sha256(raw).hexdigest(),scope='Source palette assembly and original 0x4709D8 BGRA conversion; full render palette modes/device masks still conditional.')
pathlib.Path('palette_runtime_receipt.json').write_text(json.dumps(r,indent=2));print(r)
