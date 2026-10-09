"""Source-backed sampler table selection: startup predicate and original command
parser. Only allowlisted x86 blocks execute, with synthetic argv; no CPUID, OS
imports, native game or host configuration changes are invoked.
"""
from datetime import datetime,timezone
import json,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from static_probe import ROOT,load,offset,PIN,sha
from verify_f3_contract import machine,w32,r32,STACK,STOP
ARG=0x10010000
EXE,SECTIONS=load()
TABLES={v:EXE[offset(SECTIONS,0x49bcb4 if v else 0x49bce4,48):offset(SECTIONS,0x49bcb4 if v else 0x49bce4,48)+48] for v in (0,1)}

def run(u,start,end,allowed,output_ranges,observe=None):
    state={'done':False,'instructions':0,'installs':[]}
    def code(uc,addr,size,_):
        state['instructions']+=1
        if addr==end:state['done']=True;uc.emu_stop();return
        if not any(a<=addr and addr+size<=b for a,b in allowed):raise ValueError('VARIANT_CODE_ESCAPE:'+hex(addr))
        if addr==0x46da6c:state['installs'].append(int(uc.reg_read(UC_X86_REG_EAX)!=0))
        if observe:observe(uc,addr)
    def write(uc,access,addr,size,value,_):
        if not any(a<=addr and addr+size<=b for a,b in output_ranges):raise ValueError('VARIANT_WRITE_ESCAPE:'+hex(addr))
    h=u.hook_add(UC_HOOK_CODE,code);w=u.hook_add(UC_HOOK_MEM_WRITE,write)
    try:u.emu_start(start,end+1,timeout=500000,count=60000)
    finally:u.hook_del(h);u.hook_del(w)
    if not state['done']:raise ValueError('VARIANT_TEST_BUDGET')
    return state

def startup(cpu_word):
    u=machine();w32(u,0x541520,cpu_word);w32(u,STACK,STOP)
    u.reg_write(UC_X86_REG_ESP,STACK);u.reg_write(UC_X86_REG_EDX,1)
    state=run(u,0x401b6d,0x401b84,[(0x401b6d,0x401b84),(0x401da4,0x401dab),(0x46da6c,0x46daa9)],
        [(STACK-128,STACK+8),(0x54dc00,0x54dc30)])
    expected=int((cpu_word&0xffff00ff)==6)
    if bytes(u.mem_read(0x54dc00,48))!=TABLES[expected] or state['installs']!=[expected]:raise ValueError('STARTUP_SELECTION_MISMATCH')
    return expected,state['instructions']

ALLOWED=[(0x401a60,0x401ab9),(0x4016e0,0x4017ba),(0x401684,0x4016de),
         (0x42fab4,0x42fae7),(0x42fa80,0x42fab4),(0x425800,0x425893),
         (0x47edd7,0x47ede5),(0x46da6c,0x46daa9)]
def argv(command,initial):
    raw=command.encode('ascii')
    if len(raw)>200:raise ValueError('ARGV_BUDGET')
    u=machine();u.mem_write(0x54dc00,TABLES[initial]);u.mem_write(ARG,raw+b'\0')
    w32(u,STACK,STOP);u.reg_write(UC_X86_REG_ESP,STACK);u.reg_write(UC_X86_REG_EAX,ARG)
    state=run(u,0x401a60,STOP,ALLOWED,[(STACK-512,STACK+8),(ARG,ARG+len(raw)+1),(0x54dc00,0x54dc30)])
    tokens=command.split();expected=initial;installs=[]
    for t in tokens:
        if t.lower().startswith('-pprotx'):expected=1;installs.append(1)
        elif t.lower().startswith('-nopprotx'):expected=0;installs.append(0)
        elif t.startswith('-'):raise ValueError('UNMODELED_ARGUMENT')
    if bytes(u.mem_read(0x54dc00,48))!=TABLES[expected] or state['installs']!=installs:raise ValueError('ARGV_OVERRIDE_MISMATCH')
    if bytes(u.mem_read(ARG,len(raw)+1))!=raw+b'\0':raise ValueError('ARGV_RESTORE_FAILURE')
    return expected,state

