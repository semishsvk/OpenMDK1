"""Diagnostic observation only: read original x87 registers without changing them.
Pins the per-chunk arithmetic boundary before deriving a numeric contract.
"""
from fractions import Fraction
from datetime import datetime,timezone
import json,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.x86_const import *
from verify_perspective_span_inputs import make
from verify_f3_contract import w32,r32,STACK,STOP
from static_probe import ROOT,PIN,sha
REGS=[UC_X86_REG_FP0,UC_X86_REG_FP1,UC_X86_REG_FP2,UC_X86_REG_FP3,UC_X86_REG_FP4,UC_X86_REG_FP5,UC_X86_REG_FP6,UC_X86_REG_FP7]

def number(bits):
 m,e=bits
 if m==0:return Fraction(0)
 sign=-1 if e&0x8000 else 1;power=(e&0x7fff)-16383-63
 if e&0x7fff==0x7fff:raise ValueError('NONFINITE_OBSERVATION')
 return sign*Fraction(m)*(2**power if power>=0 else Fraction(1,2**-power))

def observe(n,x):
 u,_=make();tex=0x20000000;dest=0x10080000;u.mem_map(tex,32768);u.mem_write(tex,bytes(32768));u.mem_write(dest,bytes(1000));u.reg_write(UC_X86_REG_ESP,STACK);w32(u,STACK,STOP)
 for p,v in [(0x54ec2c,n),(0x54ec70,x),(0x54ec28,7),(0x54ec50,128),(0x54ec20,tex),(0x54ec1c,dest)]:w32(u,p,v)
 values=[(0x54ec30,1.),(0x54ec34,8.),(0x54ec38,30.),(0x54ec10,1/256),(0x54ec14,1/16),(0x54ec18,1/32),(0x54ec80,1/8),(0x54ec84,2.),(0x54ec88,1.)]
 for p,v in values:u.mem_write(p,struct.pack('<f',v))
 captures=[];done=[]
 def hook(uc,a,size,_):
  if a==STOP:done.append(True);uc.emu_stop();return
  if not 0x471f82<=a or a+size>0x47278a:raise ValueError('CODE_ESCAPE')
  if a in (0x47201c,0x47208d,0x472185,0x472199,0x4726a2):
   top=(uc.reg_read(UC_X86_REG_FPSW)>>11)&7;tag=uc.reg_read(UC_X86_REG_FPTAG);fp=[]
   for i in range(8):
    physical=(top+i)&7;mant,exp=uc.reg_read(REGS[physical]);empty=(tag>>(2*physical))&3==3
    fp.append({'logical':i,'empty':empty,'mantissa':mant,'exponent':exp,'value':None if empty else str(number((mant,exp)))})
   sp=uc.reg_read(UC_X86_REG_ESP);captures.append({'va':hex(a),'written_pixels':uc.reg_read(UC_X86_REG_EDI)-dest,'fp':fp,'span_parts':[r32(uc,sp+k) for k in (16,20,24,28,32)]})
 def write(uc,access,a,size,v,_):
  if STACK-128<=a and a+size<=STACK:return
  if dest<=a and a+size<=dest+n+1:return
  raise ValueError('WRITE_ESCAPE')
 def read(uc,access,a,size,v,_):
  if tex<=a<tex+65536 and not a+size<=tex+32768:raise ValueError('READ_ESCAPE')
 u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,read);u.emu_start(0x471f82,STOP+1,timeout=200000,count=10000)
 if not done:raise ValueError('NOT_FINISHED')
 return {'delta':n,'screen_x_mod32':x,'captures':captures}
if __name__=='__main__':
 result={'source_exe_sha256':PIN,'scope':'DIAGNOSTIC_FP80_READ_ONLY_OBSERVATION','cases':[observe(70,5),observe(64,0),observe(7,0)],'created_at_utc':datetime.now(timezone.utc).isoformat()}
 p=ROOT/'default-chunk-fpu-observations.json'
 with p.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 for r in result['cases']:
  print('CASE',r['delta'],r['screen_x_mod32'])
  for x in r['captures']:print(x['va'],x['written_pixels'],x['span_parts'],[f['value'] for f in x['fp'] if not f['empty']])
