# Stepper Motor Tweaks

The following tweaks are intended to improve the accuracy of the stepper motor movements on the Qidi Plus 4

## Editing printer.cfg

To edit your `printer.cfg` file, this can typically be done through the FluiddUI Web Page to the printer under the `Configuration` tab.
Find the file named `printer.cfg` and click on it
When done editing, press the `SAVE & RESTART` button in the FluiddUI


## Per Section Changes

For each of the mentioned configuration sections within your `printer.cfg` file, find the named fields and change the associated value to the newly specified value.
Please ensure that all `hold_current` configurations in your `printer.cfg` file are commented out.
They usually are by default, but this is essential for the best print quality.

**ATTENTION!**

Some of the following configuration changes raise the stock stepper motor `run_current` values by around 5%.
While this does improve the strength of stepper motor actions, it will also cause the stepper motors and TMC drivers to run a little warmer.

If you do not wish to push more current through your stepper motors and drivers then omit any `run_current` changes to your `printer.cfg` file.
Without a boosted `run_current` the printer will work just fine with the rest of these settings, but I personally like to raise the `run_current` because it minimises the chance of layer shifts.

Additionally, before raising the stock `run_current` values, it is strongly encouraged to improve the mainboard cooling by using a larger fan on the mainboard cover.

```
[extruder]
microsteps: 64

[tmc2209 extruder]
interpolate: False
run_current: 0.8
stealthchop_threshold: 0

[stepper_x]
microsteps:32

[stepper_y]
microsteps: 32

[stepper_z]
microsteps: 16

[stepper_z1]
microsteps: 16

[tmc2240 stepper_y]
run_current: 1.15
interpolate: False
stealthchop_threshold:0

[tmc2240 stepper_x]
run_current: 1.15
interpolate: False
stealthchop_threshold:0

[tmc2209 stepper_z]
run_current: 1.15
interpolate: False
stealthchop_threshold: 999999

[tmc2209 stepper_z1]
run_current: 1.15
interpolate: False
stealthchop_threshold: 999999
```
