# Better Bed Meshing

## Introduction

## What I changed and why

All the following configuration changes are done within the `printer.cfg` file

### Z-stepper changes

Find the `[stepper_z]` and `[stepper_z1]` sections, and set microsteps to 16

eg.

```
[stepper_z]
step_pin:U_1:PB1
dir_pin:U_1:PB6
enable_pin:!U_1:PB0
microsteps: 16
rotation_distance: 4
full_steps_per_rotation: 200
endstop_pin:probe:z_virtual_endstop # U_1:PC3 for Z-max
endstop_pin_reverse:tmc2209_stepper_z:virtual_endstop
position_endstop:1
position_endstop_reverse:285
position_max:285
position_min: -4
homing_speed: 10
homing_speed_reverse: 10
second_homing_speed: 5
homing_retract_dist: 5.0
homing_positive_dir:false
homing_positive_dir_reverse:true
#step_pulse_duration:0.0000001

[stepper_z1]
step_pin:U_1:PC10
dir_pin:U_1:PA15
enable_pin:!U_1:PC11
microsteps: 16
rotation_distance: 4
full_steps_per_rotation: 200
endstop_pin_reverse:tmc2209_stepper_z1:virtual_endstop
#step_pulse_duration:0.0000001
```

Also find the `[tmc2209 stepper_z]` and `[tmc2209 stepper_z1]` sections, and ensure interpolate is set to False

eg.

```
[tmc2209 stepper_z]
uart_pin:U_1: PB7
run_current: 1.07
# hold_current: 0.17
interpolate: False
stealthchop_threshold: 99999
diag_pin:^U_1:PA13
driver_SGTHRS:100

[tmc2209 stepper_z1]
uart_pin:U_1: PC5
run_current: 1.07
# hold_current: 0.17
interpolate: False
stealthchop_threshold: 99999
diag_pin:^U_1:PC12
driver_SGTHRS:100
```

### Z-Tilt

Find the `[z_tilt]` section, and modify the `horizontal_move_z`, `retries`, and `retry_tolerance` fields like so:

```
[z_tilt]
z_positions:
    -17.5,138.5
    335.7,138.5

points:
    0,138.5
    255,138.5

speed: 150
horizontal_move_z: 10
retries: 5
retry_tolerance: 0.013
```

### Smart Effector

Find the `[smart_effector]` section, and modify `speed`, `samples`, and `sample_retract_dist` fields

```
[smart_effector]
pin:U_1:PC1
recovery_time:0
x_offset: 25
y_offset: 1.3
z_offset: 0.000001
speed:2.5
lift_speed:5
probe_accel:50
samples: 1
samples_result: submaxmin
sample_retract_dist: 10
samples_tolerance: 0.013
samples_tolerance_retries:5
```

### Bed Mesh

Find the `[bed_mesh]` section, and change it to the following:

```
[bed_mesh]
speed:150
horizontal_move_z:10
mesh_min:25,10
mesh_max:295,295
probe_count:11,11
algorithm:bicubic
bicubic_tension:0.3
mesh_pps: 2,2
```
