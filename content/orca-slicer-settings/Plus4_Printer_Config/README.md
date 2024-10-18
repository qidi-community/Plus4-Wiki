# Plus 4 Printer Configuration for Orca Slicer

## Basic Information Settings

![alt text](https://github.com/qidi-community/Plus4-Wiki/blob/main/content/orca-slicer-settings/Plus4_Printer_Config/Basic_Information.png "Basic Information")

## Extruder 1 Settings

![alt text](https://github.com/qidi-community/Plus4-Wiki/blob/main/content/orca-slicer-settings/Plus4_Printer_Config/Extruder.png "Extruder 1 Settings")

## Suggested Machine G-code Configurations

### Machine Start
```
PRINT_START BED=[hot_plate_temp_initial_layer] HOTEND=[nozzle_temperature_initial_layer] CHAMBER=[chamber_temperature]
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]
M83
M140 S[hot_plate_temp_initial_layer]
M104 S[nozzle_temperature_initial_layer]
G4 P3000
G0 X{max((min(print_bed_max[0] - 12, first_layer_print_min[0] + 80) - 85), 0)} Y{max((min(print_bed_max[1] - 5, first_layer_print_min[1] + 80) - 85), 0)} Z5 F6000
G0 Z[initial_layer_print_height] F600
G1 E3 F1800
G1 X{(min(print_bed_max[0] - 12, first_layer_print_min[0] + 80))} E{85 * 0.5 * initial_layer_print_height * nozzle_diameter[0]} F3000
G1 Y{max((min(print_bed_max[1] - 5, first_layer_print_min[1] + 80) - 85), 0) + 2} E{2 * 0.5 * initial_layer_print_height * nozzle_diameter[0]} F3000
G1 X{max((min(print_bed_max[0] - 12, first_layer_print_min[0] + 80) - 85), 0)} E{85 * 0.5 * initial_layer_print_height * nozzle_diameter[0]} F3000
G1 Y{max((min(print_bed_max[1] - 5, first_layer_print_min[1] + 80) - 85), 0) + 85} E{83 * 0.5 * initial_layer_print_height * nozzle_diameter[0]} F3000
G1 X{max((min(print_bed_max[0] - 12, first_layer_print_min[0] + 80) - 85), 0) + 2} E{2 * 0.5 * initial_layer_print_height * nozzle_diameter[0]} F3000
G1 Y{max((min(print_bed_max[1] - 5, first_layer_print_min[1] + 80) - 85), 0) + 3} E{82 * 0.5 * initial_layer_print_height * nozzle_diameter[0]} F3000
G1 X{max((min(print_bed_max[0] - 12, first_layer_print_min[0] + 80) - 85), 0) + 3} Z0
G1 X{max((min(print_bed_max[0] - 12, first_layer_print_min[0] + 80) - 85), 0) + 6}
G1 Z1 F600
SET_PRINT_STATS_INFO CURRENT_LAYER=1
```

### Machine End
```
M141 S0
M104 S0
M140 S0
G1 E-3 F1800
G0 Z{min(max_print_height, max_layer_z + 3)} F600
G0 X15 Y290 F12000
G4 P2000
TIMELAPSE_TAKE_FRAME
G4 P2000
{if max_layer_z < max_print_height / 2}G1 Z{max_print_height / 2 + 10} F600{else}G1 Z{min(max_print_height, max_layer_z + 3)}{endif}
```

### Layer Change
```
G92 E0
SET_PRINT_STATS_INFO CURRENT_LAYER={layer_num + 1}
```

### Time Lapse
```
TIMELAPSE_TAKE_FRAME
```

### Pause
```
M0
```
