# Chamber Heater Issue

## Description

This problem only affects **prints taller than 260mm** when printing with materials that require the chamber heater to be enabled.

The hot air exhaust of the chamber heater exits into the main chamber towards the very bottom of the left side of the chamber.

Unfortunately the print bed, when at Z heights of 260mm and greater will increasingly block off the chamber heater's outlet when the heater is active.
This can lead to a thermal event being triggered by Klipper, resulting in Klipper shutting the firmware down immediately and ruining any print in progress.

A true fix for this issue would require Qidi to come up with a hardware fix that does not result in the print bed blocking the outlet of the chamber heater when the print bed is near the very bottom of the chamber.

The following is a software workaround that attempts to mitigate the issue pending a true hardware fix.

## A software workaround

While the following does not fix the fundamental hardware flaw in the printer's design, it does attempt to mitigate its impact.
The following configuration will shut down the chamber heater whenever the print bed is in the last 20mm of travel (ie. at a Z height of 260mm or more).

The idea here is to disable the heater and complete the last 20mm of Z travel printing by "coasting" on the latent heat within the chamber and the heat still being supplied by the print bed.  While this is not a true fix, it will at least mitigate the firmware shutdown issue and MAY still allow the print to complete successfully.

Within the `gcode-macro.cfg` file we can add in the following macro:

```

[gcode_macro SET_PRINT_STATS_INFO]
rename_existing: SET_PRINT_STATS_INFO_BASE
gcode:
    {% set curlayer =  params.CURRENT_LAYER|default(1)|int %}
    {% if (printer.toolhead.position.z) > 268 %}
        M141 S0
    {% endif %}
    SET_PRINT_STATS_INFO_BASE CURRENT_LAYER={curlayer}

```

This will call the macro upon every layer change (as this command is called on every layer change in all stock printing profiles), and when the Z height exceeds 260mm, the chamber heater will be disabled.
This should prevent the chance for a thermal shutdown event being triggered by the chamber heateral, and leave the chamber to coast on existing heat. 
