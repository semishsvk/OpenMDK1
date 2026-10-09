"""Isolated affine kernel runner. Synthetic pixels only, bounded source reads,
destination writes and code addresses. No OS calls, actual game or GPU runtime.
"""
from datetime import datetime,timezone
import json,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK,STOP
from static_probe import ROOT,sha
TEX,DEST=0x20000000,0x10001000
U32=0xffffffff
KERNELS={
 'B0':(0x46edc0,0x46f3d2,False,False,False),
 'B1':(0x46f3d2,0x46fb42,False,True,False),
 'B2':(0x46fb42,0x470476,True,False,False),
 'B3':(0x470476,0x470f08,True,True,False),
 'A0':(0x474682,0x474dbc,False,False,True),
 'A1':(0x474dbc,0x475654,False,True,True),
 'A2':(0x475654,0x4760b0,True,False,True),
 'A3':(0x4760b0,0x476c6a,True,True,True)}

def execute(kernel,texture,width,height,n,u0=0,v0=0,du=65536,dv=0,reverse=False):
    if kernel not in KERNELS or not 1<=n<=600 or len(texture)>1024*1024:
        raise ValueError('KERNEL_FIXTURE_BUDGET')
    if width&(width-1) or height&(height-1) or len(texture)!=width*height:
        raise ValueError('POWER_TWO_TEXTURE_FIXTURE_REQUIRED')
    begin,end,wrap,key,preserved=KERNELS[kernel]
    uc=machine();uc.mem_map(TEX,0x200000);uc.mem_write(TEX,texture)
    mask=width*height-1
    initial=((u0>>16)&(width-1))+(((v0>>16)&(height-1))*width)
    start=8;left=start if not reverse else start+n-1;right=start+n-1 if not reverse else start
    values={0x54eb9c:(du>>16)+(dv>>16)*width,0x54eb98:(du>>16)+(dv>>16)*width+width,
      0x54eba0:(du<<16)&U32,0x54eba4:(dv<<16)&U32,
      0x54ebac:0,0x54eba8:width,0x54ebb0:0,0x54ebb4:0,
      0x54ebb8:(u0<<16)&U32,0x54ebbc:(v0<<16)&U32,
      0x54ebc0:left<<16,0x54ebc4:right<<16,0x54ebc8:0,0x54ebcc:0,
      0x54ebd0:2,0x54ebd4:TEX+initial,0x54ebd8:DEST,0x54ebdc:TEX,0x54ebe0:mask}
    for p,v in values.items():w32(uc,p,v)
    frame=bytes([0xA7])*768;uc.mem_write(DEST,frame);w32(uc,STACK,STOP)
    uc.reg_write(UC_X86_REG_ESP,STACK)
    state={'done':False,'instructions':0};reads=[];writes=[]
    def code(u,addr,size,_):
        state['instructions']+=1
        if addr==STOP:state['done']=True;u.emu_stop();return
        if not begin<=addr<end:raise ValueError('KERNEL_PC_ESCAPE:'+hex(addr))
    def read(u,access,addr,size,value,_):
        if TEX<=addr<TEX+0x200000:
            if addr+size>TEX+len(texture):raise ValueError('TEXEL_READ_OUTSIDE_FIXTURE:'+str(addr-TEX))
            reads.extend(range(addr-TEX,addr-TEX+size))
    def write(u,access,addr,size,value,_):
        if STACK-256<=addr and addr+size<=STACK+8:return
        if 0x54eb98<=addr and addr+size<=0x54ec90:return
        if DEST+start<=addr and addr+size<=DEST+start+n:
            writes.extend(range(addr-DEST,addr-DEST+size));return
        raise ValueError('KERNEL_WRITE_ESCAPE:'+hex(addr))
    uc.hook_add(UC_HOOK_CODE,code);uc.hook_add(UC_HOOK_MEM_READ,read);uc.hook_add(UC_HOOK_MEM_WRITE,write)
    uc.emu_start(begin,STOP+1,timeout=800000,count=90000)
    if not state['done']:raise ValueError('KERNEL_NO_RETURN')
    result=bytes(uc.mem_read(DEST,len(frame)))
    if result[:start]!=frame[:start] or result[start+n:]!=frame[start+n:]:raise ValueError('FRAME_GUARD_CHANGED')
    if bytes(uc.mem_read(TEX,len(texture)))!=texture:raise ValueError('TEXTURE_MUTATED')
    return {'pixels':list(result[start:start+n]),'reads':reads,'write_offsets':writes,
        'instructions':state['instructions'],'initial_offset':initial,'keyed':key,
        'wrapped':wrap,'preserves_du_fraction':preserved,'frame_sha256':sha(result)}

def main():
    result=[]
    for name in KERNELS:
        for n in (1,2,3,4,31,32,33):
            texture=bytes(i%256 for i in range(1024))
            result.append({'kernel':name,'n':n,'observation':execute(name,texture,32,32,n)})
    out=ROOT/'sampler-discovery.json'
    with out.open('x',encoding='utf-8') as f:json.dump({'scope':'DISCOVERY_NOT_VALIDATION','cases':result},f,indent=2)
    for r in result:
        o=r['observation'];print(r['kernel'],r['n'],'PIX',o['pixels'],'READ',o['reads'],'WRITES',len(o['write_offsets']))
if __name__=='__main__':main()