def comparator(text,encoded_pointer):
    u=machine();u.mem_write(ARG,text.encode('ascii')+b'\0');w32(u,STACK,STOP)
    for reg,value in [(UC_X86_REG_EAX,ARG),(UC_X86_REG_EDX,encoded_pointer),(UC_X86_REG_ESP,STACK)]:u.reg_write(reg,value)
    run(u,0x401684,STOP,ALLOWED,[(STACK-512,STACK+8)])
    return u.reg_read(UC_X86_REG_EAX)

def main():
    checks=[]
    anchors={0x401b40:'ba01000000',0x401b6d:'a120155400',0x401b72:'30e4',
      0x401b74:'83f806',0x401b7d:'89d0',0x401da4:'31c0',0x401c1e:'e83dfeffff',
      0x425315:'52',0x425408:'5a',0x47f480:'52',0x47f492:'5a',0x47f497:'5a'}
    for va,h in anchors.items():
        if EXE[offset(SECTIONS,va,len(bytes.fromhex(h))):offset(SECTIONS,va,len(bytes.fromhex(h)))+len(bytes.fromhex(h))].hex()!=h:raise ValueError('ANCHOR_CHANGED')
        checks.append({'test':'source_anchor_'+hex(va),'pass':True})
    for family in (0,4,5,6,7,15):
        for feature in (0,0x100,0x200,0x400,0x700,0xff00):
            for vendor in (0,0x20000,0xff0000):
                word=family|feature|vendor;variant,instructions=startup(word)
                checks.append({'test':'startup','cpu_word':word,'selected_variant':variant,'pass':True,'instructions':instructions})
    commands=['','ordinary','-pprotx','-nopprotx','-PPROTX','-NoPpRoTx',
      ' -pprotx  ','-pprotx -nopprotx','-nopprotx -pprotx',
      '-pprotx -pprotx','-nopprotx -nopprotx','\t-pprotx\t-nopprotx\t',
      '-pprotxSuffix','-nopprotxSuffix','ignored -pprotx']
    for initial in (0,1):
        for command in commands:
            variant,state=argv(command,initial)
            checks.append({'test':'argv','initial_variant':initial,'command':command,
              'selected_variant':variant,'installs':state['installs'],'pass':True})
    for token,ptr in [('pprotx',0x494034),('nopprotx',0x49403c)]:
        for text in [token,token.upper(),token+'suffix',token[:-1],'x'+token]:
            got=comparator(text,ptr);expected=int(text.lower().startswith(token))
            if got!=expected:raise ValueError('SOURCE_OBFUSCATED_COMPARATOR_MISMATCH')
            checks.append({'test':'encoded_option_comparison','token':token,'input':text,'pass':True})
    report={'schema':'OpenMDK1.RendererVariantSelection.v1','status':'PASS','tests':len(checks),'checks':checks,
      'startup_rule':'variant A iff (stored_cpu_word & 0xffff00ff) == 6, else variant B; EDX=1 is preserved by the inspected classifier/logging call ABI.',
      'command_options':{'-pprotx':'A','-nopprotx':'B'},
      'parser_semantics':'Case-insensitive encoded prefix recognition, command tokens processed in order; last recognized override wins.',
      'option_literals_in_exe':{'0x494034':'bupfda','0x49403c':'nhbupfda'},
      'source_lookup':'Classifier uses base family nibble and vendor/feature metadata; the precise stored word is required rather than a modern CPU-name heuristic.',
      'runtime_profile_contract':'Record original executable hash, stored_cpu_word, parsed command order and resulting 48-byte callback table.',
      'actual_user_machine_original_runtime_profile':'NOT_OBSERVED',
      'source_exe_sha256':PIN,'host_cpuid_executed':False,'game_runtime_executed':False,
      'stub_policy':'No emulation callbacks substitute command parser or table installer; startup slice begins after CPU detection/log output with separately anchored EDX invariant.',
      'production_renderer_modified':False,'fidelity_verified':False,
      'created_at_utc':datetime.now(timezone.utc).isoformat()}
    p=ROOT/'variant-selection-verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2));print('SHA256',sha(p.read_bytes()))
if __name__=='__main__':main()
