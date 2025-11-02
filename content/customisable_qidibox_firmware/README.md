# A modified replacement set of firmware files and customisable QidiBox macros for the Qidi Plus 4

## Disclaimer

All of the work here is very strongly a Work In Progress.  If you wish to use it, please accept that this is provided with no guarantees.

#  What is this?

The following moves a significant portion of the QidiBox filament changing, purging, and cleaning out of the obfuscated `*.so` files that the QidiBox firmware ships with, and into a single gcode macro config file that can be easily edited to modify the behaviour of the g-code macros.  Additionally more generic filament change macros are added that allows for the QidiBox to be used with OrcaSlicer (tested), QidiStudio (tested), BambuStido (untested) and PrusaSlicer (maybe?)

## Patching Qidi Plus 4 firmware

Using an SSH shell to the printer, perform the following changes:

The following files may be used to replace their `*.so` equivalents in the `/home/mks/klipper/klippy/extras/` directory

- [/home/mks/klipper/klippy/extras/aht20_f.py](./aht20_f.py)
- [/home/mks/klipper/klippy/extras/box_detect.py](./box_detect.py)
- [/home/mks/klipper/klippy/extras/box_extras.py](./box_extras.py)
- [/home/mks/klipper/klippy/extras/box_rfid.py](./box_rfid.py)
- [/home/mks/klipper/klippy/extras/box_stepper.py](./box_stepper.py)
- [/home/mks/klipper/klippy/extras/buttons_irq.py](./buttons_irq.py)

Now move/backup the corresponding `*.so` files out of the same directory to somewhere safe where they won't be picked up by the Klipper firmware. After this, you can use the following commands to overwrite them:

```
cd ~/klipper/klippy/extras/

sudo rm -f aht20_f.so box_detect.so box_extras.so box_rfid.so box_stepper.so buttons_irq.so

wget https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/customisable_qidibox_firmware/aht20_f.py

wget https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/customisable_qidibox_firmware/box_detect.py

wget https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/customisable_qidibox_firmware/box_extras.py

wget https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/customisable_qidibox_firmware/box_rfid.py

wget https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/customisable_qidibox_firmware/box_stepper.py

wget https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/customisable_qidibox_firmware/buttons_irq.py

```

##  Restore missing macros

If you're planning to use the Qidi Box, you may experience some unexpected behaviour when using a `gcode_macro.cfg` file from versions 1.7.1 or above. This happens because some of the gcode macros used in certain box operations (for example, during print start or when resuming a paused print) were moved from `gcode_macro.cfg` to macros inside the `.so` files that were replaced in a previous step.

As a result, you may have some macros being called that aren't defined anywhere. Currently, the affected macros are `BOX_PRINT_START`, `EXTRUSION_AND_FLUSH` and `TRY_RESUME_PRINT`.

A way to fix this issue is to add the following macros to your `gcode_macro.cfg`. These are [ports of the code from 1.7.0](https://github.com/QIDITECH/QIDI_PLUS4/commit/ec595fc903540564be757bcafa745cd5c4a52cd0#diff-a9e221ad0df9e5f2e8b8496842d5618351303699fc7c51c6849e6db26ab7d3d2) that was removed by the `.so` macros.

> [!WARNING]
>  It is possible that `EXTRUSION_AND_FLUSH` is already defined in your `gcode_macro.cfg` file. Double check that you aren't creating duplicate gcode_macro definitions!

```

```


## Adding the new customisable macros 

Using the FLUIDD Web UI, add in the following [box_macros.cfg](./box_macros.cfg) file into the same directory as your `printer.cfg` file

Then edit your printer.cfg and add in the following line below the existing `[include box.cfg]` line:

```
[include box_macros.cfg]
```

Now click `SAVE & RESTART`

> [!WARNING]
>  It is possible that some macros (for example, `EXTRUSION_AND_FLUSH`) are already defined in your `gcode_macro.cfg` file. Double check that you aren't creating duplicate gcode_macro definitions!

After the printer has restarted (hopefully no errors show up - if they do, address them), then you will need to power-cycle the printer to activate the new firmware changes.

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
