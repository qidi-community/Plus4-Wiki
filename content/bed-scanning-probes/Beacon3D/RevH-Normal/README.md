# Beacon3D RevH Normal Installation and Configuration Guide

This install guide should work for all other Beacon models, but it is untested on those.  The sample mounting
model provided is also only tested for clearances using the RevH Normal Beacon module.

**Last Updated:** _3PM US CST 19th July 2025_

***

**NOTE 1 :**

*All these configurations relate ONLY to using the Beacon in Contact mode on the Qidi Plus4 Printer*

***

**NOTE 2:**

*Power Loss Recovery does not work correctly yet when using the Beacon probe.  I am working on a solution
for this, but for now, do not expect to be able to safely resume prints after a power loss event.*

***

**NOTE 3:**

*This guide is primarly intended for use with the stock Qidi configs, or a lightly modified version of
them, and also be actively using the `KAMP/Line_Purge.cfg` and `KAMP/Adapative_Meshing.cfg` macros.  If you are
trying to call native Klipper `BED_MESH_CALIBRATE ADAPTIVE=1...` instead of using the `KAMP/Adapative_Meshing.cfg`
macro then there is a chance where the wrong bed mesh will be loaded.*

***

**NOTE 4 (QIDIBOX):**

I can confirm that the **QIDIBOX** 1.7 firmware update **DOES NOT**  break anything firmware wise for Beacon.  Beacon still works (and Klippain 5.1.1 also still works for those using that).

The 1.7 firmware update for Qidibox WILL over-write your pre-existing `printer.cfg` and `gcode_macro.cfg` config files though, so be sure to make backups of your old config files.  You
should not rely upon Qidi's firmware update scipts automatically making backup copies of your config during a firmware upgrade.

What you need to do here is to just redo the following Beacon configuration guide and manually patch the config files.  Afterwards you should be up and running again.

For those of you who just copy and pasted my original example configs, you will need to do that configuration manually until such time that I update those sample configs.

*DO NOT copy and paste the my sample configuration files if you have QIDIBOX installed until such time as I update them.   In the meantime, use the examples from the guide only*

***

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

You have two choices:

1. Run the following commands to install the Beacon3D software:

```
cd /home/mks
git clone https://github.com/beacon3d/beacon_klipper.git
./beacon_klipper/install.sh

```

-OR-

2. Follow Beacon3D's own guide here: https://docs.beacon3d.com/quickstart/#3-install-beacon-module

   _**Please ensure that you have actually run the install script as the guide suggests**_


**Note:** If you run into inssues with git when installing the Beacon software, it may be because your
printer's system time is too far out of sync.  Follow [this guide](https://wiki.qidi3d.com/en/Memo/System-Time-Modification)
to sync your printer's system time.

**Note 2:** Make sure that your printer can connect to the internet.  If it is in LAN-Only mode, then
you may need to take it out of LAN-mode for this step.  Alternately you can also download the Beacon
software to a USB stick and transfer it to your printer that way, but I leave this as an exercise for
the reader if you choose that path.

***

### Install the beacon unit itself

Print out my mounting model here: https://www.printables.com/model/1170120-beacon3d-mount-for-qidi-plus4

Install the mounting module along with the Beacon attached.  Route the beacon's cable to the mainboard.

