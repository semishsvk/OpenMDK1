extends SceneTree
## Draw fixed material samples along the same camera path at three native resolutions.

const FRAME_COUNT := 16
const PATCH_SIZE := Vector2i(128, 48)
# Upper left in the 1920x1080 frame: near floor, distant floor, right metal strip.
const PATCH_ORIGINS := [Vector2i(896, 870), Vector2i(896, 593), Vector2i(1348, 218)]


func _initialize() -> void:
	call_deferred("capture")


func apply_material_ids(scene: Node) -> void:
	for child in scene.get_children():
		if not child is MeshInstance3D:
			continue
		var material := child.material_override as StandardMaterial3D
		if material == null:
			continue
		var file := ""
		if material.albedo_texture != null:
			file = material.albedo_texture.resource_path.get_file()
		material.albedo_texture = null
		material.albedo_color = Color.BLACK
		if file.begins_with("H1_FLR"):
			material.albedo_color = Color.RED
		elif file.begins_with("H1_EDGE"):
			material.albedo_color = Color.GREEN


func capture() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2 or DisplayServer.get_name() == "headless":
		push_error("Expected a graphical display and -- <height> <new output directory> [--mask]")
		quit(1)
		return
	var height := args[0].to_int()
	var destination := args[1]
	if height not in [1080, 2160, 4320] or DirAccess.dir_exists_absolute(destination):
		push_error("Expected height 1080/2160/4320 and a new output directory.")
		quit(1)
		return
	if DirAccess.make_dir_recursive_absolute(destination) != OK:
		push_error("Cannot create " + destination)
		quit(1)
		return
	@warning_ignore("integer_division")
	var scale := height / 1080
	var view := SubViewport.new()
	view.size = Vector2i(1920, 1080) * scale
	view.world_3d = World3D.new()
	view.render_target_update_mode = SubViewport.UPDATE_DISABLED
	root.add_child(view)
	var scene = load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	view.add_child(scene)
	scene.set_physics_process(false)
	scene.hud.hide()
	scene.set_enhanced(true)
	if not scene.enhanced_enabled or scene.surfaces.size() != 11:
		push_error("The staged HMO1 experiment and all 11 enhanced textures are required.")
		quit(1)
		return
	if "--mask" in args:
		apply_material_ids(scene)
	for i in FRAME_COUNT:
		scene.pose = Vector3(i * 0.08, 370.0 + i * 0.45, 121.0)
		scene.heading = 90.0
		scene.pitch = -2.0
		scene.update_camera()
		view.render_target_update_mode = SubViewport.UPDATE_ONCE
		await RenderingServer.frame_post_draw
		var frame := view.get_texture().get_image()
		if frame == null or frame.get_size() != view.size:
			push_error("Framebuffer readback failed at " + str(view.size))
			quit(1)
			return
		var size := PATCH_SIZE * scale
		var strip := Image.create_empty(size.x, size.y * PATCH_ORIGINS.size(), false, frame.get_format())
		for row in PATCH_ORIGINS.size():
			strip.blit_rect(frame, Rect2i(PATCH_ORIGINS[row] * scale, size), Vector2i(0, row * size.y))
		if strip.save_png(destination.path_join("%02d.png" % i)) != OK:
			push_error("Could not save frame " + str(i))
			quit(1)
			return
	print("HMO1_MOTION_CAPTURE height=", height, " frames=", FRAME_COUNT, " project_anisotropy=",
			ProjectSettings.get_setting("rendering/textures/default_filters/anisotropic_filtering_level"))
	quit()
