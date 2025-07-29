# A modified replacement set of firmware files and customisable QidiBox macros for the Qidi Plus 4

## Patching Qidi Plus 4 firmware

The following files may be used to replace their `*.so` equivalents in the `/home/mks/klipper/klippy/extras/` directory

- /home/mks/klipper/klippy/extras/aht20_f.py
- /home/mks/klipper/klippy/extras/box_detect.py
- /home/mks/klipper/klippy/extras/box_extras.py
- /home/mks/klipper/klippy/extras/box_rfid.py
- /home/mks/klipper/klippy/extras/box_stepper.py

## Adding the new customisable macros 

Add in the following `box_macros.cfg` file into the same directory as your `printer.cfg` file

Edit your printer.cfg and add in the following line

```
[include box_macros.cfg]
```

## Update your slicer's Plus 4 macros

Within the `Machine start G-code` section ensure that the `PRINT_START` line has `EXTRUDER=[initial_no_support_extruder]` appended to it, such that it appears like so:

```
PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND=[nozzle_temperature_initial_layer] CHAMBER=[chamber_temperature] EXTRUDER=[initial_no_support_extruder]
```

Within the `Change filament G-code` section, replace its entire contents with the following:

```
{ if current_extruder != next_extruder }
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=max_layer_z VALUE={max_layer_z}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=flush_length_1 VALUE={flush_length_1}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=flush_length_2 VALUE={flush_length_2}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=flush_length_3 VALUE={flush_length_3}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=flush_length_4 VALUE={flush_length_4}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=current_extruder VALUE={current_extruder}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=current_filament_extrude_rate VALUE={old_filament_e_feedrate}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=current_filament_high_temp VALUE={nozzle_temperature_range_high[current_extruder]}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=current_filament_retract_length VALUE={old_retract_length_toolchange}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=next_extruder VALUE={next_extruder}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=next_filament_extrude_rate VALUE={new_filament_e_feedrate}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=next_filament_temp VALUE={new_filament_temp}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=next_filament_high_temp VALUE={nozzle_temperature_range_high[next_extruder]}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=next_filament_retract_length VALUE={new_retract_length_toolchange}
SET_GCODE_VARIABLE MACRO=BOX_CHANGE_FILAMENT VARIABLE=retraction_distance_when_cut VALUE=0
BOX_CHANGE_FILAMENT C_FILA_TYPE={filament_type[current_extruder]} N_FILA_TYPE={filament_type[next_extruder]}
{endif}
```
