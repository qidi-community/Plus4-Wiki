# Better Bed Meshing

## Caveat Emptor

**NOTE:** It has been reported that the approach documented here does not always work well for all machines.  I suspect that this may be down to variances in the inductive
probes that the machines are fitted with.  As mentioned below, in my situation, the variances from sample to sample were tiny, but some users on Discord have
reported wider variations.  If you encounter issues with the following recommendations then pleae revert back to the stock configuration.  I'll continue to
work with others in the meantime to see if there's a method that works better for all Qidi Plus 4 machines.

## Introduction

When bed meshing, I observed that quite frequently, especially at higher bed temperatures, that the probe points would vary quite wildly from sample to sample from time to time.

I then found this issue documented for Klipper here: https://klipper.discourse.group/t/bug-accumulating-microstep-shift-during-probe-moves-related-to-endstop-oversampling/19429

There appears to be a bug in Klipper where it does not accurately track the microstep counts for multiple Z-probes.

Most notably, I wanted to come up with a solution that addresses these main fix suggestions from the OP of that discussion thread:

- Reducing microsteps to 16 eliminates the issue when probing at 3 mm/s.
- Setting ENDSTOP_SAMPLE_COUNT to 1 eliminates the issue at the cost of disabling noise filtering (which seems unnecessary on modern printer hardware)
- Increasing ENDSTOP_SAMPLE_COUNT exacerbates the problem (e.g., 32 samples increases error to 4-5 microsteps per probe move in our case)
- The issue has been reproduced on several machines with different stepper drivers (TMC2209, TMC5160)

In addition to the above, the wide variations in Z-probe readings were also indicating to me that the probe wasn't being lifted far enough from the bed between probes.
This was introducing an additional source of error itself.

I spent a day investigating this issue, and came up with the following work-around that results in reliable bed-meshing.
When doing multiple samples I was always seeing Z-probe readings varying by no more than 0.005mm, and usually 0.0025 or 0.

With this, I knew that probing multiple times per point was no longer necessary, and we can implement the suggestion of a single probe sample.

Thus, despite each individual probe point moving a little more slowly, the fact that it only probes each point once meant that bed-meshing was taking about the same amount of time as before.


## What I changed and why

All the following configuration changes are done within the `printer.cfg` file

**NOTE** After making these changes you may need to perform a Z-offset tuning procedure to dial in your Z-offset more accurately again for best results.


### Z-stepper changes

Find the `[stepper_z]` and `[stepper_z1]` sections, and set microsteps to 16

Doing this, coupled with the changes to the `[smart_effector]` section later, ensures that the MCU more precisely catches the trigger-point of the inductive probe that is responsible for the Plus4's primary bed meshing.

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

Also find the `[tmc2209 stepper_z]` and `[tmc2209 stepper_z1]` sections, and ensure interpolate is set to False.
Setting Interpolate to False ensure a more accurate motion of the Z steppers.

Unforunately Stealthchop also introduces its own inaccuracies, but we must leave it enabled as disabling it introduces a loud resonant squealing noise from the Z-steppers through the base of the frame.

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


### Smart Effector

The `Smart Effector` config section is a Qidi-specific replacement for the traditional Klipper `probe` config section, as it mixes use of a strain sensor under the bed for nozzle offset probing, and the eddy current inductive sensor for regular bed meshing.

As such, most of the significant changes for Z-offset and bed meshing changes are done in this section on the Plus4.

By reducing the `speed`, coupled with reducing the `microsteps` in the Z-stepper sections, we allow the STM32 MCU on the Plus4 that Klipper is polling to more accurately catch the trigger point for when the build plate is detected.

By raising the `sample_retract_dist` we increase the distance that the probe lifts between multiple samples, and this allows the eddy current probe to get a better reading of the true trigger point.

Here we're also setting `samples` to 1 (the default is 2) as we've already made the required changes to catch the bed mesh trigger points more accurately.
With a sample size of 1, the `samples_tolerance` and `sample_tolerance_retries` fields effectively do nothing.
If you wish to keep `samples` at 2, or even raise it to 3, you will be able to observe the repeatability of the sample points in action.

Find the `[smart_effector]` section, and modify `speed`, `samples`, and `sample_retract_dist` fields.  Also set `samples_tolerance` to 0.013 if you plan to use more than 1 sample per point.

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

Due to the large size of the Plus4's build plate, I personally prefer more probe points, so I raised the `probe_count` from `9,9` to `11,11`, and lowered the bicubin tension from `0.4` to `0.3` as we have more probe points to deal with.

Even if you change nothing else in this section, at least change `horizontal_move_z` to 10, to ensure that the eddy current probe is sufficiently distant from the build plate prior to each sample.

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


### Z-Tilt

Normally the Z-Tilt mechanism configuration is only done once through the printer's UI screen when doing manual bed tramming.

Raising the `horizontal_move_z` distance for the `Z-tilt` section allows the inductive probe to get properly clean of the build plate for better probe point accuracy.

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
