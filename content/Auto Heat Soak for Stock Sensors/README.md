# Auto Heat Soak for Stock Sensor (Piezos & Induction)

## Reasons of this code is created:

1. My stock piezo and induction sensors have good repeatability and low standard deviation.  
2. A Beacon is just too expensive for me.  
3. Even with PLA on a 30°C cool plate bed, open top glass and open door, I still need to “heat soak” before the Z-offset stabilizes.  
4. I want to press print, walk away, and let the machine do its thing—perfect first layer every time.  
5. Laziness.  
6. Laziness.  
7. Laziness. Yes, this is so important it deserves to be repeated three times.  


## Finding:

1. Assumption: machine always starts cold (bed 20 °C, chamber 20 °C).  
2. PLA on 30 °C cool plate bed, chamber off → needs 10–12 minutes after the bed reaches 30 °C to stabilize.  
3. PLA on 60 °C PEI plate bed, chamber off → needs 12–15 minutes after the bed reaches 60 °C to stabilize.  
4. ABS on 90 °C PEI plate bed, chamber at 60 °C → needs 20–25 minutes after the chamber reaches 60 °C to stabilize.  
   With my chamber heater at 0.7 power, it takes ~20 minutes to heat the machine from cold to target.  
   Total wait = 20 min heating + 20–25 min stabilizing = ~45 minutes.  
5. Stock firmware turns off the chamber heater during piezo probing and bed mesh, which causes Z-offset drift.  
   My code keeps the chamber heater on whenever a target value is defined.  
6. Sensor repeatability vs. time and Z-offset vs. chamber temp charts are shown below.  
7. Beacon/Cartographer users can probably benefit too—just swap in the appropriate probe command.

<img src="./Sensors%20Standard%20Deviations.png">
<img src="./Z-offset%20vs%20Time.png">


## Disclaimers:
1. Even with a machine that has been heat-soaked for 1–2 hours, my code will still force a 3-minute check to see if the Z-offset has shifted. There’s no way around this.  
2. Sampling every 3 minutes is necessary. Any shorter, and the changes are too small—well within sensor tolerance.  
3. Stability check runs for up to 10 cycles (≈30 minutes). If it’s still not stable after that, the print will start automatically.  
4. last_z = Z-offset measured 3 minutes ago  
5. new_z = current Z-offset  
6. diff = last_z – new_z  


## Changes:

### Step 1. Backup your gcode_macro.cfg
### Step 2. Reset your z-offset=0 in saved_variable.cfg
### Step 3. Update your `[print_start]` macro in gcode_macro.cfg
#### This ensures the chamber heater stays on (if a value is set) throughout the entire process.
***

```

[gcode_macro PRINT_START]
gcode:
    AUTOTUNE_SHAPERS
    {% set bedtemp = params.BED|int %}
    {% set hotendtemp = params.HOTEND|int %}
    {% set chambertemp = params.CHAMBER|default(0)|int %}
    set_zoffset
    M104 S0
    M106 P2 S0
    M106 P3 S0
    M106 S255
    G28      
    M141 S{chambertemp} #Default S0
    M140 S{bedtemp}   
    M106 S0
    CLEAR_NOZZLE HOTEND={hotendtemp}
    
    M190 S{bedtemp}     
    M191 S{chambertemp}  #New line added
    M104 S140
    Z_TILT_ADJUST       #New line added
    G1 Z30 F600         #New line added
    G1 X150 Y150 F7000  #New line added
    G29
    M141 S{chambertemp} #Default S0
    G0 Z50 F600
    G0 X5 Y5  F6000
    
    {% if chambertemp == 0 %}
    M106 P3 S255
    {% endif %}

    M109 S{hotendtemp}
    M141 S{chambertemp}    
    M204 S10000
    SET_PRINT_STATS_INFO CURRENT_LAYER=1
    ENABLE_ALL_SENSOR
    save_last_file
```

### Step 4. Changes in `[get_zoffset]` macro.
#### Comment out TOGGLE_CHAMBER_FAN because once the fan is off, the chamber heater shuts off too.
#### Z-offset can still be set manually on the touchscreen (and will auto-save).
#### If you want to lock in a permanent Z-offset, reset z_offset value in save_savriable.cfg to zero and change the p value below.
***

