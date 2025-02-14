# Beacon3D RevH Normal Installation and Configuration Guide

**Note 1 :** *All these configurations relate ONLY to using the Beacon in Contact mode on the Qidi Plus4 Printer*

**NOTE 2:** *Power Loss Recovery does not work correctly yet when using the Beacon probe.  I am working on a solution
for this, but for now, do not expect to be able to safely resume prints after a power loss event.*

This install guide should work for all other Beacon models, but it is untested on those.  The sample mounting
model provided is also only tested for clearances using the RevH Normal Beacon module.

## Quick Summary Guide

If you're an experienced Beacon user, or generally know what you're doing with Klipper, then you can
generally just follow the Beacon official guide here: https://docs.beacon3d.com/quickstart/
and the Beacon Contact guide here: https://docs.beacon3d.com/contact/

As a word of encouragement, during the installation process you may get multiple errors regarding the configuration having issues.
Don't worry, these can all be resolved fairly easily by carefully reading the error messages and resolving them.  It's okay.  You can do this!

***

### First backup your configuration and klipper objects

On a command shell (`ssh`) to the printer, run the following

```
mkdir -p /home/mks/qidi-klipper-backup
(cd /home/mks; tar cvf - klipper printer_data/config) | (cd /home/mks/qidi-klipper-backup; tar xf -)

```

This will backup your klipper installation and all of your printer configuration files to the `/home/mks/qidi-klipper-backup` directory for easy recovery

***

### Install the Beacon software

Follow the Beacon guide here: https://docs.beacon3d.com/quickstart/#3-install-beacon-module

_**Please ensure that you have actually run the install script as the guide suggests**_


**Note:** If you run into inssues with git when installing the Beacon software, it may be because your
printer's system time is too far out of sync.  Follow [this guide](https://wiki.qidi3d.com/en/Memo/System-Time-Modification)
to sync your printer's system time.

***

### Install the beacon unit itself

Print out my mounting model here: https://www.printables.com/model/1170120-beacon3d-mount-for-qidi-plus4

Install the mounting module along with the Beacon attached.  Route the beacon's cable to the mainboard.
The beacon appears to have **no issues** when plugged into one of the USB2 ports on the mainboard.

***

### Klipper script changes

On your printer, edit the `/home/mks/klipper/klippy/extras/probe.py` file and comment out the lines as highlighted here:

