# BEEF system - better than KAMP?

> [!WARNING]
> **DO NOT USE THESE DIRECTLY RIGHT NOW!**
> 
> These are still WIP and meant for testing and evaluation purposes by people who are confident with Klipper and
> willing to potentially sacrifice a build plate in testing. Chances are you will crash your machine if you aren't 
> careful and can't understand these commands just reading them Once this is finalized, this will receive updates 
> to make it simpler to use.

Probably not for accuracy, but for speed certainly. 

Instead of taking like 10-15 minutes to prep for a 2 minute print, this (combined with conditional wiping routine skipping the purge/PEI wipe steps) brings that down to under 3 minutes prep time, assuming you were letting the bed heat up while you were slicing the print. 

This doesn't strictly improve "first" cold prints, as that heatup routine needs to be done either as part of the print or as part of the routine before printing, but for follow-up and back-to-back prints I find the time the Qidi takes to be excessive and in some cases detrimental (due to the effects of heat soaking on the piezo sensors)

In general, your bed mesh shouldn't really change unless you are messing with the hardware (e.g. swapping build plates). Even then, it may not change enough to matter.
- As the bed changes with temp, we can have the Print_Start routine choose the appropriate bed mesh (e.g. fine_mesh_70c)
- To help create bed meshes for everything, we can make a macro that speeds up the creation of multiple meshes back-to-back. 
- Since different build plates have different properties, we could go further and make a separate bed mesh or z offset per plate type, but this is beyond my scope at the moment.
- In my workflow, if I am swapping build plates back and forth, I already have to wait for the build plate to get up to temp anyhow, so some of the benefit here is lost.

In my opinion, the Qidi system for probing is quite clever and reasonable at getting a proper offset. However, the lack of reliability at higher temps means that back-to-back prints may randomly fail.
Therefore, instead of a system that relies on such probing routine before every print, I propose the following:

## Roadmap
- [X] Basic functionality implemented including temperature model
- [ ] Improved data from round 2 of testing and probably use a LUT generated from a better thermal model
- [ ] Set up auto-bed-meshing macro to speed up process of making new meshes
- [ ] Set up ability to store multiple base offsets - e.g. per plate type config or something
- [ ] Put the final model + macros back on here with improved instructions

## How
- When the bed and chamber temps are cold, a "general" Z offset is found. This is tored in saved_variables
- Bed meshing is done at the appropriate temperatures for printing - already these are zeroed around the inductive probe reading at the start of the mesh so no compensation is needed 
- During Print_Start, we grab the stored "base" offset from the cold test from saved_variables
- Rather than using G29, we instead just apply a temperature compensation value to ensure our physical z offset stays correct
- Finally, we load the bed mesh based on the set temp of the bed rounded to nearest 10c (or whatever you change modulus to)

