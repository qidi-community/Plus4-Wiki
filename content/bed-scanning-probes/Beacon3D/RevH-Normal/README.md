# Beacon3D RevH Normal Installation and Configuration Guide

*Note that all these configurations relate ONLY to using the Beacon in Contact mode on the Qidi Plus4 Printer*

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

First, on an ssh command shell to the printer, run `ls /dev/serial/by-id/usb-Beacon*` to find your Beacon serial number

Edit your `printer.cfg` file.  

- In `[stepper_z]` check that `endstop_pin:` is set to `probe:z_virtual_endstop`.  It should already be so on the Plus4

- In `[stepper_z]`  ensure that the `position_endstop` line is commented out

- Set `homing_retract_dist` to 0 on all of your steppers

- Comment out the `[smart_effector]`, `[safe_zhome]` and `[qdprobe]` sections in `printer.cfg` in their entirety

- Ensure `[force_move]` remains uncommented.  Various Plus4 UI moves, platform reset, and power loss recovery, need it.  We'll fix up any unnecessary calls to `SET_KINEMATIC_POSITION` later.

- Replace the `[z_tilt]` and `[bed_mesh]` sections with the following sections below:

```
[z_tilt]
z_positions:
    -17.5,152
    335.7,152

points:
    76, 170.8
    230, 170.8

speed: 150
horizontal_move_z: 5
retries: 5
retry_tolerance: 0.005

[bed_mesh]
speed:250
horizontal_move_z:2
mesh_min:15,15
mesh_max:295,283
probe_count:15,15
algorithm:bicubic
bicubic_tension:0.3
mesh_pps: 2,2
```

- Add the following `[beacon]` section:

```
[beacon]
serial: /dev/serial/by-id/usb-Beacon_Beacon_RevH_<**INSERT-YOUR-BEACON-SERIAL-HERE**>
x_offset: 0                     # update with X offset from nozzle on your machine
y_offset: -18.8                 # update with Y offset from nozzle on your machine
mesh_main_direction: x
mesh_runs: 2
contact_max_hotend_temperature: 180
home_xy_position: 152, 152      # update with your safe Z home position
home_z_hop: 5
home_z_hop_speed: 30
home_xy_move_speed: 300
home_y_before_x: False
home_method: contact
home_method_when_homed: proximity
home_autocalibrate: unhomed
home_gcode_pre_x: _BEACON_HOME_PRE_X
home_gcode_post_x: _BEACON_HOME_POST_X
home_gcode_pre_y: _BEACON_HOME_PRE_Y
home_gcode_post_y: _BEACON_HOME_POST_Y
```

When in doubt, check out the copy of my full [printer.cfg](./printer.cfg) for reference.

***

### gcode_macros.cfg changes

There are a lot of changes here.  Take your time and you'll be fine.  When in doubt, check out the copy of my full [gcode_macro.cfg](./gcode_macro.cfg) for reference.

Edit `gcode_macro.cfg`

- Add the following `[_APPLY_NOZZLE_OFFSET]` and `[APPLY_FILAMENT_OFFSET]` sections to your file

```
[gcode_macro _APPLY_NOZZLE_OFFSET]
description: Apply the global nozzle offset and set position reference with G92
variable_nozzle_offset: 0.115           # Fixed nozzle offset specific to the printer.
                                        # This value should rarely be changed, if ever
gcode:
    {% set zoff = (printer["gcode_macro _APPLY_NOZZLE_OFFSET"].nozzle_offset)|float %}
    {% set ref = (5.0)|float %}
    {% set pos = (ref + zoff)|float %}
    { action_respond_info("Adjusting Z reference position by %.3fmm" % zoff) }
    SET_GCODE_OFFSET Z=0
    G1 Z{pos} F600
    G92 Z{ref}
    G1 Z{ref} F600

[gcode_macro APPLY_FILAMENT_OFFSET]
description: Apply a Z offset adjustment for a specific filament
gcode:
    {% set filament_z = params.Z|default(0)|float %}
    { action_respond_info("Setting Filament Offset to %.3fmm" % (filament_z)) }
    SET_GCODE_OFFSET Z_ADJUST={filament_z} MOVE=1 SPEED=3
```

- Replace the `[zoffset]`, `[test_zoffset]`, `[get_zoffset]`, `[save_zoffset]`, and `[set_zoffset]` sections with these sections:

