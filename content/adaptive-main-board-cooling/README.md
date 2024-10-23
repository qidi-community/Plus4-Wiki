# Adaptive Main Board Cooling Configuration

By default, the main board cooling fan is only active/on when the X/Y stepper motors are active (ie. during printing).
While this ensures that the printer makes less noise during idle times when not printing, it does allow for the main
CPU and various components on the main board to get extremely warm.

The following configuration change alters this behaviour.  Instead the mainboard cooling fan will always be active, but
at a very low speed during idle times to ensure that the mainboard and CPU don't get overly warm.  When the CPU rises
above a certain set temperature (45C) then the main-board cooling fan speed will be ramped up to try to keep temperatures
stable.

**Note:**  While the below configuration change works well with the stock 40mm fan, it is highly recommended to swap out
the stock main-board fan and its mainboard cover with an 80mm fan, and a 3D printed mainboard cover that allows for the
use of the 80mm fan.
This ensures that the mainboard, CPU, and steppers drivers are kept cool during both idle times, and when in operation,
while keeping fan noise to a minimum.


## Editing printer.cfg

To edit your `printer.cfg` file, this can typically be done through the FluiddUI Web Page to the printer under the `Configuration` tab.
Find the file named `printer.cfg` and click on it
When done editing, press the `SAVE & RESTART` button in the FluiddUI


## Per Section Changes

For each of the mentioned configuration sections within your `printer.cfg` file, find the named fields and change the associated value to the newly specified value.

First find the `[controller_fan board_fan]` section and comment it out like so:

```
#[controller_fan board_fan]
#pin:U_1:PC4
#max_power:1.0
#shutdown_speed:1.0
#cycle_time:0.01
#fan_speed: 1.0
#stepper:stepper_x,stepper_y
```
There have been reports of later firmware versions having additional lines to the above `[controller_fan board_fan]` example.
These should also be commented out if they appear in your configuration.  ie. the entire `[controller_fan board_fan]` section
should be commented out.


Now add the following configuration below the commented out section:

```
[temperature_fan board_fan]
pin:U_1:PC4
max_power: 1.0
shutdown_speed: 1.0
cycle_time: 0.01
off_below: 0
sensor_type: temperature_host
control: pid
pid_deriv_time: 2.0
pid_Kp: 5
pid_Ki: 2
pid_Kd: 5
target_temp: 45
min_speed: 0.3
max_speed: 1.0
min_temp: 0
max_temp: 100
```
