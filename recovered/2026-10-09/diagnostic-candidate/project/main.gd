extends Node3D
const PortalPort=preload("res://portal.gd")
const CollisionPort=preload("res://collision.gd")
const ActivationPort=preload("res://activation.gd")
var ir:Dictionary
var collision
var activation
var active_object=0
var previous_object=-1
var transition_pose=Vector3.ZERO
var kurt:MeshInstance3D
var cam:Camera3D
var hud:Label
var pose=Vector3(-220,-200,450)
var heading=60.0
var pitch=-35.0
var tick=0
var collected=0
var markers=[]
var trace=[]
var blocked=0
var portal_smoke=false
var pending_target=-1
var portal_validation={}
var smoke=false
var captures=""
var input_events=0
var validation={}
var held={}
func world(v:Vector3)->Vector3:return Vector3(v.x,v.z,-v.y)
func vec(a:Array)->Vector3:return Vector3(a[0],a[1],a[2])
func _ready():
 ir=JSON.parse_string(FileAccess.get_file_as_string("res://hmo1.json"))
 collision=CollisionPort.new(ir)
 activation=ActivationPort.new()
 kurt=MeshInstance3D.new();kurt.mesh=load("res://KURT_FALL3D_structural.obj");kurt.scale=Vector3(3,3,3);add_child(kurt)
 var km=StandardMaterial3D.new();km.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;km.albedo_color=Color(0.9,0.75,0.35);kurt.material_override=km
 var args=OS.get_cmdline_user_args()
 for i in range(args.size()):
  if args[i]=="--smoke":smoke=true
  if args[i]=="--portal-smoke":smoke=true;portal_smoke=true
  if args[i]=="--capture-dir" and i+1<args.size():captures=args[i+1]
 if captures!="":DirAccess.make_dir_recursive_absolute(captures)
 var palette=JSON.parse_string(FileAccess.get_file_as_string("res://palette.json"))
 var groups={}
 for face in ir.faces:
  var key=face.material
  if not groups.has(key):groups[key]=[]
  groups[key].append(face)
 for key in groups:
  var vertices=PackedVector3Array();var uvs=PackedVector2Array()
  var dims=Vector2(1,1)
  if ir.textures.has(key):dims=Vector2(ir.textures[key].width,ir.textures[key].height)
  for face in groups[key]:
   for i in range(3):
    vertices.append(world(vec(ir.vertices[int(face.indices[i])])));uvs.append(Vector2(face.uv[i][0],face.uv[i][1])/dims)
  var arrays=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_TEX_UV]=uvs
  var mesh=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
  var instance=MeshInstance3D.new();instance.mesh=mesh
  var material=StandardMaterial3D.new();material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;material.cull_mode=BaseMaterial3D.CULL_DISABLED
  material.texture_filter=BaseMaterial3D.TEXTURE_FILTER_NEAREST;material.texture_repeat=true
  if ir.textures.has(key):material.albedo_texture=load("res://"+ir.textures[key].path)
  elif key.begins_with("PEN_"):
   var rgb=palette[int(key.substr(4))];material.albedo_color=Color8(int(rgb[0]),int(rgb[1]),int(rgb[2]))
  else:material.albedo_color=Color.MAGENTA
  instance.material_override=material;add_child(instance)
 var environment=WorldEnvironment.new();environment.environment=Environment.new();environment.environment.background_mode=Environment.BG_COLOR;environment.environment.background_color=Color(0.045,0.055,0.07);add_child(environment)
 cam=Camera3D.new();cam.near=0.05;cam.far=2000;cam.fov=70;cam.current=true;add_child(cam)
 for i in range(ir.waypoints.size()):
  var marker=MeshInstance3D.new();var mesh=SphereMesh.new();mesh.radius=0.35;mesh.height=0.7;marker.mesh=mesh;marker.position=world(vec(ir.waypoints[i]))
  var material=StandardMaterial3D.new();material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;material.albedo_color=Color(0.1,0.9,0.9);marker.material_override=material;add_child(marker);markers.append(marker)
 var canvas=CanvasLayer.new();add_child(canvas);hud=Label.new();hud.position=Vector2(18,18);hud.add_theme_font_size_override("font_size",19);canvas.add_child(hud)
 validate_portal();
 if portal_smoke:portal_approach()
 validate_collision();update_camera();update_hud();print("OPENMDK_SLICE_READY textured_faces=",ir.faces.size()," collision_cases=",validation.cases," mismatch=",validation.mismatches)
