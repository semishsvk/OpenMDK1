shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

// Positions are texels in the original 256 by 357 H1_FRONT artwork.
uniform sampler2D facade : source_color, repeat_enable, filter_linear_mipmap_anisotropic;

bool inside_panel(vec2 p, vec4 bounds) {
	return all(greaterThanEqual(p, bounds.xy)) && all(lessThan(p, bounds.zw));
}

void fragment() {
	vec2 p = fract(UV) * vec2(256.0, 357.0);
	// Sample outside the conditional so implicit texture derivatives stay defined.
	vec3 ink = texture(facade, UV).rgb;
	bool lamp = inside_panel(p, vec4(111.0, 141.0, 139.0, 150.0))
		|| inside_panel(p, vec4(106.0, 163.0, 142.0, 173.0))
		|| inside_panel(p, vec4(106.0, 179.0, 143.0, 186.0))
		|| inside_panel(p, vec4(101.0, 193.0, 146.0, 200.0));
	float warm = min(ink.r, ink.g) - ink.b;
	float cool = min(ink.g, ink.b) - ink.r;
	float coverage = smoothstep(0.035, 0.25, max(warm, cool));
	if (!lamp || coverage <= 0.0) {
		discard;
	}
	ALBEDO = ink * 0.32;
	ALPHA = coverage;
}
