extends Node3D
## Optional post-unlock XH1_DOOR audition. It never dispatches gameplay callbacks.

signal impact(animation_frame: int)

const CUE_FRAMES := [60, 74]
const PANEL := "res://door/panel.json"
const SKIN := "res://door/panel.png"
const SOUND := "res://door/doorland.wav"

var panel := MeshInstance3D.new()
var emitter := AudioStreamPlayer3D.new()
var frame_index := -1
var clock := 0.0
var fps := 30.0
var frames: Array
var surfaces := {}
var materials := {}


static func assets_available() -> bool:
	return FileAccess.file_exists(PANEL) and ResourceLoader.exists(SKIN) and ResourceLoader.exists(SOUND)


func _ready() -> void:
	hide()
	set_physics_process(false)
	add_child(panel)
	add_child(emitter)
	var clip: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PANEL))
	fps = clip.fps
	frames = clip.frames
	var palette: Array = JSON.parse_string(FileAccess.get_file_as_string("res://palette.json"))
	var skin := load(SKIN) as Texture2D
	var size := skin.get_size()
	for face in clip.faces:
		var slot := int(face.material)
		if not materials.has(slot):
			var mat := StandardMaterial3D.new()
			mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			if slot == 0:
				mat.albedo_texture = skin
			else:
				var rgb: Array = palette[-slot]
				mat.albedo_color = Color8(int(rgb[0]), int(rgb[1]), int(rgb[2]))
			materials[slot] = mat
			surfaces[slot] = {"indices": [], "uv": PackedVector2Array()}
		var group: Dictionary = surfaces[slot]
		group.indices.append_array(face.indices)
		for uv in face.uv:
			group.uv.append(Vector2(uv[0], uv[1]) / size)
	emitter.stream = make_impact_pair(load(SOUND) as AudioStreamWAV)
	emitter.unit_size = 35.0
	# Each voice uses half scale in the PCM pair to leave headroom for overlap.
	emitter.volume_db = -7.0 + linear_to_db(2.0)


func make_impact_pair(source: AudioStreamWAV) -> AudioStreamWAV:
	# Separate play() calls land on audio mix block boundaries. One spatial stream
	# keeps the two onsets sample-accurate while the listener is free to move.
	var delay := roundi((CUE_FRAMES[1] - CUE_FRAMES[0]) * source.mix_rate / fps)
	var sample := source.data
	var count := sample.size() + delay
	var mix := PackedByteArray()
	mix.resize(count * 2)
	for i in count:
		var value := sample.decode_s8(i) if i < sample.size() else 0
		if i >= delay:
			value += sample.decode_s8(i - delay)
		mix.encode_s16(i * 2, value * 128)
	var pair := AudioStreamWAV.new()
	pair.format = AudioStreamWAV.FORMAT_16_BITS
	pair.mix_rate = source.mix_rate
	pair.data = mix
	return pair


func play_preview() -> void:
	emitter.stop()
	clock = 0.0
	apply_frame(0)
	show()
	set_physics_process(true)


func cancel() -> void:
	set_physics_process(false)
	hide()
	emitter.stop()
	frame_index = -1


func _physics_process(delta: float) -> void:
	clock += delta
	var next := mini(floori(clock * fps + 0.000001), frames.size() - 1)
	if next == frame_index:
		return
	var previous := frame_index
	apply_frame(next)
	for cue: int in CUE_FRAMES:
		if previous < cue and cue <= next:
			if cue == CUE_FRAMES[0]:
				emitter.play()
			impact.emit(cue)
	if next == frames.size() - 1:
		set_physics_process(false)


func apply_frame(index: int) -> void:
	frame_index = index
	var pose: Array = frames[index]
	var mesh := ArrayMesh.new()
	for slot in surfaces:
		var vertices := PackedVector3Array()
		var group: Dictionary = surfaces[slot]
		for vertex in group.indices:
			var p: Array = pose[int(vertex)]
			vertices.append(Vector3(p[0], p[2], -p[1]))
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = vertices
		arrays[Mesh.ARRAY_TEX_UV] = group.uv
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		mesh.surface_set_material(mesh.get_surface_count() - 1, materials[slot])
	panel.mesh = mesh
