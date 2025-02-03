# Cartographer3D for Qidi Plus 4

**Heads up - This is still a work in progress. Here (might) be dragons 🐲**

**Everything is functional but not tested yet by multiple users (yet). Consider this an Alpha / Beta. It is not aimed towards notice users. It requires, SSH access, changing Klipper files and updating configs and macros. If you don't understand this, you risk damaging your printer. Performing this mod may limit your ability to update to latest firmware from Qidi. Do not update without checking as it may overwrite important configs.**

⚠️ Do not contact Qidi support about issues with bed leveling, first layer issues, klipper, etc after making this mod. It's now your responsibility. ⚠️

This guide covers installing Cartographer3D on your Qidi Plus 4. Beacon guide is in the works and should be a mostly similar process.

## Hardware

You of course need a [Cartographer3D probe](https://cartographer3d.com/). USB version. Flat pack will be the most compatible version, since you can assemble it into any configuration. 

This guide is not mount specific, only to say you need a mount for the probe. A list of tested mounts are:

- [Cartographer3D Mount for Qidi Plus 4 by Spooknik](https://www.printables.com/model/1154767-cartographer3d-mount-for-qidi-plus-4)

You should note the X and Y offset of the center of the coil to the center of the nozzle. That will be needed later.

You must be certain the coil is between 2.6 to 3.0 mm from the nozzle tip.

## Software
A small note: The code with "+" and "-" before them are meant to indicate what is added and what is removed. When you copy and paste them onto your machine, please remove the "+" before any line, and delete the lines with "-" before them. 

### Backup Klipper

Firstly, we need to make a backup of your klipper install. Via SSH run the following: 

```
mkdir -p /home/mks/qidi-klipper-backup
(cd /home/mks; tar cvf - klipper printer_data/config) | (cd /home/mks/qidi-klipper-backup; tar xf -)
```

Now your klipper install has been backed up to `/home/mks/qidi-klipper-backup`. Just in case!

### Cartographer for Klipper

Cartographer needs a plugin for Klipper to work, this plugin is only supported on Python 3.9 or higher. The Qidi Plus 4 ships with Python 3.7 by default, we need to download Python 3.12 and remake the Klipper virtual environment. 

First download and extract precompiled Python 3.12.3

```bash
sudo service klipper stop

cd ~

wget https://github.com/stew675/ShakeTune_For_Qidi/releases/download/v1.0.0/python-3-12-3.tgz

tar xvzf python-3-12-3.tgz

rm python-3-12-3.tgz
```
Now Python 3.12.3 is in the home directory. We will delete the Klipper virtual enviroment and recreate it. Don't worry this will not touch any of your user data, but **you will need to reinstall any klipper plugins after this.**

```bash
sudo rm -rf klippy-env

~/python-3.12.3/bin/python3.12 -m venv klippy-env

cd ~/klippy-env

sed -i 's/greenlet==2.0.2/greenlet==3.0.3/' ../klipper/scripts/klippy-requirements.txt # Need to upgrade this package for 3.12.

bin/pip install -r ../klipper/scripts/klippy-requirements.txt
```

Now Klipper installed again using Python 3.12. Now we can install Cartographer.

```bash
cd ~

git clone https://github.com/Cartographer3D/cartographer-klipper.git

./cartographer-klipper/install.sh
```

The plugin is now installed. And we can start up Klipper again

```bash
sudo service klipper start
```

### Patching Klipper

Qidi's version of Klipper has a heavily modified version of `probe.py` and will not work with Cartographer for Klipper, we need to replace this file with vanilla Klipper's  `probe.py`.

```bash
sudo service klipper stop

wget -P ~/klipper/klippy/extras https://raw.githubusercontent.com/Klipper3d/klipper/refs/heads/master/klippy/extras/probe.py
```


Restart Klipper

```bash
sudo service klipper restart
```

### Klipper Configs

#### printer.cfg

We need to modify `[Z_stepper]` with the following:

```diff
[stepper_z]
step_pin:U_1:PB1
dir_pin:U_1:PB6
enable_pin:!U_1:PB0
microsteps: 16
rotation_distance: 4
full_steps_per_rotation: 200
endstop_pin:probe:z_virtual_endstop # U_1:PC3 for Z-max
endstop_pin_reverse:tmc2209_stepper_z:virtual_endstop
- position_endstop:1
position_endstop_reverse:285
position_max:285
position_min: -4
homing_speed: 10
homing_speed_reverse: 10
second_homing_speed: 5
+ homing_retract_dist: 0
homing_positive_dir:false
homing_positive_dir_reverse:true
#step_pulse_duration:0.0000001
```

Comment out (or delete) all the lines in the following sections:

```gcode
#[z_tilt]
#z_positions:
#    -17.5,138.5
#    335.7,138.5
#
#points:
#    0,138.5
#
#speed: 150
#horizontal_move_z: 5
#retries: 2
#retry_tolerance: 0.05

#[smart_effector]
#pin:U_1:PC1
#recovery_time:0
#x_offset: 25
#y_offset: 1.3
#z_offset: 0.000001
#speed:5
#lift_speed:5
#probe_accel:50
#samples: 2
#samples_result: submaxmin
#sample_retract_dist: 5
#samples_tolerance: 0.05
#samples_tolerance_retries:5

#[qdprobe]
#pin:!PA10
#z_offset:0.000001

#[bed_mesh]
#speed:150
#horizontal_move_z:5
#mesh_min:25,10
#mesh_max:295,295
#probe_count:9,9
#algorithm:bicubic
#bicubic_tension:0.4
#mesh_pps: 2,2
```

### gcode_macro.cfg

We need to change what the printer does at the start of the print to not use the stock Qidi probes and use Carto instead.

```diff
[gcode_macro PRINT_START]
gcode:
    AUTOTUNE_SHAPERS

    {% set bedtemp = params.BED|int %}
    {% set hotendtemp = params.HOTEND|int %}
    {% set chambertemp = params.CHAMBER|default(0)|int %}
    M104 S0
-   set_zoffset # This is now handled by Carto

    M106 P2 S0
    M106 P3 S0
    M106 S255
    G28  
    M141 S{chambertemp}  
    M140 S{bedtemp}  
    M106 S0
    CLEAR_NOZZLE HOTEND={hotendtemp}
    M191 S{chambertemp}  
    M190 S{bedtemp}   
    M104 S140
    G29
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

We need to change the homing overrides so the Z axis homes correctly

```diff 
[homing_override]
axes:xyz
gcode: 
    {% set HOME_CUR = 1 %}
    {% set driver_config = printer.configfile.settings['tmc2240 stepper_x'] %}
    {% set RUN_CUR = driver_config.run_current %}
    {% set HOLD_CUR = driver_config.hold_current %}
    m204 S10000
    M220 S100
	{% if params.X is defined %}
+       SET_KINEMATIC_POSITION Z=1.9 # Set Z position
+       G1 Z4 F600 # Lower Z by 4 to prevent dragging the nozzle
	    SET_TMC_CURRENT STEPPER=stepper_x CURRENT={HOME_CUR * 0.7} 
        G28 X
		SET_TMC_CURRENT STEPPER=stepper_x CURRENT={HOME_CUR}     
        BEEP I=1 DUR=100       
        G1 X10 F1200
    {% endif %}

    {% if params.Y is defined %}
+       SET_KINEMATIC_POSITION Z=1.9 # Set Z position
+       G1 Z4 F600 # Lower Z by 4 to prevent dragging the nozzle
		SET_TMC_CURRENT STEPPER=stepper_y CURRENT={HOME_CUR * 0.9} 
		G28 Y
		SET_TMC_CURRENT STEPPER=stepper_y CURRENT={HOME_CUR}  
        BEEP I=1 DUR=100          
       G1 Y10 F1200
    {% endif %}

    {% if params.Z is defined %}
        G28 x
        G28 Y
        G28 X
        G1 X150 Y150 F7800

        SET_KINEMATIC_POSITION Z={printer.toolhead.axis_maximum.z-30}
-       QIDI_PROBE_PIN_2
-       probe samples=2
-       SET_KINEMATIC_POSITION Z=1.9
-       G1 Z10 F600
-       Z_VIBRATE
-       QIDI_PROBE_PIN_1
-       probe probe_speed=10
+       probe
        SET_KINEMATIC_POSITION Z=-0.1
        G1 Z30 F480
    {% endif %}

    {% if params.X is undefined %}
    {% if params.Y is undefined %}
    {% if params.Z is undefined %}
        SET_KINEMATIC_POSITION X=0
        SET_KINEMATIC_POSITION Y=0
        SET_KINEMATIC_POSITION Z={printer.toolhead.axis_maximum.z-30}
        G91
        G1 Z7 F600	
        G1 X5 F2400
        G1 Y5 F2400
        G4 P2000
    
       SET_TMC_CURRENT STEPPER=stepper_x CURRENT={HOME_CUR * 0.8} 
        G28 X
    	SET_TMC_CURRENT STEPPER=stepper_x CURRENT={HOME_CUR} 
        BEEP I=1 DUR=100  
        G1 X45 F1200
    
    	SET_TMC_CURRENT STEPPER=stepper_y CURRENT={HOME_CUR * 0.9} 
    	G28 Y
    	SET_TMC_CURRENT STEPPER=stepper_y CURRENT={HOME_CUR} 
        BEEP I=1 DUR=100        
        G1 Y10 F1200

        SET_TMC_CURRENT STEPPER=stepper_x CURRENT={HOME_CUR * 0.8} 
        G28 X
    	SET_TMC_CURRENT STEPPER=stepper_x CURRENT={HOME_CUR} 
        BEEP I=1 DUR=100  
        G1 X10 F1200

        SET_KINEMATIC_POSITION Z={printer.toolhead.axis_maximum.z-10}

        G90
        G1 X150 Y150 F7800
        G91
-       QIDI_PROBE_PIN_2
        G28 Z
        G1 Z30  F600
    {% endif %}
    {% endif %}
    {% endif %}
    SET_TMC_CURRENT STEPPER=stepper_x CURRENT={RUN_CUR} 
    SET_TMC_CURRENT STEPPER=stepper_y CURRENT={RUN_CUR} 
    M204 S10000
    G90
-   QIDI_PROBE_PIN_2
```

Now we need to completely replace G29 with this

```
[gcode_macro G29]
variable_k:1
gcode:
    M141 S0
    BED_MESH_CLEAR
    SET_GCODE_OFFSET Z=0
    {% if "xy" not in printer.toolhead.homed_axes %}
        G28 Y                               # Home Y axis
        G0 Y20 F1200                        # Move Y axis away from Y end-stop
        G28 X                               # Home X axis
    {% endif %}
    M109 S145                               # Set nozzle to 145 so any remaining filament stuck to nozzle is softened
    G28 Z                                   # Home Z
    CARTOGRAPHER_CALIBRATE SPEED=2          # Re-Calibrate incase build plate changes
    Z_TILT_ADJUST                           # Ensure bed is level
    G28 Z                                   # Re-home Z again now that the bed is level
    M109 S0                                 # Turn off hotend
    {% if k|int==1 %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=kamp
        BED_MESH_PROFILE LOAD=kamp
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"kamp"'
    {% else %}
        BED_MESH_CALIBRATE RUNS=2 PROFILE=default
        BED_MESH_PROFILE LOAD=default
        SAVE_VARIABLE VARIABLE=profile_name VALUE='"default"'
    {% endif %}
    CARTOGRAPHER_TOUCH SPEED=2 FUZZY=10 
```


Finally, remove the following lines to prevent the old Z_offset variable from getting saved.

```diff
PRINT_END
[gcode_macro PRINT_END]
gcode:
-    {% if printer.gcode_move.homing_origin.z < 0.5 %}
-       SAVE_VARIABLE VARIABLE=z_offset VALUE={printer.gcode_move.homing_origin.z}
-    {% endif %}
```

```diff
[gcode_macro CANCEL_PRINT]
- save_zoffset
```

#### saved_variables.cfg 

Inside `saved_variables.cfg` we need to set `z_offset = 0.0` as this is now handled by Cartographer.

#### carto.cfg

Create a new file in your config folder called `carto.cfg`. Copy and paste the contents of [this](./carto.cfg) into the new file. Save and close. 

Open `printer.cfg` and at the top under the last include, write `[include carto.cfg]`. Save and restart.

This file is where we are storing all the changes to printer.cfg that Carto needs to work. You need to modify a few values in this file to get your carto to work for your setup.

#### [mcu scanner]

#### USB Serial

`serial: /dev/serial/by-id/[your carto here]`

Find this by running `ls /dev/serial/by-id/*` in SSH. It should output something like: `/dev/serial/by-id/usb-Cartographer_614e_XXXXXXXXXXXXXXXXXXXXXXXXXXX`

#### X Y Offset

These should be provided from the maker of the mount you are using. The distance in X and Y from the center of the coil to the center of the nozzle.

`x_offset: 0  `

`y_offset: 15 `

#### [z_tilt]

Depending on your mount's X and Y offset to the nozzle, you need to update the z tilt points so it measures over the lead screws.

The values below are correct if you are using Spooknik's side mount.

```
points:
    0,171.6 # Adjust based on Y X offset
    255,171.6 # Adjust based on Y X offset
```

#### [bed_mesh]

Similar to z_tilt you need adjust the mesh_min and mesh_max to match your probe's offset. 

The values below are correct if you are using Spooknik's side mount.

```
mesh_min: 22, 45 # Adjust based on Y X offset
mesh_max: 295, 295 # Adjust based on Y X offset
```

#### Finishing up

Now you should have everything set up and you are now ready to follow Cartographer's guide for [calibration](https://docs.cartographer3d.com/cartographer-probe/installation-and-setup/installation/calibration).
