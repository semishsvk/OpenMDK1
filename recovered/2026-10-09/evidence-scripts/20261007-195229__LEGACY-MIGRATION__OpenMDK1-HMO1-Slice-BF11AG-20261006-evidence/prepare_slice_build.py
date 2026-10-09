import pathlib,zipfile,shutil,json,hashlib
workspace=pathlib.Path(__file__).parent;tools=workspace/'slice_tools';tools.mkdir(exist_ok=True)
tpl=tools/'windows_debug_x86_64.exe'
if not tpl.exists():
 with zipfile.ZipFile(r'F:\Remaster Framework\source\Godot\Godot_v4.7.2-stable_export_templates.tpz') as z:
  with z.open('templates/windows_debug_x86_64.exe') as src,tpl.open('wb') as dst:shutil.copyfileobj(src,dst)
project=workspace/'slice_project';dest=pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1-HMO1-Slice-BF11AG-20261006')
assert not dest.exists(),'New release directory must not overwrite concurrent work'
(dest/'project').mkdir(parents=True);(dest/'build').mkdir();(dest/'evidence').mkdir();(dest/'tools').mkdir()
for p in project.rglob('*'):
 if '.godot' in p.parts or p.suffix=='.uid' or not p.is_file():continue
 target=dest/'project'/p.relative_to(project);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
shutil.copyfile(tpl,dest/'tools'/tpl.name)
preset='''[preset.0]
name="Windows Desktop"
platform="Windows Desktop"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter="*.json"
exclude_filter=""
export_path="../build/OpenMDK-HMO1-Experimental.exe"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
[preset.0.options]
custom_template/debug="../tools/windows_debug_x86_64.exe"
custom_template/release="../tools/windows_debug_x86_64.exe"
debug/export_console_wrapper=0
binary_format/embed_pck=true
binary_format/architecture="x86_64"
texture_format/s3tc_bptc=true
texture_format/etc2_astc=false
application/modify_resources=false
'''
(dest/'project'/'export_presets.cfg').write_text(preset)
readme='''# OpenMDK HMO1 experimental slice — BF11AG

Run build/OpenMDK-HMO1-Experimental.exe on Windows x64.

WASD move, Q/E descend/ascend, Shift fast movement, arrows turn/look, click captures mouse, Esc releases mouse, R resets, F12 saves a screenshot to Godot user data. Descend with Q through three survey markers to finish the short slice, then explore freely. The markers/objective and flight camera are experimental additions.

Implemented: original HMO1 assets (21 source textures, palette and 394 nondegenerate packed geometry triangles); keyboard/mouse input; fixed 60 Hz point-segment BSP collision port; repeatable short objective; in-build collision comparison against 300 Python reference cases. BF11Y separately compared the Python reference with original executable x86 on 2000 cases.

Partial: packed collision-face geometry is adapted for rendering, not the prior 6216-polygon token-native RenderIR baseline. Face UVs normalized by texture dimensions and materials are diagnostic mappings. Lighting is unshaded, culling disabled. Collision is point-based without capsule/slide/gravity. Preview camera starts at (-220,-200,450), yaw60 pitch-35; the DTI (-4,0,190,96) seed is retained in source IR but is not used as a retail camera claim.

Missing: full retail startup/resource activation, retail camera/entity logic, enemies/combat, animation, sound, transitions, save CRT/OS environment, glass/mirror behavior and original runtime fidelity oracle. This is not VERIFIED BF12.

Validation and captures in evidence/ are from this same exported executable. A --smoke --capture-dir <absolute directory> invocation drives Q press/release through Godot input events, collects three markers in 360 physics ticks, validates collision and records PNGs plus smoke.json. Synthetic input is explicit; normal player input uses the same handler. No retail screenshot/framebuffer is supplied.
'''
(dest/'README.md').write_text(readme)
for n in ['export_hmo1_slice_assets.py','collision_port.py','prepare_slice_build.py','collision_port_validation.json','collision_emulation_receipt.json']:
 shutil.copyfile(workspace/n,dest/'evidence'/n)
print(dest)
