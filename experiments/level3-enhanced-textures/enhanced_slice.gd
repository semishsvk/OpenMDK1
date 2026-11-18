extends "res://main.gd"

var enhanced_enabled := false
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
		surfaces.append(material)
		original_textures.append(source)
		original_filters.append(material.texture_filter)
	if "--enhanced-textures" in OS.get_cmdline_user_args():
		set_enhanced(true)
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
	for index in surfaces.size():
		var material := surfaces[index]
		if enhanced_enabled:
			material.albedo_texture = replacements[index]
			material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		else:
			material.albedo_texture = original_textures[index]
			material.texture_filter = original_filters[index]
	update_hud()


func _input(event: InputEvent) -> void:
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
