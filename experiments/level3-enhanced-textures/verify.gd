extends SceneTree
## Run with a graphical renderer and a staged private project.

var failures: Array[String] = []
var capture_dir := ""


func _initialize() -> void:
	call_deferred("verify")


func check(ok: bool, message: String) -> void:
	if not ok:
		failures.append(message)
		push_error(message)


func press_f3(echo: bool = false) -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_F3
	event.pressed = true
	event.echo = echo
	root.push_input(event)
	event = event.duplicate()
	event.pressed = false
	event.echo = false
	root.push_input(event)


func frame(name: String) -> Image:
	await process_frame
	await RenderingServer.frame_post_draw
	var picture := root.get_texture().get_image()
	if not capture_dir.is_empty():
		check(picture.save_png(capture_dir.path_join(name + ".png")) == OK, "PNG: " + name)
	return picture


func verify() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("The frame comparison requires a graphical renderer.")
		quit(1)
		return
	var args := OS.get_cmdline_user_args()
	if "--capture-dir" in args:
		capture_dir = args[args.find("--capture-dir") + 1]
		check(DirAccess.make_dir_recursive_absolute(capture_dir) == OK, "Capture directory")

	var base := Node3D.new()
	base.set_script(load("res://main.gd"))
	root.add_child(base)
	base.set_physics_process(false)
	base.get("hud").hide()
	var reference := await frame("baseline")
	base.free()

	var scene = load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	scene.hud.hide()
	check(not scene.enhanced_enabled and scene.replacements.is_empty(), "Original startup")
	check(scene.surfaces.size() == 11, "HMO1 material count")
	var original := await frame("original")
	check(reference.get_data() == original.get_data(), "Baseline and Original pixels")
	var initial_pose: Vector3 = scene.pose
	var input_count: int = scene.input_events
	press_f3()
	check(scene.enhanced_enabled, "F3 enables Enhanced")
	press_f3(true)
	check(scene.enhanced_enabled, "Key repeat leaves mode selected")
	for i in scene.surfaces.size():
		var material: StandardMaterial3D = scene.surfaces[i]
		check(material.albedo_texture == scene.replacements[i], "Enhanced albedo binding")
		check(material.albedo_texture.get_image().has_mipmaps(), "Enhanced mip chain")
		check(material.texture_repeat, "UV repeat")
	var enhanced := await frame("enhanced")
	check(original.get_data() != enhanced.get_data(), "Enhanced changes rendered pixels")
	press_f3()
	check(not scene.enhanced_enabled, "F3 restores Original")
	for i in scene.surfaces.size():
		check(scene.surfaces[i].albedo_texture == scene.original_textures[i], "Original albedo")
		check(scene.surfaces[i].texture_filter == scene.original_filters[i], "Original sampler")
	check(scene.pose == initial_pose and scene.input_events == input_count, "Pose and input counters")
	var restored := await frame("restored")
	check(original.get_data() == restored.get_data(), "Restored frame equals Original")
	# A second fixed camera sits inside HMO1, looking towards the gate and facade.
	scene.pose = Vector3(0, 375, 132)
	scene.heading = 90.0
	scene.pitch = 4.0
	scene.update_camera()
	var gate := await frame("gate_original")
	press_f3()
	var gate_enhanced := await frame("gate_enhanced")
	check(gate.get_data() != gate_enhanced.get_data(), "Enhanced changes the gate view")
	press_f3()
	var gate_restored := await frame("gate_restored")
	check(gate.get_data() == gate_restored.get_data(), "Restored gate pixels")
	print("HMO1_TEXTURE_QA ", JSON.stringify({"surfaces": scene.surfaces.size(), "failures": failures}))
	quit(0 if failures.is_empty() else 1)
