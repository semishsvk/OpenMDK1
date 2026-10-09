import pathlib,json,hashlib,shutil
base=pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1-HMO1-Slice-BF11AH-20261006');dest=pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1-HMO1-Slice-BF11AI-20261006');assert not dest.exists()
r=json.loads((base/'evidence'/'delivery.json').read_text())
for n,h in r['sha256'].items():assert hashlib.sha256((base/n).read_bytes()).hexdigest()==h,'Concurrent modification: '+n
shutil.copytree(base/'project',dest/'project',ignore=shutil.ignore_patterns('.godot'));shutil.copytree(base/'tools',dest/'tools');(dest/'build').mkdir();(dest/'evidence').mkdir()
portal=json.loads(pathlib.Path('portal_segment_receipt.json').read_text());ir=json.loads((dest/'project'/'hmo1.json').read_text());ir['portal']=portal;ir['limitations'].append('Original object0 portal selector implemented; target CHMO_1 activation is missing and is shown as a pending gate, not a completed retail transition.')
(dest/'project'/'hmo1.json').write_text(json.dumps(ir))
code='''extends RefCounted
static func in_range_or_cross(previous:float,current:float,lo:float,hi:float)->bool:
 return (lo<=current and current<=hi) or ((current<lo)!=(previous<lo)) or ((current<hi)!=(previous<hi))
static func query(previous:Vector3,current:Vector3)->int:
 if in_range_or_cross(previous.z,current.z,99,126) and in_range_or_cross(previous.x,current.x,-19,17) and current.y>654 and previous.y<=654:return 10
 return -1
'''
(dest/'project'/'portal.gd').write_text(code)
s=(dest/'project'/'main.gd').read_text(encoding='utf-8');s=s.replace('const CollisionPort=','const PortalPort=preload("res://portal.gd")\nconst CollisionPort=')
s=s.replace('var smoke=false','var portal_smoke=false\nvar pending_target=-1\nvar portal_validation={}\nvar smoke=false')
s=s.replace('if args[i]=="--smoke":smoke=true','if args[i]=="--smoke":smoke=true\n  if args[i]=="--portal-smoke":smoke=true;portal_smoke=true')
s=s.replace('validate_collision();update_camera()', 'validate_portal();\n if portal_smoke:portal_approach()\n validate_collision();update_camera()')
s=s.replace('if event.pressed and event.keycode==KEY_R:reset()','if event.pressed and event.keycode==KEY_R:reset()\n  if event.pressed and event.keycode==KEY_P:portal_approach()')
s=s.replace('if smoke and tick==0:synthetic_key(KEY_Q,true)','if smoke and tick==0:synthetic_key(KEY_W if portal_smoke else KEY_Q,true)')
s=s.replace('if smoke and tick==240:synthetic_key(KEY_Q,false)','if smoke and tick==240:synthetic_key(KEY_W if portal_smoke else KEY_Q,false)')
s=s.replace('if hit.is_empty():pose=target','if hit.is_empty() and pending_target<0:\n  var portal_target=PortalPort.query(pose,target)\n  pose=target\n  if portal_target>=0:pending_target=portal_target;print("SOURCE_PORTAL_SELECTED CHMO_1 index=",portal_target)')
s=s.replace('"blocked":blocked}', '"blocked":blocked,"pending_target":pending_target}')
s=s.replace('Esc release mouse · R reset · F12 capture','Esc release mouse · R reset · P source portal approach · F12 capture')
s=s.replace('if collected==3:hud.text+="\\nSurvey complete — free exploration unlocked"','if collected==3:hud.text+="\\nSurvey complete — free exploration unlocked"\n if pending_target==10:hud.text+="\\nSource portal detected → CHMO_1; activation MISSING. R/P to restart."')
s=s.replace('pose=Vector3(-220,-200,450);heading=60;pitch=-35;collected=0;blocked=0','pose=Vector3(-220,-200,450);heading=60;pitch=-35;collected=0;blocked=0;pending_target=-1')
s=s.replace('validation.mismatches==0 and collected==3 and input_events>=2','validation.mismatches==0 and portal_validation.mismatches==0 and (pending_target==10 if portal_smoke else collected==3) and input_events>=2')
s=s.replace('"collision":validation,','"collision":validation,"portal":portal_validation,"portal_smoke":portal_smoke,"pending_target":pending_target,')
s+='''
func validate_portal():
 var errors=[]
 for i in range(ir.portal.cases.size()):
  var c=ir.portal.cases[i];var result=PortalPort.query(vec(c.start),vec(c.end));var expected=-1 if c.target==null else int(c.target)
  if result!=expected:errors.append(i)
 portal_validation={"cases":ir.portal.cases.size(),"mismatches":errors.size(),"failures":errors}
func portal_approach():
 pose=Vector3(0,652,115);heading=90;pitch=0;pending_target=-1
 print("DIAGNOSTIC_PORTAL_APPROACH — camera teleport is experimental")
'''
(dest/'project'/'main.gd').write_text(s,encoding='utf-8',newline='\n')
readme=(base/'README.md').read_text().replace('BF11AH','BF11AI')+'''\nBF11AI adds the actual object0 flag3 portal selector: 744 original-x86 comparisons, no differences. P jumps the experimental camera to (0,652,115); hold W to cross Y654. The original predicate selects CHMO_1/index10. The slice records this target and stops at an explicit missing-activation gate; it does not load or pretend to enter CHMO_1. Portal detection is source-backed; P camera teleport and this gate UI are experimental. Use R for the normal survey slice. --portal-smoke runs this crossing through the same input/physics path.\n'''
(dest/'README.md').write_text(readme)
for n in ['portal_segment_validation.py','portal_segment_receipt.json','portal_segment_disassembly.txt','world_portal_frame_disassembly.txt','prepare_portal_slice.py']:shutil.copyfile(n,dest/'evidence'/n)
print(dest)
