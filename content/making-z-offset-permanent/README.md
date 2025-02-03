# Making Z Offset Permanent

## The issue

The Qidi Plus 4 has automatic Z-offset detection, however sometimes the offset that it decides upon may not be quite right.

If we print a large single layer sheet, we can adjust the Z offset on the printer's display screen until we observe that the first layer is going down properly.

This new z offset value is saved to the `saved_variables.cfg` file under the `z_offset` field.

Under certain operations this offset value can be reset back to 0, possibly causing first layer issues once again until set again until we set back to the appropriate value.

The operations that cause the z offset to be reset is not yet completely understood at this moment.


## The Permanent Fix

The way to permanently apply a Z offset value is to add it to the `[smart_effector]` section in the `printer.cfg` file.

As an example, on my printer I determined that an appropriate `z_offset` was 0.04mm as configured on the printer's display screen.

To set this offset permanently, change the sign of the value (eg. 0.04 becomes -0.04, or -0.05 would become 0.05) and copy that value into the `z_offset` field under the `smart_effector` section in the `printer.cfg` file.

An example of this is the following:


```
[smart_effector]
pin:U_1:PC1
recovery_time:0
x_offset: 25
y_offset: 1.3
z_offset: -0.04
speed:5
lift_speed:5
probe_accel:50
samples: 2
samples_result: submaxmin
sample_retract_dist: 5
samples_tolerance: 0.05
samples_tolerance_retries:5
```

After applying this offset value and saving the updated `printer.cfg` file, we MUST edit `saved_variables.cfg` file and set `z_offset` there back to 0.

Ignore all the other values there.

For example:

```
[Variables]
bed_temp = 75.0
file_path = '/home/mks/gcode_files/.cache/3DBenchy.gcode'
filepath = ''
gcode_lines = 50
hot_temp = 0.0
last_file = ''
power_resume_z = 58.0
print_temp = 240.0
profile_name = 'kamp'
was_interrupted = False
z_offset = 0.0
```

## Fixing `gcode_macro.cfg`

Additionally, we need to change the `PRINT_END` and `save_zoffset` macros in the `gcode_macro.cfg` file.

Open up your `gcode_macro.cfg` file, and find the `PRINT_END` macro and comment out the lines as in the below example

```
[gcode_macro PRINT_END]
gcode:
#    {% if printer.gcode_move.homing_origin.z < 0.5 %}
#       SAVE_VARIABLE VARIABLE=z_offset VALUE={printer.gcode_move.homing_origin.z}
#    {% endif %}
```

This prevents the macro from writing over the stored 0 value in `saved_variables.cfg`

We also need to do the same thing in the following `save_zoffset` macro (also in `gcode_macro.cfg`)

```
[gcode_macro save_zoffset]
gcode:
#    {% if printer.gcode_move.homing_origin.z < 0.5 %}
#       SAVE_VARIABLE VARIABLE=z_offset VALUE={printer.gcode_move.homing_origin.z}
#    {% endif %}
```

Just comment out those 3 lines