func validate_collision():
 var failures=[]
 for index in range(ir.collision_cases.size()):
  var c=ir.collision_cases[index];var hit=collision.query(vec(c.start),vec(c.end));var expected=c.hit
  if (hit.is_empty())!=(expected==null):failures.append(index);continue
  if not hit.is_empty():
   if hit[0]!=int(expected[0]) or hit[1]!=int(expected[1]) or hit[2].distance_to(vec(c.point))>0.002:failures.append(index)
 validation={"cases":ir.collision_cases.size(),"mismatches":failures.size(),"failure_indices":failures}
func _input(event):
 if event is InputEventKey and not event.echo:
  input_events+=1;held[event.keycode]=event.pressed
  if event.pressed and event.keycode==KEY_R:reset()
  if event.pressed and event.keycode==KEY_P:portal_approach()
  if event.pressed and event.keycode==KEY_ESCAPE:Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
  if event.pressed and event.keycode==KEY_F12:take_capture("manual")
 if event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_LEFT:Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
 if event is InputEventMouseMotion and Input.mouse_mode==Input.MOUSE_MODE_CAPTURED:
  heading-=event.relative.x*0.12;pitch=clamp(pitch-event.relative.y*0.12,-80.0,80.0)
func pressed(k:int)->float:return 1.0 if held.get(k,false) else 0.0
func synthetic_key(k:int,down:bool):
 var event=InputEventKey.new();event.keycode=k;event.pressed=down;Input.parse_input_event(event)
func _physics_process(_delta):
 if smoke and tick==0:synthetic_key(KEY_W if portal_smoke else KEY_Q,true)
 if smoke and tick==240:synthetic_key(KEY_W if portal_smoke else KEY_Q,false)
 var angle=deg_to_rad(heading);var forward=Vector3(cos(angle),sin(angle),0);var right=Vector3(sin(angle),-cos(angle),0)
 var motion=forward*(pressed(KEY_W)-pressed(KEY_S))+right*(pressed(KEY_D)-pressed(KEY_A))+Vector3(0,0,pressed(KEY_E)-pressed(KEY_Q))
 if motion.length()>1:motion=motion.normalized()
 heading+=(pressed(KEY_LEFT)-pressed(KEY_RIGHT))*1.0
 pitch=clamp(pitch+(pressed(KEY_UP)-pressed(KEY_DOWN))*0.75,-80.0,80.0)
 var speed=60.0 if held.get(KEY_SHIFT,false) else 3.0
 var target=pose+motion*speed/60.0
 var hit=collision.query(pose,target)
 if hit.is_empty():
  var portal_target=-1
  if pending_target<0:portal_target=PortalPort.query(pose,target)
  pose=target
  if portal_target>=0:
   pending_target=portal_target
   previous_object=active_object
   active_object=portal_target
   transition_pose=pose
   activation.begin(portal_target)
   print("SOURCE_PORTAL_SELECTED CHMO_1 index=",portal_target)
 elif motion.length()>0:blocked+=1
 if collected<markers.size() and pose.distance_to(vec(ir.waypoints[collected]))<0.65:
  markers[collected].visible=false;collected+=1;print("BEACON ",collected)
 if pending_target==10 and not activation.active():
  var activation_state=activation.step()
  if activation_state=="ACTIVE":
   active_object=10
   print("SOURCE_ACTIVATION_ACTIVE CHMO_1 index=10 previous=",previous_object," transition_pose=",transition_pose)
 kurt.position=world(pose);kurt.rotation.y=deg_to_rad(-heading)
 tick+=1;update_camera();update_hud()
 if tick%30==0:trace.append({"tick":tick,"pose":[pose.x,pose.y,pose.z],"yaw":heading,"collected":collected,"blocked":blocked,"pending_target":pending_target,"active_object":active_object,"activation_state":activation.state})
 if smoke and tick in [1,90,180,300]:call_deferred("take_capture","frame_%03d"%tick)
 if smoke and tick==360:call_deferred("finish_smoke")
