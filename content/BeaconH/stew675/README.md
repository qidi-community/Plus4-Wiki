# Stew's Beacon Contact Installation Guide and configuration settings

Note that all these configurations relate ONLY to using the Beacon in Contact mode on the Qidi Plus4 Printer

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

### Physical Preparation

Print out my mounting model here: https://www.printables.com/model/1170120-beacon3d-mount-for-qidi-plus4

Install the mounting module along with the Beacon attached.  Route the beacon's cable to the mainboard.
The beacon appears to have no issues when plugged into one of the USB2 ports on the mainboard.

***

### Install the Beacon software

Follow the Beacon guide here: https://docs.beacon3d.com/quickstart/#3-install-beacon-module

***

### Klipper script changes

On your printer, edit the `/home/mks/klipper/klipper/extras/probe.py` file and comment out the lines as highlighted here:
https://github.com/QIDITECH/klipper/blob/PLUS4/klippy/extras/probe.py#L485-L492

Then save the file, and then power-cycle your printer.  This disables the Z-vibrate functionality that is incompatible with Beacon.

***

### printer.cfg changes

First, on an ssh command shell to the printer, run `ls /dev/serial/by-id/usb-Beacon*` to find your Beacon serial number

Edit your `printer.cfg` file.  

- In `[stepper_z]` check that `endstop_pin:` is set to `probe:z_virtual_endstop`.  It should already be so on the Plus4
- Set `homing_retract_dist` to 0 on all of your steppers
- Comment out the `[smart_effector]`, `[force_move]`, `[safe_zhome]` and `[qdprobe]` sections in `printer.cfg` in their entirety
- Add the following section:

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
    G1 Z{pos} F600

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

- Comment out, or delete, the gcode in the `Z_VIBRATE` macro like so:

```
[gcode_macro Z_VIBRATE]
gcode:
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

