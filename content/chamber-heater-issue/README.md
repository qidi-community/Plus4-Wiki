# Chamber Heater Issue

## Description

This problem only affects **prints taller than 268mm** when printing with materials that require the chamber heater to be enabled.

The hot air exhaust of the chamber heater exits into the main chamber towards the very bottom of the left side of the chamber.

Unfortunately the print bed, when at Z heights of 268mm and greater will increasingly block off the chamber heater's outlet when the heater is active.
This can lead to a thermal event being triggered by Klipper, resulting in Klipper shutting the firmware down immediately and ruining any print in progress.

A true fix for this issue would require Qidi to come up with a hardware fix that does not result in the print bed blocking the outlet of the chamber heater when the print bed is near the very bottom of the chamber.

## A firmware configuration workaround

**NOTE:**  While the following does not fix the fundamental hardware flaw in the printer's design, it does essentially nullify its impact.

The following configuration will disable the chamber heater's coils whenever the print bed is at a Z height of 268mm or greater.
The idea here is to disable the heater coils and then complete the remainder of the print using the latent heat within the chamber **and** by making best possible use of the heating element of the print bed.
This will mitigate the firmware shutdown issue and, in almost all reasonable scenarios, will allow the print to complete successfully.

Within the `gcode-macro.cfg` file we can add in the following macro:

```

[gcode_macro SET_PRINT_STATS_INFO]
rename_existing: SET_PRINT_STATS_INFO_BASE
gcode:
    {% set curlayer =  params.CURRENT_LAYER|default(1)|int %}
    {% if (printer.toolhead.position.z) >= 268 %}
        # Set chamber target to 10C, which still keeps the chamber heater fan on
        # This allows the print bed to warm the chamber more effectively even
        # though the heater coils are effectively disabled
        M141 S10
    {% endif %}
    SET_PRINT_STATS_INFO_BASE CURRENT_LAYER={curlayer}

```

This will call the macro upon every layer change (as this command is called on every layer change in all stock printing profiles).
When the Z height exceeds 268mm, the chamber heater target will be set to 10C.

**The target of 10C is important here, instead of using a 0C target.**

Using a 10C target will keep the chamber heater's fan spinning, which will still help to circulate some air under the print bed,
and this will in turn help to keep the chamber warm as the print bed warms the air-flow under it.

Doing this will prevent the chance for a thermal shutdown event being triggered by the chamber heater, and will keep the chamber warm for the remainder of the print.

## Additional Safety Configurations

### Setting the chamber_fan shutdown_speed

In addtion, for added safety the chamber heater fan can be set to run even if the printer does shut down due to the chamber heater overheating.
This can be done by modifying the following in `printer.cfg`:

```
[chamber_fan chamber_fan]
shutdown_speed: 1 
```

### Setting the chamber_heater power to 0.5 (instead of 0.7)

Qidi's stock PWM power setting for the chamber heater is too aggressive and has been known to cause the Chamber Thermal Protection Sensor to trip.
This has been seen to result in a firmware shutdown even in normal operation when a print is first starting to warm the chamber up.

Making the following config change will prevent this from happening.

Additionally, setting a lower `max_power` value here will also help protect the SSR unit from potentially failing in 110VAC countries as reports
of this for the first batch of Plus4 printers have started to surface somewhat frequently within the first month of customer use.

Find the `[heater_generic chamber]` section within the `printer.cfg` file, and then find the line starting with `max_power`, and set its value to `0.5`.

For example:
```
[heater_generic chamber]
max_power:0.7
```

Should be replaced with:

```
[heater_generic chamber]
max_power: 0.5
```

Note that while the chamber will take a little longer to reach a target temperature, it should still reach the target temperature before
the print bed reaches it own target in almost all reasonable scenarios.

