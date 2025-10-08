# Adaptive chamber heater fan configuration

You ever think to yourself "Man, this fan sure is loud!"? I have. This mod makes the fan in the chamber heater adapt to the temperature of the heater, and maintain the temperature at comfortable 70C.

> [!IMPORTANT]
> This mod can potentially result in your chamber heater fan dying if your Chamber Tempreature Protection Sensor is not working properly. I cannot be held responsible for parts, and qidi is likely to deny a warranty request for a new chamber fan if you run this mod.

> [!NOTE]
> Tested with firmware 1.6.0 and 1.7.0, should work with any version older than 1.7.3

## Compatibility
This mod is compatible with [Dynamic Chamber Temperature Manager](../chamber-temperature-manager/README.md), [Warming the Chamber Faster!](../tuning-for-40-percent-heater-power/README.md), and other chamber-related mods on this wiki, including [aftermarket SSRs](../heater-ssr-upgrade/README.md), beacon/cartographer etc. 

## Instructions
In fluidd, edit the `printer.cfg` configuration file. Roughly 2/3rds of the way down, there will be a section about the chamber fan. You can also hit Ctrl-F and search for `chamber_fan`.
Comment that definition out like so:
```text
# [chamber_fan chamber_fan]
# pin:U_1:PA4
# max_power: 1.0
# shutdown_speed: 1.0
# kick_start_time: 0.5
# heater:chamber
# fan_speed: 1.0
# off_below: 0
# idle_timeout:300
# idle_speed:1.0
```

> [!TIP]
> If using github, there will be a button in the top right of a code block (like the one below and above this tip), and hitting that button would copy the block's content into your copy-paste buffer.

and insert the new *adaptive* definition right after:
```text
[temperature_fan adaptive_chamber_fan]
pin:U_1:PA4
max_power: 1.0
shutdown_speed: 1.0
kick_start_time: 0.5
off_below: 0.1
sensor_type: temperature_combined
sensor_list: temperature_sensor Chamber_Thermal_Protection_Sensor, temperature_sensor Chamber_Thermal_Protection_Sensor
combination_method: max
maximum_deviation: 999
min_speed: 0
max_speed: 1.0
min_temp: 0
max_temp: 140
target_temp: 70
control: pid
pid_deriv_time: 10.0
pid_Kp=12
pid_Ki=12
pid_Kd=5
```

Restart the printer by clicking "firmware restart" on the touchscreen, or submit `"FIRMWARE_RESTART` command in the gcode-console. Done!

## Troubleshooting

#### Problem:
My fan ramps up and ramps down rapidly!

#### Solution:
In the config, reduce `pid_Kp=` number. Go in increments of 2-3. Beware - lowering this too much will make the fan dangerously slow to ramp up.

#### Problem:
I print a lot of high-temp materials and would like my fan to run harder.

#### Solution:
reduce `target_temp:` from 70 to 60 or 50.

#### Problem:
I would like to PID calibrate the fan automatically, how do I?

#### "Solution":
Klipper does not implement such functionality. I wish it did. Bad luck, sorry.
