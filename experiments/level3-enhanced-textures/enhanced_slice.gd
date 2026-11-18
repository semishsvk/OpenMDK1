extends "res://main.gd"

const GATE_LAMPS := preload("res://gate_lamps.gdshader")

const DoorPreview := preload("res://door_preview.gd")

var door: DoorPreview
var door_available := false
var enhanced_enabled := false
var gate_lamps_enabled := false
var facade_material: StandardMaterial3D
var original_facade_pass: Material
var lamp_pass: ShaderMaterial
var surfaces: Array[StandardMaterial3D] = []
var original_textures: Array[Texture2D] = []
var original_filters: Array[int] = []
var replacements: Array[Texture2D] = []


func _ready() -> void:
	super()
	for child in get_children():
		if not child is MeshInstance3D:
			continue
		var material := child.material_override as StandardMaterial3D
		if material == null or material.albedo_texture == null:
			continue
		var source := material.albedo_texture
		if source.resource_path.get_base_dir() != "res://textures":
			continue
		if source.resource_path == "res://textures/H1_FRONT.png":
			facade_material = material
			original_facade_pass = material.next_pass
		surfaces.append(material)
		original_textures.append(source)
		original_filters.append(material.texture_filter)
	door_available = DoorPreview.assets_available()
	var args := OS.get_cmdline_user_args()
	gate_lamps_enabled = "--gate-lamps" in args
	if "--enhanced-textures" in args or "--door-preview" in args:
		set_enhanced(true)
	if "--door-preview" in args:
		if door_available and enhanced_enabled:
			if not smoke:
				pose = Vector3(-9, 583, 119)
				heading = 80.0
				pitch = -6.0
				update_camera()
			play_door_preview()
		else:
			push_warning("Stage the door preview with prepare.py --asset-import.")
	update_hud()


func set_enhanced(enabled: bool) -> void:
	if enabled and replacements.is_empty():
		var loaded: Array[Texture2D] = []
		for source in original_textures:
			var path := "res://enhanced/" + source.resource_path.get_file()
			if not ResourceLoader.exists(path):
				push_warning("Missing enhanced texture: " + path)
				return
			var enhanced := load(path) as Texture2D
			if enhanced == null or enhanced.get_size() != source.get_size() * 4:
				push_warning("Invalid enhanced texture: " + path)
				return
			loaded.append(enhanced)
		replacements = loaded
	enhanced_enabled = enabled and not replacements.is_empty()
	if not enhanced_enabled and door != null:
		door.cancel()
	for index in surfaces.size():
		var material := surfaces[index]
		if enhanced_enabled:
			material.albedo_texture = replacements[index]
			material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		else:
			material.albedo_texture = original_textures[index]
			material.texture_filter = original_filters[index]
	update_gate_lamps()
	update_hud()


func update_gate_lamps() -> void:
	if facade_material == null:
		return
	if not enhanced_enabled or not gate_lamps_enabled:
		facade_material.next_pass = original_facade_pass
		return
	if lamp_pass == null:
		lamp_pass = ShaderMaterial.new()
		lamp_pass.shader = GATE_LAMPS
		lamp_pass.set_shader_parameter("facade", facade_material.albedo_texture)
		lamp_pass.next_pass = original_facade_pass
	facade_material.next_pass = lamp_pass


func play_door_preview() -> void:
	if not enhanced_enabled or not door_available:
		return
	if door == null:
		door = DoorPreview.new()
		door.position = world(Vector3(0, 632, 104))
		door.rotation.y = deg_to_rad(-90.0)
		add_child(door)
	door.play_preview()


func reset() -> void:
	if door != null:
		door.cancel()
	super()


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.keycode == KEY_F5 and door_available:
		if event.pressed and not event.echo:
			play_door_preview()
		get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.keycode == KEY_F4:
		if enhanced_enabled and event.pressed and not event.echo:
			gate_lamps_enabled = not gate_lamps_enabled
			update_gate_lamps()
			update_hud()
		get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.keycode == KEY_F3:
		if event.pressed and not event.echo:
			set_enhanced(not enhanced_enabled)
		get_viewport().set_input_as_handled()
		return
	super(event)


func update_hud() -> void:
	super()
	var mode := "Enhanced 4×" if enhanced_enabled else "Original"
	hud.text += "\nF3 Textures · %s" % mode
	if enhanced_enabled:
		hud.text += "   F4 Gate lamps · " + ("On" if gate_lamps_enabled else "Off")
		if door_available:
			hud.text += "   F5 Door impact preview"
