extends Node3D
var world: MeshInstance3D
var kurt: MeshInstance3D
var cam: Camera3D
func load_obj(path:String)->ArrayMesh:
 var verts=PackedVector3Array(); var inds=PackedInt32Array()
 for l in FileAccess.get_file_as_string(path).split("\n"):
  if l.begins_with("v "):
   var p=l.split(" ",false); verts.append(Vector3(float(p[1]),float(p[3]),-float(p[2])))
  elif l.begins_with("f "):
   var p=l.split(" ",false); inds.append(int(p[1])-1); inds.append(int(p[2])-1); inds.append(int(p[3])-1)
 var a=[]; a.resize(Mesh.ARRAY_MAX); a[Mesh.ARRAY_VERTEX]=verts; a[Mesh.ARRAY_INDEX]=inds
 var m=ArrayMesh.new(); m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a); return m
func _ready():
 world=MeshInstance3D.new(); add_child(world); world.mesh=load_obj("res://LEVEL3.obj")
 var wm=StandardMaterial3D.new(); wm.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED; wm.albedo_color=Color(0.55,0.58,0.62); world.material_override=wm
 kurt=MeshInstance3D.new(); add_child(kurt); kurt.mesh=load_obj("res://KURT.obj"); kurt.scale=Vector3(30,30,30); kurt.position=Vector3(680,40,-2115)
 var km=StandardMaterial3D.new(); km.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED; km.albedo_color=Color(0.9,0.75,0.35); kurt.material_override=km
 cam=Camera3D.new(); add_child(cam); cam.position=Vector3(680,180,-2450); cam.look_at(Vector3(680,40,-2115)); cam.current=true; cam.fov=70
 print("OPENMDK1_LEVEL3_RUNTIME world=7205tri kurt=363tri")
func _process(delta):
 var t=Time.get_ticks_msec()/1000.0; cam.position=Vector3(680+sin(t*.25)*120,180,-2450+cos(t*.25)*80); cam.look_at(Vector3(680,40,-2115))