> [!NOTE]
> There is a second benefit to doing faster/fewer bed meshes such as mentioned in [Stew675's post (link)](https://github.com/qidi-community/Plus4-Wiki/blob/main/content/more-accurate-bed-meshing/README.md). They are more accurate as if the chamber is not at equilibium, the probe reading will drift as its temperature changes. Therefore, probing a single point and the minimum-viable grid of points (e.g. 7x7) may result in a more accurate mesh

In general, I've found my bed to drift not all that much with temperature changes, but found the z probe to drift a boatload. As much as 0.25mm closer to bed as the chamber warms up

## Random notes

- So I tried to create a model that predicts the drift based on bed temp and chamber temp. Chamber temp takes longer to hit so it does influence the probe temp.
- Right now that model isn't really great, it's just `temp_comp = coefficient * bed_temp * chamber_temp + bias`.
> Current model is: `thermal_comp = (-0.0000444 * bed_temp * chamber_temp) + 0.045`
- The screen z offset can be adjusted per print but it doesn't persist so long as we adjust print stop and cancel macros - stops cumulative errors
- Still uses the Qidi Fudge Factor (the 0.11-0.15 value) in the calculation, but I found I needed to flip the sign 
- I'll update with a better thermal model after developing a nice transfer function

# Current Macros (will be renamed/cleaned up once finalized):

Also missing from here are the print_start, print_cancel etc changes. These will be outline more specifically in the finalized version and are not included to reduce the chance of someone using this inadvertantly copy/pasting macros in this current state.

```
[gcode_macro BEEF_GET_Z_OFFSET]
description: Probe, apply, and save new Z offset with heated nozzle (cold bed/chamber). Also Errors if below 15c since that's probably not good for calibration.
gcode:
    {% set hotendtemp = params.HOTEND|default(170)|int %}
    {% set max_chamber_temp = 30 %}
    {% set max_bed_temp = 30 %}
    
     {% set bed_temp = printer["heater_bed"].temperature %}
     {% if bed_temp < 15.0 or bed_temp > max_bed_temp %}
         M118 [BEEF] ERROR: Bed temperature ({bed_temp}°C) is outside acceptable range (15.0-{max_bed_temp}°C)
         M118 [BEEF] Let bed cool to before calibrating Z-offset
     {% else %}
         {% set chamber_temp = printer["heater_generic chamber"].temperature %}
         {% if chamber_temp < 15.0 or chamber_temp > max_chamber_temp %}
             M118 [BEEF] ERROR: Chamber temperature ({chamber_temp}°C) is outside acceptable range (15.0-{max_chamber_temp}°C)
             M118 [BEEF] Let chamber cool before calibrating Z-offset
         {% else %}
            M118 [BEEF] Starting Z-offset calibration (Bed: {bed_temp}c, Chamber: {chamber_temp}c)
            SET_GCODE_OFFSET Z=0 MOVE=0
            BED_MESH_CLEAR
            G28
            Z_TILT_ADJUST
            G28
            
            # Heat nozzle to calibration temperature
            M104 S{hotendtemp}
            M109 S{hotendtemp}
            G4 P5000  # Wait 5 seconds
            
            BEEF_submacro_probe_offset
            BEEF_submacro_apply_offset
            BEEF_submacro_save_offset
            
            # Cool down nozzle
            M104 S0
            
            # Move to safe position
            G1 Z30 F600
            G1 X10 Y10 F6000
            
            M118 [BEEF] Z-offset calibration complete with hotend at {hotendtemp}c
            M118 [BEEF] This is the BASE offset stored in saved_variables
         {% endif %}
     {% endif %}

[gcode_macro BEEF_submacro_probe_offset]
gcode:
    TOGGLE_CHAMBER_FAN
    G1 Z10 F600
    Z_VIBRATE
    QIDI_PROBE_PIN_1
    M204 S50
    G4 P500

    probe probe_speed=5 lift_speed=18 samples=5 sample_retract_dist=10
    G1 Z{printer.probe.last_z_result} F600
    M114
    G4 P1000

    G1 Z30 F600
    QIDI_PROBE_PIN_2
    M204 S10000
    TOGGLE_CHAMBER_FAN

[gcode_macro BEEF_submacro_apply_offset]
variable_z_applied: 0.0
gcode:
    {% set actual_probe = printer.probe.last_z_result|float %}
    {% set qidi_fudge_factor = 0.11 %}
    
    # This 0.11 is the qidi-style "extra" offset.
    {% set corrected = actual_probe + qidi_fudge_factor %}  
    
    SET_KINEMATIC_POSITION Z={corrected}
    SET_GCODE_VARIABLE MACRO=BEEF_submacro_apply_offset VARIABLE=z_applied VALUE={corrected}

    M118 [BEEF] Actual probe result: {actual_probe}
    M118 [BEEF] Corrected Z offset with Qidi Fudge Factor ({qidi_fudge_factor}) is: {corrected}

[gcode_macro BEEF_submacro_save_offset]
gcode:
    {% set max_offset = 0.65 %} # Increased some from 0.5 as it was right at 0.5 frequently it seemed
    {% set zpos = printer["gcode_macro BEEF_submacro_apply_offset"].z_applied %}
    
    {% if zpos < max_offset %}
        SAVE_VARIABLE VARIABLE=z_offset VALUE={zpos}
        M118 [BEEF] Z offset saved: {zpos}
    {% else %}
        M118 [BEEF] Z offset not saved — value too large: {zpos}
    {% endif %}

[gcode_macro BEEF_CREATE_BED_MESH]
description: Create and save a bed mesh using inductive probe for specific temperature
gcode:
    {% set bedtemp = params.BED|default(70)|int %}
    {% set temp_rounded = ((bedtemp + 5) // 10) * 10 %}  # Round to nearest 10c
    {% set profile_name = "fine_mesh_" ~ temp_rounded ~ "c" %}
    
    M118 Generating bed mesh profile: {profile_name} at {bedtemp}c

    # Clear any previous mesh and Z offset
    SET_GCODE_OFFSET Z=0 MOVE=0
    BED_MESH_CLEAR

    G28

    # Heat bed to target temperature
    M140 S{bedtemp}
    M118 Waiting for bed temperature to stabilize at {bedtemp}°C...
    M190 S{bedtemp}

    # Bed leveling pass
    Z_TILT_ADJUST

    # For whatever reason, adding the G28 here is bad and 1.0mm too high
    # I think it has to do with the Z endstops but I don't want to mess with it
    # Maybe a kinematic correction down 1mm is in order, but for now comment out G28 as it works fine too
    # G28

    # Create the temperature-specific mesh
    BED_MESH_CALIBRATE PROFILE={profile_name}
    
    # Save the profile name to variables for reference
    SAVE_VARIABLE VARIABLE=profile_name VALUE='"{profile_name}"'
    
    # Move to safe position
    G1 Z30 F600
    G1 X10 Y10 F6000
    
    # Turn off heaters
    M140 S0
    
    M118 Temperature-specific mesh {profile_name} created and saved
    M118 Run SAVE_CONFIG to save mesh data

[gcode_macro CALCULATE_TEMP_COMPENSATION]
description: Calculate and apply temperature-based Z-offset compensation
gcode:
    {% set bed_temp = printer["heater_bed"].temperature %}
    {% set chamber_temp = printer["heater_generic chamber"].temperature %}
    {% set base_offset = printer.save_variables.variables.z_offset %}
    
    SET_GCODE_OFFSET Z=0 MOVE=0

    # Only apply thermal compensation when bed is >40°C
    {% if bed_temp > 40 %}
        # Calculate thermal drift compensatio
        {% set thermal_comp = (-0.0000444 * bed_temp * chamber_temp) + 0.045 %}

        # Subtract thermal compensation from base offset
        {% set total_offset = base_offset - thermal_comp %}
        
        # Apply the offset
        SET_GCODE_OFFSET Z={total_offset} MOVE=0
        
        M118 Applied Z-offset {total_offset}mm
        M118 (Base offset: {base_offset}) - (Comp: {thermal_comp})
    {% else %}
        SET_GCODE_OFFSET Z={base_offset} MOVE=0
        M118 Applied base Z-offset: {base_offset}mm (No thermal compensation used <40c)
    {% endif %}


[gcode_macro BEEF_TEST_STORED_OFFSET_W_TEMPCOMP]
description: Test Z-offset with thermal compensation at current temperatures
gcode:
    G28
    
    ; Calculate and apply temperature compensation
    CALCULATE_TEMP_COMPENSATION
    
    ; Load bed mesh profile
    BED_MESH_PROFILE LOAD=fine_mesh
    
    ; Move to center and park 2mm above mesh-adjusted surface
    G1 X150 Y150 F6000
    G1 Z2 F300
    
    M118 [BEEF] Toolhead is now 2mm above center of mesh-adjusted bed w/thermal comp
    M118 [BEEF] Jog down 1mm manually and check with 1mm feeler gauge
```