func update_camera():
 cam.position=world(pose);var a=deg_to_rad(heading);var p=deg_to_rad(pitch);var direction=Vector3(cos(a)*cos(p),sin(a)*cos(p),sin(p));cam.look_at(cam.position+world(direction),Vector3.UP)
func update_hud():
 hud.text="OpenMDK HMO1 — EXPERIMENTAL\nOriginal assets · adapted mesh/UVs · flight camera, not retail replay\nWASD move · Q/E descend/ascend · Shift fast · arrows/click+mouse look\nEsc release mouse · R reset · P portal approach · F12 capture\nDescend through 3 cyan survey beacons: %d / 3\nCollision blocks: %d | XYZ %.2f %.2f %.2f"%[collected,blocked,pose.x,pose.y,pose.z]
 if collected==3:hud.text+="\nSurvey complete — free exploration unlocked"
 if pending_target==10:hud.text+="\nSOURCE PORTAL -> CHMO_1; activation "+activation.state+" (retail I/O timing unverified)."
func reset():
 pose=Vector3(-220,-200,450);heading=60;pitch=-35;collected=0;blocked=0;pending_target=-1;active_object=0;previous_object=-1;transition_pose=Vector3.ZERO;activation=ActivationPort.new()
 for marker in markers:marker.visible=true
func take_capture(name:String):
 await RenderingServer.frame_post_draw
 var dir=captures if captures!="" else "user://captures"
 DirAccess.make_dir_recursive_absolute(dir);var error=get_viewport().get_texture().get_image().save_png(dir+"/"+name+".png");print("CAPTURE ",name," error=",error)
func finish_smoke():
 var transition_ok=previous_object==0 and active_object==10 and activation.active() and pose.distance_to(transition_pose)>0.5
 var data={"status":"PASS" if validation.mismatches==0 and portal_validation.mismatches==0 and (transition_ok if portal_smoke else collected==3) and input_events>=2 else "FAIL","collision":validation,"portal":portal_validation,"portal_smoke":portal_smoke,"pending_target":pending_target,"previous_object":previous_object,"active_object":active_object,"transition_pose":[transition_pose.x,transition_pose.y,transition_pose.z],"transition_continued":pose.distance_to(transition_pose)>0.5,"activation":activation.snapshot(),"ticks":tick,"input_events":input_events,"collected":collected,"trace":trace,"source_sha256":ir.source_sha256,"renderer":RenderingServer.get_video_adapter_name(),"limitations":ir.limitations}
 var dir=captures if captures!="" else "user://captures";var file=FileAccess.open(dir+"/smoke.json",FileAccess.WRITE);file.store_string(JSON.stringify(data," "))
 print("OPENMDK_SMOKE ",data.status);get_tree().quit(0 if data.status=="PASS" else 1)

func validate_portal():
 var errors=[]
 for i in range(ir.portal.cases.size()):
  var c=ir.portal.cases[i];var result=PortalPort.query(vec(c.start),vec(c.end));var expected=-1 if c.target==null else int(c.target)
  if result!=expected:errors.append(i)
 portal_validation={"cases":ir.portal.cases.size(),"mismatches":errors.size(),"failures":errors}
func portal_approach():
 pose=Vector3(0,652,115);heading=90;pitch=0;pending_target=-1
 print("DIAGNOSTIC_PORTAL_APPROACH — camera teleport is experimental")
