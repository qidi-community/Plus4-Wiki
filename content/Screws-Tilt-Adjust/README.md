# Enabling SCREWS_TILT_CALCULATE

The `SCREWS_TILT_CALCULATE` macro allows you to use the accuracy of your printer's inductive probe to adjust each corner of the bed during the tramming process. 
Similar to the built in calibration, which places the nozzle directly above each corner's bed leveling screw, this macro will place the inductive probe over each screw instead.

Using your inductive probe's precision will allow a more accurate bed tramming to the gantry and subsequently a flatter printing surface.
This also allows klipper to tell you exactly how much each screw will need to be turned, and in which direction to achieve this. 

## Installation

The [config-xplus4](https://github.com/qidi-community/config-xplus4/tree/main) repo contains the most up to date version of the `screws-tilt-calculate.cfg`. Please follow the install process outlined there to get this macro up and running. 

Note that the installation process for config-xplus4 installs more than just the `SCREWS_TILT_CALCULATE` macro. If you do not want to install other patrst of the config follow the installation guide but when it is complete, edit your `printer.cfg` file and replace the line added by config-xplus4 with a more specific version. The default installation adds the following line towards the end of your printer.cfg:

`[include config-xplus4/*.cfg]`

You can edit this to only include the `SCREWS_TILT_CALCULATE` macro i.e.:

`[include config-xplus4/screws-tilt-calculate.cfg]`


## How to use the Macro

Home your printer then run 

`SCREWS_TILT_CALCULATE`

The printer will probe each corner of the bed and then display a popup like this: 

![image](https://github.com/user-attachments/assets/27722936-8ce3-4062-b7e4-33463361283e)

The most important values are on the left side and in green or red. The numbers are the amount of difference between that bed screw and the `base` bed screw. Note the icon infront of each number is either an arrow point clockwise or counter-clockwise. This is the direction you must turn the bed screw to adjust it. 

The numbers are in the hour:minute format. For example 00:15 means you would need to turn the screw one quarter turn. 

Adjust all the values in red and press `Retry` until all the values are in green. 

Lock down the nuts under the bed screw knobs

Done! You can check your work by doing a full bed mesh calibrate. 