```
[gcode_macro get_zoffset]
gcode:
    #TOGGLE_CHAMBER_FAN #Comment out
    G1 Z10 F600
    Z_VIBRATE

    stability    # Call new macro 'stability' to check the z-offset change every 3mins till it is stabilized.

    QIDI_PROBE_PIN_1
    m204 S50
    G4 P500
    probe probe_speed=5 lift_speed=5 samples=5 sample_retract_dist=5
    move_subzoffset
    M114
    {% set p=(-0.08 + printer.gcode_move.homing_origin.z)|float %} #Default value -0.11, -0.15 nozzle further from plate, -0.08 nozzle closer to plate.
    SET_KINEMATIC_POSITION Z={p}
    G1 Z30 F600
    
    QIDI_PROBE_PIN_2
    m204 S10000
    #TOGGLE_CHAMBER_FAN #comment out 12/05/2525
```

### Step 5. Changes in `[G29]` bed mesh macro.
#### Makes sure chamber heater is always ON if value is set.
***

```
[gcode_macro G29]
variable_k:1
gcode:
    
    {% set temp = printer["heater_generic chamber"].target %}
    #M141 S0                   #Comment out
    {% if temp > 0 %}
        G4 P15000
    {% endif %}
    BED_MESH_CLEAR
    {% if k|int==1 %}
        G28
        M141 S{temp}             #Moved here, default value 0
        M191 S{temp}             #New added after moves above
        get_zoffset
        #original M141 position
        G1 X{150 - printer.probe["x_offset"]} Y{150 - printer.probe["y_offset"]} F9000
        G1 Z10 F600
        probe
        SAVE_Z_OFFSET_TO_BED_MESH
        G1 z10 F600
        M141 S{temp}             #New line added
        M191 S{temp}             #New line added
        BED_MESH_CALIBRATE PROFILE=kamp
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"kamp"'
        G4 P5000
        SAVE_CONFIG_QD
    {% else %}
        G28
        M141 S{temp}             #New line added
        M191 S{temp}             #New line added
        get_zoffset
        {% if printer["bed_mesh"].profiles.default %}
            M141 S{temp}             #New line added
            M191 S{temp}             #New line added
            BED_MESH_PROFILE LOAD=default
            SAVE_VARIABLE VARIABLE=profile_name VALUE='"default"'
        {% else %}
            G1 X{150 - printer.probe["x_offset"]} Y{150 - printer.probe["y_offset"]} F9000
            G1 Z10 F600
            probe
            SAVE_Z_OFFSET_TO_BED_MESH
            G1 z10 F600
            _BED_MESH_CALIBRATE PROFILE=default
            G4 P5000
            SAVE_CONFIG_QD
        {% endif %}
    {% endif %}
```