```
[gcode_macro zoffset]
description: Apply baseline Z offset which is always zero for Beacon Contact
gcode:
    SET_GCODE_OFFSET Z=0 MOVE=1             # Apply a zero gcode_offset

# Development test
[gcode_macro test_zoffset]
description: Debugging test to compare the probe's contact and proximity Z Offset values
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
    M109 S145                               # Wait until hotend is up to temp to soften any filament on nozzle                                  
    G28 Z METHOD=CONTACT CALIBRATE=0        # Use contact to find our Z end-stop                
    M104 S0                                 # Turn off hotend
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

- Comment out, or delete, the `[homing_override]` section in its entirety


- Ensure that these 3 lines are commented out in your `PRINT_END` macro

```
[gcode_macro PRINT_END]
gcode:
#    {% if printer.gcode_move.homing_origin.z < 0.5 %}
#       SAVE_VARIABLE VARIABLE=z_offset VALUE={printer.gcode_move.homing_origin.z}
#    {% endif %}
```

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
gcode:
    # Turn off all fans to minimise sources of vibration and clear any old state
    M141 S0                                 # Turn off chamber heater
    M106 S0                                 # Turn off part cooling fan
    M106 P2 S0                              # Turn off auxiliary part cooling fan
    M106 P3 S0                              # Turn off chamnber exhaust/circulation fan        
    BED_MESH_CLEAR                          # Clear out any existing bed meshing context
    SET_GCODE_OFFSET Z=0                    # Comnpletely reset all prior notions of Z offset

    M104 S145                               # Warm nozzle to 145 to soften any remaining filament on nozzle
    G28 X Y                                 # Home X and Y axes
    M109 S145                               # Wait until hotend is up to temp if still necessary                                  
    G28 Z METHOD=CONTACT CALIBRATE=1        # Use contact to find our Z end-stop, and calibrate a model for tilt and meshing                
    Z_TILT_ADJUST                           # Ensure bed is level    
    G28 Z METHOD=CONTACT CALIBRATE=0        # Re-establish Z end-stop after bed levelling
    M104 S0                                 # Turn off hotend
    {% if k|int==1 %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=kamp
        BED_MESH_PROFILE LOAD=kamp
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"kamp"'
    {% else %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=default
        BED_MESH_PROFILE LOAD=default
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"default"'
    {% endif %}
    _APPLY_NOZZLE_OFFSET                     # Apply global nozzle offset
```

- Add these 4 macros to the end of your file:

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


## APPLY_FILAMENT_OFFSET - What it does and how to use it

The idea behind `APPLY_FILAMENT_OFFSET` is to do away with the fiddling about with the global Z offset
when changing to filaments that prefer a different Z offset to the replaced filament

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

The next time that we print with this filament, the filament specific Z offset will be applied and we will
get perfect first layers with it without having to fiddle with the global Z offset.

If this is done for all the filaments that you print with, then every time that you switch a filament then
it will be printed with the correct Z-offset and your layers should turn out perfect.


## Optional QoL Bed Tramming Macros

With the Beacon Probe now providing for accurate bed offset measurements, the probe can be used to make the
task tramming the bed using the 4 knobs under the print bed a lot easier.

Add the following macros to the end of your `gcode_macro.cfg` file:

```
[gcode_macro SFL]
description: Get zoffset at front-left bed adjustment screw position
gcode:
    G1 X{25 - printer.configfile.settings.beacon.x_offset} Y{21 - printer.configfile.settings.beacon.y_offset} F6000
    PROBE PROBE_METHOD=proximity

[gcode_macro SFR]
description: Get zoffset at front-right bed adjustment screw position
gcode:
    G1 X{285 - printer.configfile.settings.beacon.x_offset} Y{21 - printer.configfile.settings.beacon.y_offset} F6000
    PROBE PROBE_METHOD=proximity

[gcode_macro SBL]
description: Get zoffset at back-left bed adjustment screw position
gcode:
    G1 X{25 - printer.configfile.settings.beacon.x_offset} Y{281 - printer.configfile.settings.beacon.y_offset} F6000
    PROBE PROBE_METHOD=proximity

[gcode_macro SBR]
description: Get zoffset at back-right bed adjustment screw position
gcode:
    G1 X{285 - printer.configfile.settings.beacon.x_offset} Y{281 - printer.configfile.settings.beacon.y_offset} F6000
    PROBE PROBE_METHOD=proximity
```

Each of the macros above will position the probe above the knobs so you can adjust and re-measure quickly

To use these macros, first clear the bed mash, home and recalibrate the probe by calling the following macros

```
BED_MESH_CLEAR
SET_GCODE_OFFSET Z=0
G28
Z_TILT_ADJUST
```

then call the macros listed above and look at the last line (eg. `// Result is z=1.948191
`).  This informs you of how far away
the print bed is from the probe.  You can adjust the knob under the bed and call the same macro again to obtain
the new offset.  This can be repeated for each of the 4 screw points until all are equal within ~0.02mm.  It will
be difficult to obtain better accuracy than that.  By default, the Beacon probe sets itself to 2.00mm from the center
of the print bed after the call to `G28` is made, so therefore we are aiming for all 4 screw positions to report
something greater than `z=1.98` and less than `z=2.02`
