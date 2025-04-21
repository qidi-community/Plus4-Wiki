# Enabling SCREWS_TILT_CALCULATE

The `SCREWS_TILT_CALCULATE` macro allows you to use the accuracy of your printer's inductive probe to adjust each corner of the bed during the tramming process. 
Similar to the built in calibration, which places the nozzle directly above each corner's bed leveling screw, this macro will place the inductive probe over each screw instead.

Using your inductive probe's precision will allow a more accurate bed tramming to the gantry and subsequently a flatter printing surface.
This also allows klipper to tell you exactly how much each screw will need to be turned, and in which direction to achieve this. 

## Installation

Copy the contents of the file [here](https://github.com/qidi-community/config-xplus4/blob/main/screws-tilt-calculate.cfg) into your printer.cfg (somewhere in the middle will do). Restart the printer.

> [!TIP]
> In firmware 1.6 there already is a commented entry `[screws_tilt_adjust]`, just search and replace that.

## How to use the Macro

Home your printer, using Fluidd or the display on the printer, then run this command in the Console section:

`SCREWS_TILT_CALCULATE`

![image](https://github.com/user-attachments/assets/6993554b-383b-4855-9847-291efb51f954)

The printer will probe each corner of the bed and then display a popup like this: 

![image](https://github.com/user-attachments/assets/27722936-8ce3-4062-b7e4-33463361283e)

The most important values are on the left side and in green or red. The numbers are the amount of difference between that bed screw and the `base` bed screw. Note the icon infront of each number is either an arrow point clockwise or counter-clockwise. This is the direction you must turn the bed screw to adjust it.

> [!NOTE]
> This means turning the bed screw left and right while being at the side of the door, looking down.

The numbers are in the hour:minute format, where 1 hour is 360 degrees, a full turn. For example 00:15 means you would need to turn the screw one quarter turn. 

Adjust all the values in red and press `Retry` until all the values are in green. 

Lock down the nuts under the bed screw knobs

Done! You can check your work by doing a full bed mesh calibrate. 
