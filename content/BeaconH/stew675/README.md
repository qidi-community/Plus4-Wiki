
# Stew's Beacon Contact configuration settings

Note that all these configurations relate ONLY to using the Beacon in Contact mode.


## A (Mostly) Idiot proof G29 macro for Beacon Contact mode

This should work for the widest possible range of scenarios.

The sequence of events in this macro is very deliberately chosen for the fastest possible stock G29 equivalence.

Stock `G28` behaviour in Beacon Contact mode issues very slow Z axis movements.  This macro is written to use the
faster proximity mode Z axis movements to quickly cover unknown Z axis distances, before switching to the slower
and more precise contact mode.

It assumes nothing about any prior state, and certain events are chosen to work around a number of stock firmware bugs.
For example `G28 YX` will home Y but not X (a bug).  Setting `homing_retract_distance` distance to a non-zero value in
the `[stepper_x/y]` sections can also activate a firmware bug, so this retract distance is handled explicitly here.

```
[gcode_macro G29]
variable_k:1
gcode:
    M104 S145                               # Commence warming nozzle to 145 so any remaining filament stuck to nozzle is softened

    # Turn off all fans to minimise sources of vibration
    M141 S0                                 # Turn off chamber heater for this part
    M106 S0                                 # Turn off part cooling fan
    M106 P2 S0                              # Turn off auxiliary part cooling fan
    M106 P3 S0                              # Turn off chamnber exhaust/circulation fan
        
    BED_MESH_CLEAR                          # Clear out any existing bed meshing context
    SET_GCODE_OFFSET Z=0                    # Comnpletely reset all prior notions of Z offset

    {% if "x" not in printer.toolhead.homed_axes %}
        G28 X                               # Home X axis
    {% endif %}
    {% if "y" not in printer.toolhead.homed_axes %} 
        G0 X10 F1200                        # Move print-head away from any potential Y end-stop collision
        G28 Y                               # Home Y axis
    {% endif %}
                                  
    G28 Z METHOD=PROXIMITY                  # Use the fast proximity Z homing to get within a decent contact probing range                 
    Z_TILT_ADJUST                           # Ensure bed is level
    M109 S145                               # Wait until hotend is up to temp if still necessary
    G28 Z METHOD=CONTACT CALIBRATE=1        # Identify source of truth regarding when the nozzle is touching the build plate
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
    SET_GCODE_OFFSET Z=0.10                 # Apply a GCODE Offet for Z of 0.10, which works for most filaments
```
