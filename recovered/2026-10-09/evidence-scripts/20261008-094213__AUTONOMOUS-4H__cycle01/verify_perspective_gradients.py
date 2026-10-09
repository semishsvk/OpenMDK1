"""Original perspective horizontal-gradient setup vs ordered rational x87 model.
This stage receives stored q, u*q, v*q values; no triangle coverage or pixel loop
is claimed. The exact source operation order is tested, including cancellation.
"""
from fractions import Fraction
from datetime import datetime,timezone
import json,struct,math,itertools
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from verify_f3_contract import machine,w32,r32,STACK
from verify_perspective_inputs import quantize,f32
from static_probe import ROOT,PIN,load,offset,sha
EXE,SECTIONS=load();K=struct.unpack_from('<d',EXE,offset(SECTIONS,0x498fec,8))[0]
if not math.isfinite(K) or K<=0:raise ValueError('SOURCE_SCALE_CONSTANT')
D=0x10010000

def ordered(a,short,total,den):
 r=lambda x:quantize(x,64,0)
 a=list(map(Fraction.from_float,a));inv=r(Fraction(1,den))
 first=r(r(a[2]-a[0])*short);second=r(r(a[0]-a[1])*total)
 g=r(r(second+first)*inv)
 return g,r(g*Fraction.from_float(K))

def run(values,short,total,den):
 if not 0<short<total<32768 or not 0<den<2**30:raise ValueError('GRADIENT_FIXTURE_DOMAIN')
 values=tuple(tuple(f32(v) for v in row) for row in values)
 if len(values)!=3 or any(len(row)!=3 or any(not math.isfinite(v) for v in row) for row in values):raise ValueError('VALUE_DOMAIN')
 u=machine();u.reg_write(UC_X86_REG_FPCW,0x37f);u.reg_write(UC_X86_REG_EBP,STACK)
 w32(u,STACK-0x7c,D);w32(u,D+12,0);w32(u,0x5414b8,0)
 for p,v in [(0x54ebec,den),(0x54ec00,short),(0x54ebfc,total)]:w32(u,p,v)
 components=[(-0x84,-0x88,-0x98),(-0x94,-0x9c,-0xa4),(-0x8c,-0xa0,-0xa8)]
 for row,rels in zip(values,components):
  for v,rel in zip(row,rels):u.mem_write(STACK+rel,struct.pack('<f',v))
 source=bytes(u.mem_read(STACK-0xa8,0x2c));writes=[];state={'done':False,'instructions':0}
 addrs=[0x54ec10,0x54ec80,0x54ec14,0x54ec84,0x54ec18,0x54ec88]
 def code(uc,a,n,_):
  state['instructions']+=1
  if a==0x46dec8:state['done']=True;uc.emu_stop();return
  if not 0x46de05<=a or a+n>0x46dec8:raise ValueError('GRADIENT_CODE_ESCAPE')
 def write(uc,access,a,n,v,_):
  if n!=4 or a not in addrs:raise ValueError('GRADIENT_WRITE_ESCAPE')
  writes.append(a)
 u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,write)
 u.emu_start(0x46de05,0x100ff000,timeout=200000,count=300)
 if not state['done'] or writes!=addrs:raise ValueError('GRADIENT_WRITE_ORDER')
 actual=[];ideal=[]
 for row,addresses in zip(values,[(addrs[0],addrs[1]),(addrs[2],addrs[3]),(addrs[4],addrs[5])]):
  for v,p in zip(ordered(row,short,total,den),addresses):
   want=struct.pack('<f',float(quantize(v,24,0)));got=bytes(u.mem_read(p,4))
   if want!=got:raise ValueError('GRADIENT_NUMERIC_MISMATCH:'+str((row,short,total,den,p,want.hex(),got.hex())))
   actual.append(got.hex())
  aa=list(map(Fraction.from_float,row));exact=((aa[2]-aa[0])*short+(aa[0]-aa[1])*total)/den
  ideal.append(struct.pack('<f',float(exact)).hex())
 if bytes(u.mem_read(STACK-0xa8,0x2c))!=source:raise ValueError('INPUT_VALUES_MUTATED')
 return {'q_uq_vq':values,'short':short,'total':total,'denominator':den,'stored_hex':actual,'unreordered_exact_real_hex':ideal,'instructions':state['instructions'],'pass':True}

def main():
 values=[((1.,0.5,0.25),(10.,-7.,2.),(3.,8.,5.)),
  ((0.1,0.2,0.3),(-1.25,2.75,8.5),(1000.,-1000.,3.)),
  ((1.,1.,1.),(2.,2.,2.),(-3.,-3.,-3.)),
  ((1/7,1/11,1/13),(1.1,2.2,3.3),(-99.125,0.125,100.25)),
  ((1.,1e20,2e20),(1.,1e20,2e20),(3.,3e20,6e20))]
 tests=[run(v,s,t,d) for v in values for s,t in [(1,2),(3,7),(31,64)] for d in (1,3,127,65537)]
 control=run(values[-1],1,2,3)
 if control['stored_hex'][0]==control['unreordered_exact_real_hex'][0]:raise ValueError('NUMERIC_COUNTEREXAMPLE_MISSING')
 result={'schema':'OpenMDK1.PerspectiveGradientMechanism.v1','status':'PASS','tests':len(tests)+1,'cases':tests,
  'source_exe_sha256':PIN,'source_gradient_scale_constant':K,
  'ordered_rule':'round_x87_64((round64((a2-a0)*S) + round64((a0-a1)*T))*round64(1/D)); store binary32 and separately multiply the still-unrounded x87 value by the source scale constant before its second store.',
  'field_contract':{'S':'global 0x54ec00','T':'global 0x54ebfc','D':'global 0x54ebec after branch-specific width adjustment',
   'outputs':['q_gradient','scaled_q_gradient','uq_gradient','scaled_uq_gradient','vq_gradient','scaled_vq_gradient']},
  'counterexample_to_real_number_reassociation':control,
  'numeric_profile':'x87 PC64 / round-to-nearest-even. Finite binary32 q/uq/vq inputs; no subnormal/overflow cases.',
  'scope':'Positive-width perspective gradient block with explicit source-global inputs, not a complete camera-to-pixel pipeline.',
  'game_runtime_executed':False,'fidelity_verified':False,
  'next':'Verify sign-dependent width setup and perspective span stepping at the actual callback boundary.',
  'created_at_utc':datetime.now(timezone.utc).isoformat()}
 with (ROOT/'perspective-gradient-verification.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True)
 print(json.dumps({'status':'PASS','tests':result['tests'],'source_scale':K,'exact_reassociation_counterexample':{'original':control['stored_hex'][0],'algebraic_real':control['unreordered_exact_real_hex'][0]},'sha256':sha((ROOT/'perspective-gradient-verification.json').read_bytes())}))
if __name__=='__main__':main()