### Step 6. Add new `[stability]` related macros to gcode_macro.cfg.
#### zRangeTarget defaults to 0.015 mm (adjust if you want shorter/looser cycles).
#### G4 P180000 = 180,000 ms wait (3 mins). You can experiment with shorter waits, but too short and the drift hides in sensor tolerance.
#### PROBE samples=5 can be reduced if your probe is consistent (delete samples=5 to probe once).
***
```
#--------           STABILITY Check Gcode             --------------#
# Add this to your gcode_macro.cfg - COMPLETE WORKING SET

[gcode_macro STABILITY_STATE]
variable_compared_result: 0.015
variable_cycles: 0
variable_stable: 0
variable_last_z: 0.0
gcode:
    # State storage

[gcode_macro stability]
description: Induction sensor check on z-axis drift. Max 10 cycles, probe every 3mins.
gcode:
    {% set Compared_result = params.ZRangeTarget|default(0.015)|float %}
    SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=compared_result VALUE={Compared_result}
    SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE=0
    SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=stable VALUE=0
    SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=last_z VALUE=0.0

    M118 Starting stability check. Target = {Compared_result}

    # Initial probe
    QIDI_PROBE_PIN_2
    PROBE samples=5
    G1 Z30 F1800
    M118 Wait 180s for next probe
    G4 P180000
    CAPTURE_INITIAL_Z
    STABILITY_CYCLE_1

[gcode_macro CAPTURE_INITIAL_Z]
gcode:
    {% set initial_z = printer.probe.last_z_result|float %}
    SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=last_z VALUE={initial_z}
    M118 DEBUG: Initial last_z = { "%.6f"|format(initial_z) }

[gcode_macro STABILITY_CYCLE_1]
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 1 %}
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_2
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_2]
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 2 %}
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_3
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_3]
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 3 %}
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_4
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_4]
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 4 %}
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_5
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_5]  # Replace N with your cycle number
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 5 %}  # Replace N
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_6  # Replace N+1 (or STABILITY_FINISH if final)
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_6]  # Replace N with your cycle number
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 6 %}  # Replace N
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_7  # Replace N+1 (or STABILITY_FINISH if final)
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_7]  # Replace N with your cycle number
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 7 %}  # Replace N
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_8  # Replace N+1 (or STABILITY_FINISH if final)
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_8]  # Replace N with your cycle number
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 8 %}  # Replace N
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_9  # Replace N+1 (or STABILITY_FINISH if final)
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_9]  # Replace N with your cycle number
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 9 %}  # Replace N
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
        {% set check_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
        M118 DEBUG: After capture, check_stable = {check_stable}
        {% if check_stable == 0 %}
            STABILITY_CYCLE_10  # Replace N+1 (or STABILITY_FINISH if final)
        {% else %}
            STABILITY_FINISH
        {% endif %}
    {% else %}
        STABILITY_FINISH
    {% endif %}

[gcode_macro STABILITY_CYCLE_10]
gcode:
    {% set current_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if current_stable == 0 %}
        {% set Cycles = 10 %}
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=cycles VALUE={Cycles}
        M118 Starting Cycle {Cycles}
        PROBE samples=5
        G1 Z30 F1800
        CAPTURE_CYCLE_Z CYCLE={Cycles}
    
    {% endif %}
    STABILITY_FINISH

[gcode_macro CAPTURE_CYCLE_Z]
gcode:
    {% set cycle_num = params.CYCLE|default(1)|int %}
    {% set new_z = printer.probe.last_z_result|float %}
    {% set last_z = printer["gcode_macro STABILITY_STATE"].last_z|float %}
    {% set Compared_result = printer["gcode_macro STABILITY_STATE"].compared_result|float %}
    M118 DEBUG: Cycle {cycle_num} new_z = { "%.6f"|format(new_z) }
    M118 ===== Completed Cycle {cycle_num} ====
    {% set diff = (last_z - new_z)|abs %}
    {% if diff <= Compared_result %}
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=stable VALUE=1
        M118 Result is stable, Last_z= { "%.6f"|format(last_z) }, New_z= { "%.6f"|format(new_z) }, Diff= { "%.6f"|format(diff) }  ✓ , Target={Compared_result}
    {% else %}
        SET_GCODE_VARIABLE MACRO=STABILITY_STATE VARIABLE=last_z VALUE={new_z}
        M118 Not stable yet. Last_z= { "%.6f"|format(last_z) }, New_z= { "%.6f"|format(new_z) }, Diff= { "%.6f"|format(diff) }  ✗
        M118 Last_z now updated to { "%.6f"|format(new_z) }
        M118 Wait 180s for next probe
        G4 P180000
    {% endif %}

[gcode_macro STABILITY_FINISH]
gcode:
    {% set final_cycles = printer["gcode_macro STABILITY_STATE"].cycles|int %}
    {% set final_stable = printer["gcode_macro STABILITY_STATE"].stable|int %}
    {% if final_stable == 1 %}
        M118 Stability achieved after {final_cycles} cycles ✓
    {% else %}
        M118 No stable result after {final_cycles} cycles ✗
    {% endif %}
    Z_TILT_ADJUST
    G1 Z30 F1800
    G1 X150 Y150 F7000
```

