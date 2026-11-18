extends SceneTree
## Run at 60 physics ticks/s with --write-movie to verify the recorded stereo mix.

var failures: Array[String] = []
var events: Array = []
var shots: Array = []
var scene


func _initialize() -> void:
	call_deferred("verify")


func check(ok: bool, what: String) -> void:
	if not ok:
		failures.append(what)
		push_error(what)


func press(key: Key, echo := false) -> void:
	var event := InputEventKey.new()
	event.keycode = key
	event.pressed = true
	event.echo = echo
	root.push_input(event)
	event = event.duplicate()
	event.pressed = false
	event.echo = false
	root.push_input(event)


func wait_ticks(count: int) -> void:
	for i in count:
		await physics_frame


func heard(frame: int) -> void:
	events.append({"cue": frame, "tick": Engine.get_physics_frames(), "movie": Engine.get_process_frames()})


func verify() -> void:
	scene = load(ProjectSettings.get_setting("application/run/main_scene")).instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	scene.hud.hide()
	if not scene.door_available:
		push_error("Stage the private door inputs before running this test.")
		quit(1)
		return
	var gameplay_inputs: int = scene.input_events
	press(KEY_F5)
	check(scene.door == null, "Original F5 is silent")
	press(KEY_F3)
	press(KEY_F5)
	check(scene.door != null and scene.door.visible, "F5 creates panel")
	scene.door.impact.connect(heard)
	check(scene.door.global_position == Vector3(0, 104, -632), "HMO1 source position")
	var clip := load("res://door/doorland.wav") as AudioStreamWAV
	check(clip.format == AudioStreamWAV.FORMAT_8_BITS and not clip.stereo and clip.mix_rate == 22050, "Imported mono PCM")
	var pcm := clip.data
	for i in pcm.size():
		pcm[i] ^= 128  # Godot signed 8-bit -> RIFF unsigned PCM
	var hash_ctx := HashingContext.new()
	hash_ctx.start(HashingContext.HASH_SHA256)
	hash_ctx.update(pcm)
	check(hash_ctx.finish().hex_encode() == "b5bc01fe1346bc58d9fce8be405f975fc49120ecae8d2576c2e071bc3561492f", "Imported sample bytes")
	var pair_stream := scene.door.emitter.stream as AudioStreamWAV
	var pair_data := pair_stream.data
	var exact := pair_stream.format == AudioStreamWAV.FORMAT_16_BITS and pair_stream.mix_rate == clip.mix_rate
	exact = exact and not pair_stream.stereo and pair_data.size() == (pcm.size() + 10290) * 2
	if exact:
		for i in pcm.size() + 10290:
			var a := int(pcm[i]) - 128 if i < pcm.size() else 0
			var b := int(pcm[i - 10290]) - 128 if i >= 10290 else 0
			if pair_data.decode_s16(2 * i) != (a + b) * 128:
				exact = false
				break
	check(exact, "Every mixed sample equals two lossless impacts 10290 samples apart")
	await wait_ticks(20)
	press(KEY_F5, true)
	check(scene.door.frame_index > 0, "Held F5 does not restart")
	press(KEY_F3)
	check(not scene.door.visible and not scene.door.emitter.playing, "F3 cancels preview")
	await wait_ticks(152)
	check(events.is_empty(), "Cancelled audition emits no delayed cue")
	press(KEY_F3)
	for shot in [["left", 45, 587], ["centre", 90, 587], ["right", 135, 587], ["far", 90, 497]]:
		scene.pose = Vector3(0, shot[2], 115)
		scene.heading = shot[1]
		scene.pitch = -6.0
		scene.update_camera()
		var before := events.size()
		press(KEY_F5)
		var start := Engine.get_physics_frames()
		await wait_ticks(215)
		var pair := events.slice(before)
		check(pair.size() == 2, str(shot[0]) + " two impacts")
		if pair.size() == 2:
			check(pair[0].cue == 60 and pair[1].cue == 74 and pair[1].tick - pair[0].tick == 28, "Impact spacing")
			check(absi(pair[0].tick - start - 120) <= 1, "First impact timing")
		check(scene.door.frame_index == 85, "Terminal pose")
		shots.append({"name": shot[0], "events": pair})
	# Cancel while the first impact is audible; the second animation event must stay cancelled.
	press(KEY_F5)
	await wait_ticks(130)
	var count := events.size()
	check(scene.door.emitter.playing, "First tail is active")
	press(KEY_F3)
	await wait_ticks(88)
	check(not scene.door.emitter.playing and not scene.door.visible and events.size() == count, "Active cancellation")
	check(scene.input_events == gameplay_inputs, "Preview keys do not count as gameplay inputs")
	print("HMO1_DOOR_QA ", JSON.stringify({"shots": shots, "failures": failures}))
	quit(0 if failures.is_empty() else 1)