[probe.py lines to comment out](./probe.py#L485-L492)

Then save the file, and then power-cycle your printer.  This disables the Z-vibrate functionality that is incompatible with Beacon.

***

### printer.cfg changes

- First, on an ssh command shell to the printer, run `ls /dev/serial/by-id/usb-Beacon*` to find your Beacon serial number

It should look something like the following:

![image](https://github.com/user-attachments/assets/499294c2-c79c-42da-b4df-15d46b4d3011)



Now edit your `printer.cfg` file.  

- In `[stepper_z]` check that `endstop_pin:` is set to `probe:z_virtual_endstop`.  It should already be so on the Plus4

- In `[stepper_z]`  ensure that the `position_endstop` line is commented out

- Set `homing_retract_dist` to 0 on all of your steppers

- Comment out the `[smart_effector]`, and `[qdprobe]` sections in `printer.cfg` in their entirety.

- Also comment out `[safe_z_home]` IF it appears in your `printer.cfg` file.  It does not on stock Plus4 configs, but other mods may have added it.

- Ensure `[force_move]` remains uncommented.  Various Plus4 UI moves, platform reset, and power loss recovery, need it.  We'll fix up any unnecessary calls to `SET_KINEMATIC_POSITION` later.

- Replace the `[z_tilt]` and `[bed_mesh]` sections with the following sections below:

```
[z_tilt]
z_positions:
    -17.5,152
    335.7,152

points:
    50, 170.8           # Assumes using stew675 beacon mount's offsets
    255, 170.8          # Assumes using stew675 beacon mount's offsets

speed: 200
horizontal_move_z: 5
retries: 5
retry_tolerance: 0.006

[bed_mesh]
speed:150
horizontal_move_z:2
zero_reference_position: 152, 152
mesh_min:15,15
mesh_max:295,283
probe_count:14,14
algorithm:bicubic
bicubic_tension:0.3
mesh_pps: 2,2
fade_start: 2
fade_end: 10
fade_target: 0
```

- Add the following `[beacon]` section:

```
[beacon]
serial: /dev/serial/by-id/usb-Beacon_Beacon_RevH_<**INSERT-YOUR-BEACON-SERIAL-HERE**>
x_offset: 0                     # Assumes using stew675 beacon mount's offsets
y_offset: -18.8                 # Assumes using stew675 beacon mount's offsets
mesh_main_direction: x
mesh_runs: 2
contact_max_hotend_temperature: 270  # 180
home_xy_position: 152, 152      # update with your safe Z home position
home_z_hop: 5
home_z_hop_speed: 30
home_xy_move_speed: 300
home_y_before_x: False
home_method: proximity
home_method_when_homed: proximity
home_autocalibrate: never
home_gcode_pre_x: _BEACON_HOME_PRE_X
home_gcode_post_x: _BEACON_HOME_POST_X
home_gcode_pre_y: _BEACON_HOME_PRE_Y
home_gcode_post_y: _BEACON_HOME_POST_Y
contact_activate_gcode: _BEACON_CONTACT_PRE_Z
contact_deactivate_gcode: _BEACON_CONTACT_POST_Z
autocal_tolerance: 0.006
```

When in doubt, check out the copy of my full [printer.cfg](./printer.cfg) for reference.

***

### gcode_macros.cfg changes

**NOTE**: *If you were following this guide before 11th Feb 2025, then most of the following content
has changed significantly and it is best to re-follow this guide carefully and copy and replace all
of the macros again from this guide.  Also pay particular attention to the line of gcode added to
the `[PRINT_START]` macro. *

There are a lot of changes here.  Take your time and you'll be fine.  When in doubt, check out the copy of my full [gcode_macro.cfg](./gcode_macro.cfg) for reference.

Edit `gcode_macro.cfg`

- Add the following `[_APPLY_NOZZLE_OFFSET]` and `[APPLY_FILAMENT_OFFSET]` sections to your file.

```
[gcode_macro _APPLY_NOZZLE_OFFSET]
description: Determine the global nozzle offset and apply
variable_z_homing_temperature: 150      # Temperature that we home the nozzle at to determine Z=0
variable_reference_position: 5.0        # A safe Z position at which we'll apply the offset change
variable_expansion_factor: 0.00045      # Amount hotend lengthens by per 1C temperature rise, within ±3%
variable_contact_compensation: 0.06     # Static Offset to compensate for Beacon contact latency
                                        # 0.05 to 0.07 appears to be typical for the Plus 4
variable_hotend_temp: 250               # Target hotend temp (typically set by PRINT_START)
gcode:
    # Set our working variables.  We treat everything as floats for these calculations
    {% set z_home_temp = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].z_homing_temperature)|float %}
    {% set z_home_x = printer.configfile.settings.beacon.home_xy_position[0] %}
	{% set z_home_y = printer.configfile.settings.beacon.home_xy_position[1] %}
    {% set z_speed = (printer.configfile.settings['stepper_z'].homing_speed)|float * 60 %}
	{% set z_hop = (printer.configfile.settings['beacon'].home_z_hop)|float %}
    {% set reference_position = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].reference_position)|float %}
    {% set expansion_factor = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].expansion_factor)|float %}
    {% set contact_comp = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].contact_compensation)|float %}
    {% set hotend_temp = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].hotend_temp)|float %}

    # Calculate Offset and sanity check it so we don't end up etching the build plate
    {% set temperature_offset = ((hotend_temp - z_home_temp) * expansion_factor)|float %}
    {% if temperature_offset < 0 %}
        {% set temperature_offset = 0|float %}
    {% endif %}

    # Determine the Z target position
    {% set target_position = (reference_position + contact_comp + temperature_offset)|float %}

    # Report to the console what we've determined
    { action_respond_info("Applying Z offset adjustment for hotend temperature of %.1f°C" % hotend_temp|float) }
    { action_respond_info("  Expansion Coefficient = %.6f" % (expansion_factor)|float) }
    { action_respond_info("  Temperature Offset    = %.6f" % (temperature_offset)|float) }
    { action_respond_info("  Contact Compensation  = %.3f" % (contact_comp)|float) }
    { action_respond_info("  Total Offset          = %.6f" % (temperature_offset + contact_comp)|float) }
    { action_respond_info("  Reference Position    = %.1f" % (reference_position)|float) }
    { action_respond_info("  Target Position       = %.6f" % (target_position)|float) }

    SET_GCODE_OFFSET Z=0                            # Clear any pre-existing Gcode offsets
    G1 Z{target_position} F{z_speed}                # Move Z to determined target position
    G1 X{z_home_x} Y{z_home_y} F7200                # Move X/Y to Z homing position 
    M400                                            # Wait for prior gcode-commands to finish
    SET_KINEMATIC_POSITION Z={reference_position}   # Set target position to be the reference position
    G1 Z{reference_position} F600                   # Move Z to reference position.  Ideally the bed should not move
    M400

[gcode_macro _FIND_Z_EQUALS_ZERO]
gcode:
    {% set z_home_temp = printer["gcode_macro _APPLY_NOZZLE_OFFSET"].z_homing_temperature|int %}
    {% set z_home_x = printer.configfile.settings.beacon.home_xy_position[0] %}
	{% set z_home_y = printer.configfile.settings.beacon.home_xy_position[1] %}

    # Turn off all fans to minimise sources of vibration and clear any old state
    M109 S{z_home_temp}                     # Commence nozzle warmup for z homing        
    BED_MESH_CLEAR                          # Clear out any existing bed meshing context
    SET_KINEMATIC_POSITION Z=0              # Force firmware to believe Z is homed at 0
    G1 Z3 F600                              # Move bed away from the nozzle by 3mm from where it was
    SET_KINEMATIC_POSITION CLEAR=XYZ        # Clear all kinematic repositionings
    SET_GCODE_OFFSET Z=0                    # Comnpletely reset all prior notions of Z offset
    G28 X Y                                 # Home X and Y Axes
    G28 Z METHOD=CONTACT CALIBRATE=1        # Home Z axis, and calibrate beacon                                               
    Z_TILT_ADJUST                           # Ensure bed is level
    G1 X{z_home_x} Y{z_home_y} F7200        # Move to Z home position
    G4 P30000                               # Heatsoak hotend for 30s more
    G28 Z METHOD=CONTACT CALIBRATE=0        # Establish Z=0
    G1 Z3 F600                              # Move bed away from the nozzle by 3mm from where it was

[gcode_macro APPLY_FILAMENT_OFFSET]
description: Apply a Z offset adjustment for a specific filament
gcode:
    {% set filament_z = params.Z|default(0)|float %}
    { action_respond_info("Setting Filament Offset to %.3fmm" % (filament_z)) }
    SET_GCODE_OFFSET Z_ADJUST={filament_z} MOVE=1 SPEED=3
```

- Replace the `[zoffset]`, `[test_zoffset]`, `[get_zoffset]`, `[save_zoffset]`, and `[set_zoffset]` sections with these sections:

```
# All the following zoffset calls only exist to keep Qidi's xindi happy
[gcode_macro zoffset]
description: Apply baseline Z offset which is always zero for Beacon Contact
gcode:
    SET_GCODE_OFFSET Z=0 MOVE=1             # Apply a zero gcode_offset

# Development test
[gcode_macro test_zoffset]
description: Debugging test to compare the probe contact and proximity Z Offset values
gcode:
    G28 X Y
    get_zoffset
    M400
    BEACON_OFFSET_COMPARE
    G4 P5000
    G1 Z10 F600

[gcode_macro get_zoffset]
description: Homes nozzle against build plate and applies global z offset
gcode:
    _FIND_Z_EQUALS_ZERO
    _APPLY_NOZZLE_OFFSET

[gcode_macro save_zoffset]
description: Use APPLY_FILAMENT_OFFSET instead
gcode:
    { action_respond_info("Use APPLY_FILAMENT_OFFSET instead") }

[gcode_macro set_zoffset]
description: Apply baseline Z offset which is always zero for Beacon Contact      
gcode: 
    SET_GCODE_OFFSET Z=0 MOVE=1             # Apply a zero gcode_offset
```

- In the `[PRINT_START]` macro, towards the top of the macro, add this line:

```
    SET_GCODE_VARIABLE MACRO=_APPLY_NOZZLE_OFFSET VARIABLE=hotend_temp VALUE={hotendtemp}
```

immediately after these three lines:
```
    {% set bedtemp = params.BED|int %}
    {% set hotendtemp = params.HOTEND|int %}
    {% set chambertemp = params.CHAMBER|default(0)|int %}
```

For example, the starting area of `[PRINT_START]` should look something like this:
```
    {% set bedtemp = params.BED|int %}
    {% set hotendtemp = params.HOTEND|int %}
    {% set chambertemp = params.CHAMBER|default(0)|int %}
    SET_GCODE_VARIABLE MACRO=_APPLY_NOZZLE_OFFSET VARIABLE=hotend_temp VALUE={hotendtemp}
```

**The above is important, as it enables the automatic Z offset management mechanism to function correctly.**

- Ensure that these 3 lines are commented out in your `PRINT_END` macro

```
[gcode_macro PRINT_END]
gcode:
#    {% if printer.gcode_move.homing_origin.z < 0.5 %}
#       SAVE_VARIABLE VARIABLE=z_offset VALUE={printer.gcode_move.homing_origin.z}
#    {% endif %}
```

- Comment out, or delete, the call to `save_zoffset` in the `[CANCEL_PRINT]` macro
 
- Comment out, or delete, the `[homing_override]` section in its entirety

- Comment out, or delete, the gcode in the `Z_VIBRATE` macro like so

```
#[gcode_macro Z_VIBRATE]
#gcode:
#   Commented out for use of Beacon Contact
#    m204 S400
#    G90
#    G0 Z4
#    G91
#    G4 P3000
#    SET_PIN PIN=ctlyd VALUE=1 
#    {% for z in range(1,50) %}
#        G1 Z1 F1200
#        G4 P50
#        G1 Z-1 F1200
#        G4 P50
#    {% endfor %}
#    M204 S100
#    SET_PIN PIN=ctlyd VALUE=0
#    G4 P1000
#    G1 Z4
#    G90
```

- Modify the `M4027` macro in its entirety to look like this.  This does the Bed Meshing in a Beacon appropriate manner:

```
[gcode_macro M4027]
gcode:
    { action_respond_info("M4027 called")  }
    G32                                     # Set bed meshing to default profile
    G29                                     # Do full homing, z-tilt, and bed meshing
    G31                                     # Set bed meshing back to kamp profile
    M400                                    # Wait for all outstanding G-code moves to finish
    M118 Bed mesh calibrate complete        # Tell xindi we're done
    SAVE_CONFIG
```

- Replace your `G29` macro with this version here:

```
[gcode_macro G29]
variable_k:1
description: Prepare print bed, generate a bed mesh, and apply global Z nozzle offset
gcode:
    _FIND_Z_EQUALS_ZERO
    {% if k|int==1 %}
        BED_MESH_CALIBRATE RUNS=2 USE_CONTACT_AREA=1 PROFILE=kamp
        BED_MESH_PROFILE LOAD=kamp
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"kamp"'
    {% else %}
        BED_MESH_CALIBRATE RUNS=2 USE_CONTACT_AREA=1 PROFILE=default
        BED_MESH_PROFILE LOAD=default
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"default"'
    {% endif %}
    _APPLY_NOZZLE_OFFSET
```

- Add these 6 macros to the end of your file:

```
[gcode_macro _BEACON_HOME_PRE_X]
gcode:
    {% set RUN_CURRENT = printer.configfile.settings['tmc2240 stepper_x'].run_current|float %}
    SET_TMC_CURRENT STEPPER=stepper_x CURRENT={RUN_CURRENT * 0.6}

[gcode_macro _BEACON_HOME_POST_X]
gcode:
    {% set RUN_CURRENT = printer.configfile.settings['tmc2240 stepper_x'].run_current|float %}
    # Move away
    G1 X20 F9000
    M400
    SET_TMC_CURRENT STEPPER=stepper_x CURRENT={RUN_CURRENT}

[gcode_macro _BEACON_HOME_PRE_Y]
gcode:
    {% set RUN_CURRENT = printer.configfile.settings['tmc2240 stepper_y'].run_current|float %}
    SET_TMC_CURRENT STEPPER=stepper_y CURRENT={RUN_CURRENT * 0.8}       

[gcode_macro _BEACON_HOME_POST_Y]
gcode:
    {% set RUN_CURRENT = printer.configfile.settings['tmc2240 stepper_y'].run_current|float %}
    # Move away
    G1 Y20 F9000
    M400
    SET_TMC_CURRENT STEPPER=stepper_y CURRENT={RUN_CURRENT}

[gcode_macro _BEACON_CONTACT_PRE_Z]
gcode:

[gcode_macro _BEACON_CONTACT_POST_Z]
gcode:
    G1 Z3 F600              # Ensure the bed is moved away from the nozzle
    M400
```

## Calibration of your new Beacon

With all the above changes in place (and the firmware restarted) your Beacon can now be easily
calibrated with the following typed into the Gcode Console:

```
G32
G29
G31
SAVE_CONFIG
```

This will set the Plus4 to generate a `default` bed mesh (`G32`), then do a full calibration home
and bed mesh (`G29`), and then finally put the Plus4 back into Kamp mode meshing ready for the
next print (`G31`).  The whole lot gets saved afterwards (`SAVE_CONFIG`)

***

## APPLY_FILAMENT_OFFSET - What it does and how to use it

**NOTE**: *If you have applied filament offsets from using this guide before 11th Feb 2025, then these
may need to all be commented out, as the automated filament offset system should largely make doing
filament specific offsets unnecessary.*

The idea behind `APPLY_FILAMENT_OFFSET` is to do away with the fiddling about with the global Z offset
when changing to filaments that prefer a different Z offset to the replaced filament.  By and large the
automated filament nozzle temperature management system should set the correct offset for almost all
filaments, however there may still be a handful of standout filaments that need tweaking.

With the original method, if the first layer wasn't going down properly, we would have to adjust the global Z
offset, and save it, and then that could cause issues later when changing filaments.

`APPLY_FILAMENT_OFFSET` is designed to be used within the filament material settings within your slicer.

By default, the filament offset is set to 0 whenever a new print starts.  If the first layer offset
needs to be adjusted, then that can be done the usual way on the printer's screen UI by adjusting the
Z offset up/down as required.  This is best done with a 1 layer sheet of 100x100mm, and using the screen
to apply Z offset adjustments until the first layer sheet is printing well.

When you are happy with the Z offset adjustment, take note of the offset that is displayed, and we can
apply that to our filament settings.

For example, let's say that we were printing our test sheet and saw best results with an offset of 0.02mm

We edit the filament start G-code and end G-codes like so:

![image](https://github.com/user-attachments/assets/b7b3281e-6a2d-402a-a1da-a64a2215860e)

and save the filament settings.  Note that we are reversing the sign of the filament offset in the Filament
end G-code section.  This allows for filaments with different preferred offsets to be swapped mid-print.
This should be especially useful when the QidiBox is released.

The next time that we print with this filament, the filament specific Z offset will be applied and we should
get perfect first layers with it moving forwards.

***

## Optional QoL Bed Tramming Macros

**NOTE**: *If you were using bed tramming by folllowing this guide before 11th Feb 2025, then those macros
will need to be replaced with the following macros as they handle bed tramming more accurately*

Are you tired of tramming the bed using the old paper and nozzle drag test?  The Beacon Probe knows precisely
when the nozzle is touching the print bed, so let it do that job for you!  It'll do it more accurately than you
can by dragging a piece of paper under the nozzle.

This makes the task of tramming the bed using the 4 knobs under the print bed a lot easier.

Add the following macros to the end of your `gcode_macro.cfg` file:

```
[gcode_macro SCREW_ADJUST_START]
gcode:
    _FIND_Z_EQUALS_ZERO

[gcode_macro SCREW_ADJUST_END]
gcode:
    G1 Z3 F600              # Move print bed away from nozzle
    M104 S0                 # Turn off hotend
    M400

[gcode_macro SFL]
description: Get zoffset at front-left bed adjustment screw position
gcode:
    {% set screw_pos_x = printer.configfile.settings.bed_screws.screw1[0] %}
    {% set screw_pos_y = printer.configfile.settings.bed_screws.screw1[1] %}
    {% set beacon_off_x = printer.configfile.settings.beacon.x_offset %}
    {% set beacon_off_y = printer.configfile.settings.beacon.y_offset %}
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle
    G1 X{screw_pos_x - beacon_off_x + 20} Y{screw_pos_y - beacon_off_y + 20} F6000
    PROBE PROBE_METHOD=proximity

[gcode_macro SFR]
description: Get zoffset at front-right bed adjustment screw position
gcode:
    {% set screw_pos_x = printer.configfile.settings.bed_screws.screw2[0] %}
    {% set screw_pos_y = printer.configfile.settings.bed_screws.screw2[1] %}
    {% set beacon_off_x = printer.configfile.settings.beacon.x_offset %}
    {% set beacon_off_y = printer.configfile.settings.beacon.y_offset %}
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle
    G1 X{screw_pos_x - beacon_off_x - 20} Y{screw_pos_y - beacon_off_y + 20} F6000
    PROBE PROBE_METHOD=proximity

[gcode_macro SBL]
description: Get zoffset at back-left bed adjustment screw position
gcode:
    {% set screw_pos_x = printer.configfile.settings.bed_screws.screw3[0] %}
    {% set screw_pos_y = printer.configfile.settings.bed_screws.screw3[1] %}
    {% set beacon_off_x = printer.configfile.settings.beacon.x_offset %}
    {% set beacon_off_y = printer.configfile.settings.beacon.y_offset %}
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle
    G1 X{screw_pos_x - beacon_off_x + 20} Y{screw_pos_y - beacon_off_y - 20} F6000
    PROBE PROBE_METHOD=proximity

[gcode_macro SBR]
description: Get zoffset at back-right bed adjustment screw position
gcode:
    {% set screw_pos_x = printer.configfile.settings.bed_screws.screw4[0] %}
    {% set screw_pos_y = printer.configfile.settings.bed_screws.screw4[1] %}
    {% set beacon_off_x = printer.configfile.settings.beacon.x_offset %}
    {% set beacon_off_y = printer.configfile.settings.beacon.y_offset %}
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle
    G1 X{screw_pos_x - beacon_off_x - 20} Y{screw_pos_y - beacon_off_y - 20} F6000
    PROBE PROBE_METHOD=proximity
```

Each of the macros above will position the probe above the knobs so you can adjust and re-measure quickly

To use these macros, first heat your print bed to your typical printing temperature.
When the print bed's temperature has stabilised, call `SCREW_ADJUST_START` from the console.
This re-homes the axes and re-confirms where the nozzle touches the build plate, and leaves the hotend
on at the contact probing temperature.

Now call the `SFL`, `SFR`, `SBL`, and `SBR` macro listed above and look at the last line of the output

For example: `// Result is z=0.038333`

This informs you of the Z offset of the print bed at each screw location relative to the Z=0 homing
position at the center of the print bed.  You can now adjust the knob under the bed
and call the same macro again to obtain the new offset.  The goal is to get within 0.02mm of Z=0
This can be repeated for each of the 4 screw points until all are equal within -0.02 to +0.02mm
Better accuracy than this may be difficult to achieve due to backlash in the Z-axis lead screws.

When done, call the `SCREW_ADJUST_END` macro to disable the hotend


## Beacon and KAMP Line Purge

If you are using the KAMP Line Purging, you may notice that some parts of the Beacon will catch onto
the purged line.  If this is affecting you, then here's a solution.  This places the purge line
towards the back-right of the print area where the Beacon module is unlikely to catch on any part of it.

[KAMP_Settings.cfg](./KAMP_Settings.cfg)

[KAMP/Line_Purge.cfg](./Line_Purge.cfg)

Replace the contents of the `KAMP_Settings.cfg` file that lives __*in the same directory*__ as your
`printer.cfg` file with the contents of the [KAMP_Settings.cfg](./KAMP_Settings.cfg) file.

**NOTE**: Do not edit the `KAMP_Settings.cfg` file that is in the `KAMP` sub-directory as it is
unused by the Plus4.

Also, replace the contents of the `Line_Purge.cfg` file which is in the `KAMP` sub-directory
with the contents of the [KAMP/Line_Purge.cfg](./Line_Purge.cfg) file.

Now Save and Restart.


# FAQ


## I've configured everything using the guide, but my first layers still aren't perfect (but they are close)

This may be due to differences in the `expansion_factor` from my setup, to yours.  In the `_APPLY_NOZZLE_OFFSET` macro
we can find the `variable_expansion_factor` value.  A value of `0.00099` works perfectly on my system, but due to
manufacturing variances, your particular hotend may behave differently to mine.

This can be addressed by calibrating this value for your setup.

1. Print out a single layer 100x100mm square using some PLA+ at 230C.
2. If the nozzle is too high, subtract 0.00003 from the expansion factor, then save and restart. eg. 0.00099 would become 0.00096
3. Repeat steps 1 and 2 until the first layer looks good.
4. We do the reverse if you first layer is too low.  Increase the expansion factor by 0.00003 each time until it looks good
5. You can fine tune using 0.00001 steps, but generally these steps are so small that inherent inaccuracies in the eddy current based bed meshing tend to dominate
6. If your expansion factor is getting below 0.00075, or above 0.00125, then stop.  Something else is likely wrong and seek help.


##  I've calibrated my `expansion_factor` and it's good, but there's still some spots on the bed that are never perfect

Unfortunately Eddy Current bed meshing, while very good, isn't a perfect science.  The Beacon detects eddy currents in the
metal of the build plate.  Variations in the thickness of a PEI, or other, coating atop the metal plate cannot be accounted
for by eddy current probing.  The best we can do here is get it close enough, and trust that the 2nd and 3rd layers will
cover over any small inconsistencies.  The other tactic is to switch build plates if your build plate's coating is
particularly inconsistent.


## My first layers are pretty good most of the time, but sometimes it can be a little inconsistent

In this case, your bed meshing speed may be too high.  The higher the speed you generate a mesh at, the less accurate the
eddy current sensing becomes.

Inside the `[bed_mesh]` section in your `printer.cfg` file, find the `speed` field and drop it back to `150` or even `100`
and see if that helps.  If that doesn't resolve issues then reach out to the Beacon discord for assistance.


## Bed Z homing is slow!  Can it be faster?

Yes, it can, but there is a risk of a nozzle crash if you change print bed sheets to something wildly different to what was
there before.  The current configuration is deliberately conservative and safe to try to avoid nozzle crashes.

While the chance of a nozzle crashe is generally very, very small, it is not zero.  If you accept the risk, you can enable faster
homing by changing the `[beacon]` config in your `printer.cfg` like so:

```
[beacon]
...
home_method: proximity
home_method_when_homed: proximity
home_autocalibrate: never
...
```

This will enable the much faster proximity based homing for all regular homing operations.
The `G29` macro will still do contact based homing to accurately determine the nozzle offset, and bed mesh, but otherwise
all other Z homing operations should be relatively quick.

Only make this change if you're okay with the risk that the nozzle may crash into the build plate if you do something
weird and forget to recalibrate your Beacon's proximity models.  See: https://docs.beacon3d.com/quickstart/#6-calibrate-beacon



## Where can I go for further assistance with issues?

You can reach out to me, `stew675` on the [Qidi Official Discord](https://discord.gg/B6jDttWUE6) in the Plus 4 channel

Alternately you can reach out to the [Official Beacon Discord Channel](https://discord.gg/MzTR3zE) and ask for help there
