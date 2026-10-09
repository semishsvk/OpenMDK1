# OpenMDK HMO1 experimental slice — BF11AI

Run build/OpenMDK-HMO1-Experimental.exe on Windows x64.

WASD move, Q/E descend/ascend, Shift fast movement, arrows turn/look, click captures mouse, Esc releases mouse, R resets, F12 saves a screenshot to Godot user data. Descend with Q through three survey markers to finish the short slice, then explore freely. The markers/objective and flight camera are experimental additions.

Implemented: original HMO1 assets (21 source textures, palette and 394 nondegenerate packed geometry triangles); keyboard/mouse input; fixed 60 Hz point-segment BSP collision port; repeatable short objective; in-build collision comparison against 300 Python reference cases. BF11Y separately compared the Python reference with original executable x86 on 2000 cases.

Partial: packed collision-face geometry is adapted for rendering, not the prior 6216-polygon token-native RenderIR baseline. Face UVs normalized by texture dimensions and materials are diagnostic mappings. Lighting is unshaded, culling disabled. Collision is point-based without capsule/slide/gravity. Preview camera starts at (-220,-200,450), yaw60 pitch-35; the DTI (-4,0,190,96) seed is retained in source IR but is not used as a retail camera claim.

Missing: full retail startup/resource activation, retail camera/entity logic, enemies/combat, animation, sound, transitions, save CRT/OS environment, glass/mirror behavior and original runtime fidelity oracle. This is not VERIFIED BF12.

Validation and captures in evidence/ are from this same exported executable. A --smoke --capture-dir <absolute directory> invocation drives Q press/release through Godot input events, collects three markers in 360 physics ticks, validates collision and records PNGs plus smoke.json. Synthetic input is explicit; normal player input uses the same handler. No retail screenshot/framebuffer is supplied.

BF11AI correction: BF11AG incorrectly treated the 112-color local palette and following bytes as a full 256-color palette. This build uses the DTI base palette and places the HMO1 local palette at indices64..175, as original activation does. Original 0x422C00 constructed all198+21 material records; all20 HMO1 names resolve. Texture width/height/pixel addresses match those records. This is executable/source evidence, not retail screenshot fidelity.

BF11AI adds the actual object0 flag3 portal selector: 744 original-x86 comparisons, no differences. P jumps the experimental camera to (0,652,115); hold W to cross Y654. The original predicate selects CHMO_1/index10. The slice records this target and stops at an explicit missing-activation gate; it does not load or pretend to enter CHMO_1. Portal detection is source-backed; P camera teleport and this gate UI are experimental. Use R for the normal survey slice. --portal-smoke runs this crossing through the same input/physics path.
