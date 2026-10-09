import pathlib
p=pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1-HMO1-Slice-BF11AI-20261006\project\main.gd');s=p.read_text(encoding='utf-8')
s=s.replace('elif motion.length()>0:blocked+=1','elif not hit.is_empty() and motion.length()>0:blocked+=1')
if 'Source portal detected' not in s:
 s=s.replace('\nfunc reset():','\n if pending_target==10:hud.text+="\\nSOURCE PORTAL -> CHMO_1; activation MISSING. R/P to restart."\nfunc reset():')
s=s.replace('R reset · F12 capture','R reset · P portal approach · F12 capture')
p.write_text(s,encoding='utf-8',newline='\n');print('PORTAL_FEEDBACK_FIXED')
