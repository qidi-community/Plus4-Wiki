# Square Corner Velocity Tweak

The following tweaks are intended to improve the quality of prints on the Qidi Plus 4

## Editing printer.cfg

To edit your `printer.cfg` file, this can typically be done through the FluiddUI Web Page to the printer under the `Configuration` tab.
Find the file named `printer.cfg` and click on it
When done editing, press the `SAVE & RESTART` button in the FluiddUI

This is needed as the Klipper version that ships with the Plus 4 tunes its input shapers around the assumption that square corner velocity is always set to 5.

## Per Section Changes

For each of the mentioned configuration sections within your `printer.cfg` file, find the named fields and change the associated value to the newly specified value.

```
[printer]
square_corner_velocity: 5
```
