# Enabling Screws_TILT_ADJUST

The Screws_Tilt_Adjust macro allows you to use the accuracy of your printer's inductive probe to adjust each corner of the bed during the tramming process. 
Similar to the built in calibration, which places the nozzle directly above each corner's bed leveling screw, this macro will place the inductive probe over each screw instead.

Using your inductive probe's precision will allow a more accurate bed tramming to the gantry and subsequently a flatter printing surface.
This also allows klipper to tell you exactly how much each screw will need to be turned, and in which direction to achieve this. 

# Printer.cfg Changes
On stock, the [screws_tilt_adjust] section is commented out and does not have the necessary screw locations.
Unfortunately, sdding in the locations from [BED_SCREWS] directly will not work as this places the nozzle over the desired area and not the inductive probe which could result in a potential nozzle crash

Using the x and y stock nozzle offset for the inductive probe:
x_offset: 25
y_offset: 1.3

and the screw locations from [Bed_Screws] we can get the required coordinates

## Printer.cfg Changes
In printer.cfg, replace

#[screws_tilt_adjust] <br>
#screw_thread: CM-M4

with:
```
[screws_tilt_adjust]
screw1:0,19.7
screw1_name: Front left
screw2: 260,19.7
screw2_name: Front right
screw3: 260,279.7
screw3_name: Last right
screw4: 0,279.7
horizontal_move_z: 10.
speed: 50.
screw_thread: CW-M4
```

## How to use the Macro

Home your printer then run 

Z_TILT_ADJUST

Once finished type

SCREWS_TILT_CALCULATE

 into your console and follow the directions on adjusting each screw either clock-wise or counter clockwise. The direction is based from looking at the screws from above. 
