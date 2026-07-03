** This is a WIP **

## Measuring gantry induced nozzle probe distance variation
(and eventually compensating for it)

This may not be due to gantry differences, but currently its my lead suspect.

### Intro
Ive often thought about and there is discussion about, the potential error that could creep into a bed mesh due to the probe being offset (in a different location) than the nozzle. In a perfect world this would not happen, but when it takes only .01-.05 of a millimeter of difference to effect first layer results, you could imagine thats its possible. 

For example a gantry or rail having a minute bow, sag or twist, such that at different points along an axis the z height difference between the nozzle and the sensor changes.

This is a theory im investigating to hopefully explain and one day fix variation in first layer finish across a bed, generally more noticable when printing a full bed, despite automatic bed levelling.

Now you could just do a full mesh using the nozzle tip to get rule out differences by the sensor, and i might try this one day. But im not sure this is an ideal workaround.


One outcome could be to map this variation and then apply it as a correction when bed meshes are made.

### Measurement code

The first step is to find out if this even happens and if its repeatable and consistent.

So with the help of AI, Im working on this gcode macro to map and measure variation if present:
(This is put at the bottom of gcode_macro.cfg, klipper restarted, and then GRID_PROBE_COMPARE selected from the marco menu, the result being printed to console at the end)

This code will measure the Z with the nozzle and then the probe for each given point, you can look for differences between points, as ideally there should be no difference.

```
[gcode_macro GRID_PROBE_COMPARE]
variable_z_nozzle: 0
variable_z_sensor: 0
variable_nozzle_vals: []
variable_sensor_vals: []
variable_x_vals: []
variable_y_vals: []
gcode:
    {% set points = [
		(35, 162),
		(72, 162),
		(109, 162),
		(146, 162),
		(183, 162),
		(220, 162),
		(257, 162),
		(294, 162)
	] %}
    {% set xoff = printer.probe["x_offset"]|float %}
    {% set yoff = printer.probe["y_offset"]|float %}
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=nozzle_vals VALUE="[]"
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=sensor_vals VALUE="[]"
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=x_vals VALUE="[]"
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=y_vals VALUE="[]"
    _CG28
    Z_TILT_ADJUST
    {% for point in points %}
        ; --- PIN_1 = nozzle contact probe (true point, no shift needed) ---
        G1 X{point[0]} Y{point[1]} F9000
        G1 Z10 F600
        M400
        QIDI_PROBE_PIN_1
        probe samples=3 sample_retract_dist=5 probe_speed=5 lift_speed=5
        _CAPTURE_NOZZLE

        G1 Z10 F600
        M400

        ; --- PIN_2 = non-contact sensor (shifted so sensor sits over true point) ---
        G1 X{point[0] - xoff} Y{point[1] - yoff} F9000
        QIDI_PROBE_PIN_2
        probe samples=3 sample_retract_dist=5 probe_speed=5 lift_speed=5
        _CAPTURE_SENSOR

        _APPEND_RESULT X={point[0]} Y={point[1]}
        G1 Z10 F600
    {% endfor %}
    QIDI_PROBE_PIN_2
    _PRINT_RESULTS

[gcode_macro _CAPTURE_NOZZLE]
gcode:
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=z_nozzle VALUE={printer.probe.last_z_result}

[gcode_macro _CAPTURE_SENSOR]
gcode:
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=z_sensor VALUE={printer.probe.last_z_result}

[gcode_macro _APPEND_RESULT]
gcode:
    {% set m = "gcode_macro GRID_PROBE_COMPARE" %}
    {% set nv = printer[m].nozzle_vals %}
    {% set sv = printer[m].sensor_vals %}
    {% set xv = printer[m].x_vals %}
    {% set yv = printer[m].y_vals %}
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=nozzle_vals VALUE="{nv + [printer[m].z_nozzle]}"
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=sensor_vals VALUE="{sv + [printer[m].z_sensor]}"
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=x_vals VALUE="{xv + [params.X|float]}"
    SET_GCODE_VARIABLE MACRO=GRID_PROBE_COMPARE VARIABLE=y_vals VALUE="{yv + [params.Y|float]}"

[gcode_macro _PRINT_RESULTS]
gcode:
    {% set m = "gcode_macro GRID_PROBE_COMPARE" %}
    {% set nv = printer[m].nozzle_vals %}
    {% set sv = printer[m].sensor_vals %}
    {% set xv = printer[m].x_vals %}
    {% set yv = printer[m].y_vals %}
    RESPOND MSG="=== GRID PROBE RESULTS ==="
    {% for i in range(nv|length) %}
        {% set delta = sv[i] - nv[i] %}
        RESPOND MSG="X={xv[i]} Y={yv[i]} nozzle={'%.6f'|format(nv[i])} sensor={'%.6f'|format(sv[i])} delta={'%.6f'|format(delta)}"
    {% endfor %}
```

For reference the nozzle is chosen with
```
 QIDI_PROBE_PIN_1
```
and the probe is chosen with
```
QIDI_PROBE_PIN_2
```
and the plus 4 nozzle offset is
```
x_offset=25.0  y_offset=1.3
```

### Here is some results from me running it 3 times
(there definately seems to be some consistent variation worth investigation further)

| X | Y | Run1 delta | Run2 delta | Run3 delta | Avg delta |
|---|---|---|---|---|---|
| 60 | 60 | 1.535 | 1.528 | 1.518 | **1.527** |
| 166 | 60 | 1.530 | 1.517 | 1.521 | **1.523** |
| 270 | 60 | 1.543 | 1.540 | 1.501 | **1.528** |
| 60 | 162 | 1.487 | 1.485 | 1.486 | **1.486** |
| 166 | 162 | 1.514 | 1.515 | 1.513 | **1.514** |
| 270 | 162 | 1.479 | 1.479 | 1.492 | **1.484** |
| 60 | 265 | 1.499 | 1.503 | 1.509 | **1.504** |
| 166 | 265 | 1.472 | 1.462 | 1.465 | **1.466** |
| 270 | 265 | 1.507 | 1.501 | 1.469 | **1.492** |
(ai can help you make a nice table from your raw results)
