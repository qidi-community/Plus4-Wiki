# Stew's Beacon Contact Installation Guide and configuration settings

Note that all these configurations relate ONLY to using the Beacon in Contact mode.

## Quick Summary Guide

If you're an experienced Beacon user, or generally know what you're doing with Klipper, then you can
generally just follow the Beacon official guide here: https://docs.beacon3d.com/quickstart/
and the Beacon Contact guide here: https://docs.beacon3d.com/contact/


### Physical Preparation

Print out my mounting model here: https://www.printables.com/model/1170120-beacon3d-mount-for-qidi-plus4

Install the mounting module along with the Beacon attached.  Route the beacon's cable to the mainboard.
The beacon appears to have no issues when plugged into one of the USB2 ports on the mainboard.

### Install the Beacon software

Follow the Beacon guide here: https://docs.beacon3d.com/quickstart/#3-install-beacon-module

### Klipper script changes

As a word of encouragement, during the installation process

On your printer, edit the `/home/mks/klipper/klipper/extras/probe.py` file and comment out the lines as highlighted here:
https://github.com/QIDITECH/klipper/blob/PLUS4/klippy/extras/probe.py#L485-L492

Then save the file, and then power-cycle your printer.  This disables the Z-vibrate functionality that is incompatible with Beacon.


### printer.cfg changes

Edit your `printer.cfg` file.  When in doubt, check out my copy of my full [printer.cfg](./printer.cfg) for reference.

- In `[stepper_z]` check that `endstop_pin:` is set to `probe:z_virtual_endstop`.  It should already be so on the Plus4
- Set `homing_retract_dist` to 0 on all of your steppers
- Comment out the `[smart_effector]`, `[force_move]`, `[safe_zhome]` and `[qdprobe]` sections in `printer.cfg` in their entirety
- Add the following section:

```
[beacon]
serial: /dev/serial/by-id/usb-Beacon_Beacon_RevH_<**INSERT-YOUR-BEACON-SERIAL-HERE**>
x_offset: 0                     # update with X offset from nozzle on your machine
y_offset: -18.8                 # update with Y offset from nozzle on your machine
mesh_main_direction: x
mesh_runs: 2
contact_max_hotend_temperature: 180
home_xy_position: 152, 152      # update with your safe Z home position
home_z_hop: 5
home_z_hop_speed: 30
home_xy_move_speed: 300
home_y_before_x: False
home_method: contact
home_method_when_homed: proximity
home_autocalibrate: unhomed
home_gcode_pre_x: BEACON_HOME_PRE_X
home_gcode_post_x: BEACON_HOME_POST_X
home_gcode_pre_y: BEACON_HOME_PRE_Y
home_gcode_post_y: BEACON_HOME_POST_Y
```

On an ssh command shell to the printer, run `ls /dev/serial/by-id/usb-Beacon*` to find your Beacon serial number


### gcode_macros.cfg changes

Edit `gcode_macros.cfg`