It has been reported by some users that using the USB3 port (which is the upper of the 3 USB-A connectors on the left of the mainboard can cause intermittent errors and problems with the Beacon.

The Beacon module appears to have **no issues** when plugged into one of the USB2 ports (being the lower two) on the mainboard,

***

### Klipper script changes

First we need to remove the `Z-Vibrate` functionality from `/home/mks/klipper/klippy/extras/probe.py` as this
is incompatible with beacon.

There are two options for how this can be done.

1.  Run the following command which overwrites the file with a version that already has the problematic lines commented out.

```
wget -O /home/mks/klipper/klippy/extras/probe.py https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/bed-scanning-probes/Beacon3D/RevH-Normal/probe.py

```

-OR-  (if you wish to do it manually for more personal control)

2. On your printer, edit the `/home/mks/klipper/klippy/extras/probe.py` file, then find and comment out the lines as highlighted here:

[probe.py lines to comment out](./probe.py#L485-L492)

Then save the file and exit the editor.


After either option is complete, then power-cycle your printer.

**VERY IMPORTANT NOTE** - Power-cycle means to turn your printer off at the power switch, wait 10s, and then turn it back on.

It does **NOT** mean just save and restart.  That will not perform the necessary Klipper firmware rebuilding that
happens with a power cycle.


***

### printer.cfg changes

- First, on an ssh command shell to the printer, run `ls /dev/serial/by-id/usb-Beacon*` to find your Beacon serial number

It should look something like the following:

![image](https://github.com/user-attachments/assets/499294c2-c79c-42da-b4df-15d46b4d3011)



Now edit your `printer.cfg` file.  

- In `[stepper_z]` check that `endstop_pin:` is set to `probe:z_virtual_endstop`.  It should already be so on the Plus4

- Commenting out lines in G-code is done by putting the `#` symbol at the start of the line.  Everything after the `#` symbol is ignored by the printer firmware

- In `[stepper_z]`  ensure that the `position_endstop` line is commented out

- Set `homing_retract_dist` to 0 on all of your steppers

- Comment out the `[smart_effector]`, and `[qdprobe]` sections in `printer.cfg` in their entirety.

- Also comment out `[safe_z_home]` IF it appears in your `printer.cfg` file.  It does not on stock Plus4 configs, but other mods may have added it.

- Ensure `[force_move]` remains uncommented.  Various Plus4 UI moves, platform reset, and power loss recovery, need it.  We'll fix up any unnecessary calls to `SET_KINEMATIC_POSITION` later.

- Replace the `[z_tilt]` and `[bed_mesh]` sections with the following sections below:

```
[z_tilt]
z_positions:
    -17.5,152.5
    335.7,152.5

points:
    40, 171.3           # Assumes we are using the stew675 beacon mount offsets of X=0, Y=-18.8
    265, 171.3          # Assumes we are using the stew675 beacon mount offsets of X=0, Y=-18.8

speed: 200
horizontal_move_z: 5
retries: 5
retry_tolerance: 0.006

[bed_mesh]
speed: 150
horizontal_move_z: 2
zero_reference_position: 152.5, 152.5
mesh_min: 22,22
mesh_max: 283,283
probe_count: 14,14
algorithm:bicubic
bicubic_tension: 0.3
mesh_pps: 2,2
fade_start: 2
fade_end: 10
fade_target: 0
split_delta_z: 0.01
move_check_distance: 4
```

- Add the following `[beacon]` section:

Using the serial number you had captured before, put that in the serial section here.

It's been reported that there appears to be a bug in some versions of the Beacon
firmware that causes `contact_activate_gcode` and `contact_deactivate_gcode` to
fail.  As such, I have commented out those lines in the config here.

Once your install is complete and if everything is verified to be working, then
you may try uncommenting those lines to see if everything still works.  The
deactivate macro performs a movement to move the print head away from the print
bed as an additional safety measure, but it is not essential for normal operation.

```
[beacon]
serial: /dev/serial/by-id/usb-Beacon_Beacon_RevH_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX-if00      # Replaces the X's with your unit's serial number
# serial: /dev/serial/by-id/usb-Beacon_Beacon_RevH_0123456789ABCDEF0123456789ABCDEF-if00    # Example only, DO NOT uncomment this line
x_offset: 0                     # Assumes using stew675 beacon mount's offsets
y_offset: -18.8                 # Assumes using stew675 beacon mount's offsets
mesh_main_direction: x
mesh_runs: 2
contact_max_hotend_temperature: 270  # 180
home_xy_position: 152.5, 152.5      # update with your safe Z home position
home_z_hop: 5
home_z_hop_speed: 30
home_xy_move_speed: 300
home_y_before_x: True
home_method: proximity
home_method_when_homed: proximity
home_autocalibrate: never
home_gcode_pre_x: _BEACON_HOME_PRE_X
home_gcode_post_x: _BEACON_HOME_POST_X
home_gcode_pre_y: _BEACON_HOME_PRE_Y
home_gcode_post_y: _BEACON_HOME_POST_Y
#contact_activate_gcode: _BEACON_CONTACT_PRE_Z         
#contact_deactivate_gcode: _BEACON_CONTACT_POST_Z
contact_sensitivity: 1          # You can try the default of 0, but if your
                                # automatic Z is too high, then put back to 1
contact_latency_min: 2          # You can try the default of 0, but if your
                                # automatic Z is high, put back to 2, 3 or 4
autocal_tolerance: 0.006
```

When in doubt, check out the copy of my full [printer.cfg](./printer.cfg) for reference.

***

### gcode_macros.cfg changes

**NOTE**: *If you were following this guide before 14th Feb 2025, then most of the following content
has changed significantly and it is best to re-follow this guide carefully and copy and replace all
of the macros again from this guide.  Also pay particular attention to the line of gcode added to
the `[PRINT_START]` macro. *

There are a lot of changes here.  Take your time and you'll be fine.  When in doubt, check out the copy of my full [gcode_macro.cfg](./gcode_macro.cfg) for reference.

Edit `gcode_macro.cfg`

- Add the following `[_APPLY_NOZZLE_OFFSET]`, `[_SETTLE_PRINT_BED]`, `[_FIND_Z_EQUALS_ZERO]`, and `[APPLY_FILAMENT_OFFSET]` sections to your file.

```
[gcode_macro _APPLY_NOZZLE_OFFSET]
description: Determine the global nozzle offset and apply
variable_hotend_temp: 250               # Target hotend temp (typically set by PRINT_START)
variable_probe_temp_delta: 75           # We probe at this amount less than the hotend temp
variable_reference_position: 5.0        # A safe Z position at which we'll apply the offset change
variable_offset_correction: 0.07        # Static Offset Correction
gcode:
    # Set our local working variables.  We treat everything as floats for these calculations
    {% set reference_position = reference_position|float %}
    {% set offset_correction  = offset_correction|float %}

    # Determine the rest of our working variables
    {% set z_home_x = printer.configfile.settings.beacon.home_xy_position[0] %}
    {% set z_home_y = printer.configfile.settings.beacon.home_xy_position[1] %}
    {% set z_speed  = printer.configfile.settings['stepper_z'].homing_speed|float * 60 %}
    
    {% set target_position = (reference_position + offset_correction)|float %}

    # Report to the console what we've determined
    { action_respond_info("Applying Z offset adjustment for hotend temperature of %.1f°C" % hotend_temp|float) }
    { action_respond_info("  Offset Correction    = %.3f" % (offset_correction)|float) }
    { action_respond_info("  Reference Position   = %.1f" % (reference_position)|float) }
    { action_respond_info("  Target Position      = %.6f" % (target_position)|float) }

    SET_GCODE_OFFSET Z=0                            # Clear any pre-existing Gcode offsets
    G1 Z{target_position} F{z_speed}                # Move Z to determined target position
    G1 X{z_home_x} Y{z_home_y} F7200                # Move X/Y to Z homing position 
    M400                                            # Wait for prior gcode-commands to finish
    SET_KINEMATIC_POSITION Z={reference_position}   # Set target position to be the reference position
    G1 Z{reference_position} F600                   # Move Z to reference position.  Ideally the bed should not move
    M400

[gcode_macro _SETTLE_PRINT_BED]
gcode:
    G1 Z4 F600                              # Move to Z=4
    G91                                     # Enter relative positioning mode
    M400                                    # Wait for all prior commands to finish
    {% for z in range(50) %}                # Loop 50 times
        G1 Z1 F5000                         # Move bed down by 1mm
        G1 Z-1 F5000                        # Move bed up by 1mm
    {% endfor %}
    G90                                     # Go back to absolute positioning mode
    M400                                    # Wait for all prior commands to finish
    G1 Z4 F600                              # Make sure Z=4mm before we leave the macro

[gcode_macro _FIND_Z_EQUALS_ZERO]
gcode:
    {% set hotend_temp = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].hotend_temp)|float %}
    {% set probe_temp_delta = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].probe_temp_delta)|float %}

    {% set z_home_temp = hotend_temp - probe_temp_delta %}
    {% set z_home_x = printer.configfile.settings.beacon.home_xy_position[0] %}
    {% set z_home_y = printer.configfile.settings.beacon.home_xy_position[1] %}

    M104 S{z_home_temp}                     # Commence nozzle warmup for z homing        
    BED_MESH_CLEAR                          # Clear out any existing bed meshing context
    SET_KINEMATIC_POSITION Z=0              # Force firmware to believe Z is homed at 0
    G1 Z3 F600                              # Move bed away from the nozzle by 3mm from where it was
    SET_KINEMATIC_POSITION CLEAR=XYZ        # Ensure all kinematic repositionings are cleared
    SET_GCODE_OFFSET Z=0                    # Comnpletely reset all prior notions of Z offset
    G28 X Y                                 # Home X and Y Axes
    {% if (printer.configfile.settings['beacon model default'] is defined) %}
        G28 Z METHOD=proximity              # Do a rapid proximity based Z home if possible
    {% else %}
        M109 S{z_home_temp}                 # Wait for nozzle to fully heat up
        G28 Z METHOD=CONTACT CALIBRATE=0    # Home Z axis without calibration
    {% endif %}
    _SETTLE_PRINT_BED                        # Try to settle the build plate
    M109 S{z_home_temp}                     # Wait for nozzle to fully reach Z probing temperature
    G28 Z METHOD=CONTACT CALIBRATE=1        # Home Z axis, and calibrate beacon                                     
    Z_TILT_ADJUST                           # Ensure bed is level
    G1 X{z_home_x} Y{z_home_y} F7200        # Move to Z home position
    G4 P15000                               # Heatsoak hotend for 15s more
    G28 Z METHOD=CONTACT CALIBRATE=1        # Establish Z=0
    G1 Z3 F600                              # Move bed away from the nozzle by 3mm from where it was
    _APPLY_NOZZLE_OFFSET

[gcode_macro APPLY_FILAMENT_OFFSET]
description: Apply a Z offset adjustment for a specific filament
gcode:
    {% set filament_z = params.Z|default(0)|float %}
    { action_respond_info("Setting Filament Offset to %.3fmm" % (filament_z)) }
    SET_GCODE_OFFSET Z_ADJUST={filament_z}
```

- Replace the `[zoffset]`, `[test_zoffset]`, `[get_zoffset]`, `[save_zoffset]`, and `[set_zoffset]` sections with these sections.

  * Note that the `[move_subzoffset]` macro is deleted/removed as a consequence of these changes.

```
# All the following zoffset calls only exist to keep Qidi's xindi happy
[gcode_macro zoffset]
description: Apply baseline Z offset which is always zero for Beacon Contact
gcode:
    SET_GCODE_OFFSET Z=0                    # Apply a zero gcode_offset

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

[gcode_macro save_zoffset]
description: Use APPLY_FILAMENT_OFFSET instead
gcode:
    { action_respond_info("Use APPLY_FILAMENT_OFFSET instead") }

[gcode_macro set_zoffset]
description: Apply baseline Z offset which is always zero for Beacon Contact      
gcode: 
    SET_GCODE_OFFSET Z=0                    # Apply a zero gcode_offset
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
    {% set accel = printer.toolhead.max_accel|int %}               # Take not of current acceleration value
    _FIND_Z_EQUALS_ZERO                                            # The user must make sure that nothing else homes Z after this call
    M204 S1000
    {% if k|int==1 %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=kamp
        BED_MESH_PROFILE LOAD=kamp
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"kamp"'
    {% else %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=default
        BED_MESH_PROFILE LOAD=default
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"default"'
        SET_GCODE_VARIABLE MACRO=G29 VARIABLE=k VALUE=1            # Reactivate KAMP/Adaptive mode for next time
    {% endif %}
    M204 S{accel}
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
G28 X Y
G1 X150 Y150
BEACON_AUTO_CALIBRATE
G29
G31
SAVE_CONFIG
```

This will:
- instruct to generate a `default` bed mesh of the whole bed when doing a scan (`G32`)
- home XY axis only (`G28 XY`)
- collect the beacon calibration model (`BEACON_AUTO_CALIBRATE`)
- do a full calibration home and bed mesh (`G29`)
- put the Plus4 back into Kamp mode meshing ready for the next print (`G31`)
- The whole lot gets saved to internal memory afterwards to persist across printer restarts (`SAVE_CONFIG`)

***

## A note regarding `default` bed-meshing behaviour changes

With the above changes, the intent of `default` bed meshing has changed somewhat from the original behavior.

Due to the speed of Beacon meshing, and for the benefits of always using an up to date mesh, the
`G29` macro is designed around always generating a new mesh by default.

If you're wanting to generate a new default mesh (eg. by calling `G32`) then `G29` will default to generating
a fresh full bed mesh of the whole bed.  Basically `G32` is only used now to see what your full bed mesh looks
like for tasks like tramming, initial configuration, and so on.

What this means is that when re-printing objects, if you select the `Re-use existing mesh` option, what
it will do instead is generate a fresh full `default` bed mesh and load that, which may not be what you
were expecting.  Your model will still print, but using the freshly generated default mesh, so this new
behaviour doesn't affect regular printing operations in any other way.

Basically just leave KAMP/dynamic meshing on all the time unless you have a specific need to generate
a `default` mesh (such as during the initial Beacon calibration after installation, tramming, etc).

***

## APPLY_FILAMENT_OFFSET - What it does and how to use it

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

**NOTE**: *If you were using bed tramming by folllowing this guide before 14th Feb 2025, then those macros
will need to be replaced with the following macros as they handle bed tramming more accurately*

Are you tired of tramming the bed using the old paper and nozzle drag test?  The Beacon Probe knows precisely
how far away the nozzle is from the bed.  It'll do it more accurately than you can by dragging a piece of
paper under the nozzle.

This makes the task of tramming the bed using the 4 knobs under the print bed a lot easier.

Add the following macros to the end of your `gcode_macro.cfg` file:

```
[gcode_macro SCREW_ADJUST_START]
gcode:
    _FIND_Z_EQUALS_ZERO
    M104 S0                 # Turn off hotend

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
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle

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
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle

[gcode_macro SBR]
description: Get zoffset at back-right bed adjustment screw position
gcode:
    {% set screw_pos_x = printer.configfile.settings.bed_screws.screw3[0] %}
    {% set screw_pos_y = printer.configfile.settings.bed_screws.screw3[1] %}
    {% set beacon_off_x = printer.configfile.settings.beacon.x_offset %}
    {% set beacon_off_y = printer.configfile.settings.beacon.y_offset %}
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle
    G1 X{screw_pos_x - beacon_off_x - 20} Y{screw_pos_y - beacon_off_y - 20} F6000
    PROBE PROBE_METHOD=proximity
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle

[gcode_macro SBL]
description: Get zoffset at back-left bed adjustment screw position
gcode:
    {% set screw_pos_x = printer.configfile.settings.bed_screws.screw4[0] %}
    {% set screw_pos_y = printer.configfile.settings.bed_screws.screw4[1] %}
    {% set beacon_off_x = printer.configfile.settings.beacon.x_offset %}
    {% set beacon_off_y = printer.configfile.settings.beacon.y_offset %}
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle
    G1 X{screw_pos_x - beacon_off_x + 20} Y{screw_pos_y - beacon_off_y - 20} F6000
    PROBE PROBE_METHOD=proximity
    G1 Z3 F600      # Ensure the bed is moved away from the nozzle
```

Each of the macros above will position the probe above the knobs so you can adjust and re-measure quickly

To use these macros, first heat your print bed to your typical printing temperature.
When the print bed's temperature has stabilised, call `SCREW_ADJUST_START` from the console.
This re-homes the axes and re-confirms where the nozzle touches the build plate, and then turns the
hotend off.  From here on the Beacon will probe the bed distance using its proximity mode.

Now call the `SFL`, `SFR`, `SBL`, and `SBR` macro listed above and look at the last line of the output

For example: `// Result is z=1.929233`

This informs you of the Z offset of the print bed at each screw location relative to the Z=0 homing
position at the center of the print bed.  You can now adjust the knob under the bed
and call the same macro again to obtain the new offset.  The goal is to get within 0.02mm of Z=2.0

This can be repeated for each of the 4 screw points until all are equal within 1.98 to 2.02mm
Better accuracy than this may be difficult to achieve due to backlash in the Z-axis lead screws.


## Beacon and KAMP Line Purge and Meshing

If you are using the KAMP Line Purging, you may notice that some parts of the Beacon will catch onto
the purged line.  If this is affecting you, then here's a solution.  This places the purge line
towards the back-right of the print area where the Beacon module is unlikely to catch on any part of it.

[KAMP_Settings.cfg](./KAMP_Settings.cfg)

[KAMP/Line_Purge.cfg](./Line_Purge.cfg)

Additionally here are some (optional) changes to the KAMP meshing file which will always do full bed
meshing when the `default` meshing profile is selected.

[KAMP/Adaptive_Meshing.cfg](./Adaptive_Meshing.cfg)

Replace the contents of the `KAMP_Settings.cfg` file that lives __*in the same directory*__ as your
`printer.cfg` file with the contents of the [KAMP_Settings.cfg](./KAMP_Settings.cfg) file.

**NOTE**: Do not edit the `KAMP_Settings.cfg` file that is in the `KAMP` sub-directory as it is
unused by the Plus4.

Also, replace the contents of the `Line_Purge.cfg` file which is in the `KAMP` sub-directory
with the contents of the [KAMP/Line_Purge.cfg](./Line_Purge.cfg) file.

Optionally, replace the contents of the `Adaptive_Meshing.cfg` file which is in the `KAMP` sub-directory
with the contents of the [KAMP/Adaptive_Meshing.cfg](./Adaptive_Meshing.cfg) file.

Now Save and Restart.

***

***

# FAQ

**This is an optimized and fairly comprehensive guide resulting from questions from dozens of users on Discord.**

**You are encouraged to read it fully as it will very likely answer most of your questions you'll have along the way.**

![image](https://github.com/user-attachments/assets/ef9a4788-260d-4640-8cb5-208ebfb9c259)


## I've followed your guide, but the automatic Z height detection is WAY off!

The above configuration guide is primarly intended for use with the stock Qidi configs, or a very lightly modified
version of them.  It is also assumed you are using the `KAMP/Line_Purge.cfg` and `KAMP/Adapative_Meshing.cfg` macros.

Without doing so, there is a strong chance that the wrong bed mesh may be loaded.  This can occur if you have modified
the `G29` macro to add `ADAPTIVE=1` to the `BED_MESH_CALIBRATE` call arguments and then call `BED_MESH_PROFILE LOAD=xxx`
afterwards.  It appears that adding `ADAPTIVE=1` will cause `BED_MESH_CALIBRATE` to ignore the `PROFILE` argument.


## I've configured everything using the guide, but my first layers still aren't perfect

First, make sure that your nozzle has been torqued at 300C into the hotend.

Secondly, ensure that your Z axis lead screws are thoroughly cleaned and lubricated.
The contact based Z end stop detection works by determining when the bed slows down against the nozzle.
Other sources of friction in the lead screws can have a similar effect and cause false/high readings.

Further, the state of the silicon rubber scrubbing brush, and small PEI cleaning plate is very important.  If
these are worn or otherwise in bad condition, then they may not be cleaning your nozzle properly, resulting in
filament left on the nozzle, which can affect Z offset readings.

Additionally if your nozzle is dirty and/or covered in melted filament this may also be causing bad end stop detection.

I have found that inadequate torquing of the nozzle at a high temperature, dirty leads screws and/or nozzle, and
poorly maintained nozzle cleaning hardware are the primary cause of unreliable/inconsistent results.

Additionally, it's been reported that various after-market nozzles and hotends for the Qidi Plus4 are poorly sized, ill-fitting,
and/or do not hold the nozzles or the heated portion of the hotend steady.  If you are using after-market hotend parts, it would
serve you well to verify that every part of your aftermarket hotend is adequately sized and secured properly.


## I've tightened my nozzle at 300C, cleaned my Z-Axis lead screws and nozzle, but the results are still a bit off

My first recommendation here is to read and use
[the `APPLY_FILAMENT_OFFSET` guide](./README.md#apply_filament_offset---what-it-does-and-how-to-use-it)
to apply per-filament tweaks to your offset for a filament.

In general, try to avoid the urge to rush in and start fiddling with the inner workings of the automatic Z offset calculation
system within `_APPLY_NOZZLE_OFFSET` as doing so will affect the behavior of ALL filaments.  Wait until you have used a wide
range of filament of different temperatures and are able to see a pattern in how it's behaving.


## I've been using APPLY_FILAMENT_OFFSET but most the offsets are consistently a little high, or a little low

The beacon module, when touching the build plate to establish where Z=0 is, often experiences some "overshoot".

Within the `_APPLY_NOZZLE_OFFSET` macro there is a variable named `offset_correction` that is presently set to `0.07mm` which is
a value that I personally found to be necessary.  If most of your filaments are requiring something of a fixed adjustment up or down,
then it may be that your particular beacon module is reacting differently to mine.  In this case feel free to adjust that fixed
contact compensation offset up/down as suits your particular module.  Closer to zero means bringing the nozzle closer to the print
bed, and larger values means moving the nozzle further from the print bed.  Just remember to save and restart the firmware after
making the change.

Note that `offset_correction` should NEVER need to be lowered to below `0.0`, nor above `0.2`.  If you find yourself in this
situation, then stop, as something else is definitely going wrong and it needs to be addressed first.  Read the rest of the FAQ as
the answer to your problem is instead likely addressed by those suggestions.


## The automated offset mechanism is having difficulty consistently finding when the nozzle touches the print bed

This could manifest as the `G29` macro constantly retrying and complaining that there's too much varation, or it may succeed, but
with the nozzle actually located some significant distance away from the print bed.

This generally caused by mechanical issues whereby the nozzle touch is triggering too early, or you have hard filament stuck to your nozzle.
If cleaning the Z-axis lead screws and cleaning your nozzle doesn't solve this issue, then try these following entries added to the
`[beacon]` config section in `printer.cfg`.

**Updated Note:** I have made the following the default config now after some testing to ensure that
it doesn't affect the operation of machines in good mechanical condition.

```
contact_sensitivity: 1          # You can try the default of 0, but if your
                                # automatic Z is too high, then put back to 1
contact_latency_min: 2          # You can try the default of 0, but if your
                                # automatic Z is high, put back to 2 or 3
```

The above configurations attempts to work around the issue of overly early nozzle tap triggers from a mechanically noisy/rough Z axis
system which can cause the first layer to be too high.

If you are still seeing your offsets be consistently high, try raising
`contact_latency_min` up to `4` and see if that resolves it.  If that still doesn't solve it, then there is likely something
mechanically wrong occurring with your printer and this needs to be addressed.


## I've done all the above, but hotter temperature filaments have worse first layers than cold temperature filaments, or vica-versa

This shouldn't really occur as the updates macros now determine where Z=0 is by using a fixed temperature offset from
the printing temperature.  This eliminates variations due to the thermal expansion of the hotend as all probing temperatures
are now relative by a fixed difference.

If you are experiencing inconsistent from one filament to another, then I refer to the `APPLY_FILAMENT_OFFSET` section.


## Is there an easier way to determine my hotend's thermal expansion co-efficient?

**NOTE:** *This section is now deprecated, but I'll leave this macro and work here for posterity sake*

I won't say it's easier, but there is an automated process that is [documented here](./Hotend-Expansion-Coefficient.md)

If you enjoy pain, frustration and fastidiously cleaning your nozzle and hotend, then proceed.


## My first layers are pretty good most of the time, but sometimes it can be a little inconsistent

In this case, your bed meshing speed may be too high.  The higher the speed you generate a mesh at, the less accurate the
eddy current sensing becomes.

Inside the `[bed_mesh]` section in your `printer.cfg` file, find the `speed` field and drop it back to `150` or even `100`
and see if that helps.  If that doesn't resolve issues then reach out to the Beacon discord for assistance.


## My beacon meshing detection light doesn't stay on for the whole meshing sequence

Firstly, it is ok/normal for the meshing light to turn off at the ends of an X pass, but if midway during an X pass the
Beacon's eddy current detection LED light doesn't stay on, that means that the print bed is too far away from the sensor
to take an accurate mesh.

It is unfortunate, but with the stock Qidi build plate, and even when using my mounting model which mounts the beacon as
close to the bed that Beacon officially recommends, that sometimes over a full (or partial) bed mesh that variances in the
print bed height can cause the bed to move out of detection range.

If you are experiencing this issue, then I have developed a modified `G29` macro below, with which you can replace the
above guide's regular `G29` macro with in its entirety.

*So what's going on here?* - The Beacon module always does a bed mesh with the nozzle 2.0mm away from the print bed.  This
is hard-coded into the beacon code.  The following tweaked `G29` macro will fool the Beacon into believing that the nozzle
is 2.0mm away when in reality it is closer, and with this we can hopefully keep the print bed always in range of the eddy
current scanning mode.

The Gcode macro variable, `bed_meshing_offset`, controls this over-ride adjustment.  A negative value will move the bed a
bit closer to the nozzle/Beacon while a positive value will move it further away.  For bed safety reasons, specifying
values outside of the range of `[-1.0, 1.0]` will be capped to `-1.0` or `1.0`.

*A Warning* - Since this has the effect of bringing the nozzle closer to the bed during scanning, there is a small risk
that if your bed is dramatically tilted that the nozzle can potentially scratch the build plate.  For this reason I have
kept this version of `G29` separate to the main configuration guide. 

A `bed_meshing_offset` value of `-0.4`, which is present in the replacement `G29` macro below, should provide for enough
of an adjustment to allow for eddy-current meshing of the whole print bed without adding too great of a risk of
scratching the build plate, but I make no promises that it won't.  Use at your own risk with this knowledge in mind.

```
[gcode_macro G29]
variable_k:1
variable_bed_meshing_offset: -0.4           # Generate bed with this amount applied
                                            # to the default meshing height of 2.0mm
                                            # negative = closer, positive = further
                                            # Acceptable range is [-1.0, 1.0]
description: Prepare print bed, generate a bed mesh, and apply global Z nozzle offset
gcode:
    {% set accel = printer.toolhead.max_accel|int %}         # Take note of current acceleration value
    {% set z_home_x = printer.configfile.settings.beacon.home_xy_position[0] %}
    {% set z_home_y = printer.configfile.settings.beacon.home_xy_position[1] %}
    # Read bed meshing offset value.  Cap value to within the [-1.0, 1.0] range
    {% set bmo = [([(printer["gcode_macro G29"].bed_meshing_offset)|float, -1.0]|max), 1.0]|min %}
    {% set mesh_closer = (2.0 + bmo)|float %}
    {% set mesh_return = (2.0 - bmo)|float %}
    { action_respond_info("  Mesh Closer = %.2f" % (mesh_closer)|float) }
    { action_respond_info("  Mesh Return = %.2f" % (mesh_return)|float) }

    _FIND_Z_EQUALS_ZERO

    G1 X{z_home_x} Y{z_home_y} F7200
    G1 Z{mesh_closer} F600
    SET_KINEMATIC_POSITION Z=2.0

    M204 S1000            # Set acceleration to a less aggressive value for smoother bed meshing
    {% if k|int==1 %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=kamp
        BED_MESH_PROFILE LOAD=kamp
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"kamp"'
    {% else %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=default
        BED_MESH_PROFILE LOAD=default
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"default"'
        SET_GCODE_VARIABLE MACRO=G29 VARIABLE=k VALUE=1
    {% endif %}
    M204 S{accel}        # Restore old acceleration value

    G1 X{z_home_x} Y{z_home_y} F7200
    G1 Z{mesh_return} F600
    SET_KINEMATIC_POSITION Z=2.0
```


## Where can I go for further assistance with issues?

You can reach out to me, `stew675` on the [Qidi Official Discord](https://discord.gg/B6jDttWUE6) in the Plus 4 channel

Alternately you can reach out to the [Official Beacon Discord Channel](https://discord.gg/MzTR3zE) and ask for help there


## Supporting the creator

Enjoying my guide and work?  [How about buying me a coffee!](https://ko-fi.com/stew675)
