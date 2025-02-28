# CLEAR_NOZZLE With Conditional Purging and Wiping


```
[gcode_macro _MOVE_TO_CHUTE]
description: Safely move nozzle over the purge chute if not already there
gcode:
    M400
    {% if (printer.gcode_move.position.x) != 95 %}
        {% if (printer.gcode_move.position.y) != 324 %}
            {% if (printer.gcode_move.position.x) < 56 %}
                G1 X56 F12000           # Move to avoid collision with stepper motor
                M400
            {% endif %}
            {% if (printer.gcode_move.position.y) != 310 %}
                G1 Y310 F12000          # Move to avoid collision with purge activation arm
                M400
            {% endif %}
            {% if (printer.gcode_move.position.x) > 56 %}
                G1 X56 F12000           # Move in line with silicon scrubbing brush
                M400
            {% endif %}
            G1 Y324 F600                # Slowly move back in line with purge chute
            G1 X95 F600                 # Move directly over the purge chute
            M400                        # Wait for all operations to complete
        {% endif %}
    {% endif %}

[gcode_macro _ACTIVATE_PURGE_EJECTION]
description: Activate purge arm to drop purged filament down chute
gcode:
    _MOVE_TO_CHUTE
    M106 S255
    G4 P5000
    M104 S140
    G1 Y318 F9000
    G1 Y322 F600
    G1 Y318 F9000
    G1 Y322 F600
    G1 Y308 F30000
    G1 Y324 F600

[gcode_macro _PURGE_INTO_CHUTE]
description: Purge Filament into purge chute
gcode:
    _MOVE_TO_CHUTE
    G92 E0                              # Set extruder position to 0
    G1 E5 F50                           # Purge 5mm of filament slowly
    G92 E0                              # Set extruder position to 0
    G1 E80 F200                         # Purge 80mm of filament at 2mm/s
    G92 E0                              # Set extruder position to 0
    G1 E-2 F200                         # Perform a 2mm retraction
    _ACTIVATE_PURGE_EJECTION            # Eject the purged filament
    G1 E-1                              # Perform a 1mm retraction

[gcode_macro _PEI_WIPE]
description: Wipe nozzle over PEI Plate
gcode:
    _MOVE_TO_CHUTE
    G1 X124
    G1 X133 F200
    G1 Y321 F200
    G2 I0.5 J0.5 F600
    G2 I0.5 J0.5 F600
    G2 I0.5 J0.5 F600

    G1 Y319 F150
    G1 X132 
    G1 Y324
    G1 X131 
    G1 Y319
    G1 X130
    G1 Y324
    G1 X129
    G1 Y319

    G1 X113 F200
    G1 Y320
    G1 X125
    G1 X113
    G1 X125
    G2 I0.5 J0.5 F200
    G2 I0.5 J0.5 F200
    G2 I0.5 J0.5 F200
    M400

[gcode_macro _BRUSH_WIPE]
description: Wipe nozzle over Silicone Brush area
gcode:
    _MOVE_TO_CHUTE
    G1 Y300 F600
    G1 X95 F12000
    G1 Y314 F9000
    G1 Y324 F600

    G1 X58 F12000
    G1 X78 F12000
    G1 Y324
    G1 X58 F12000
    G1 X78 F12000
    G1 Y323.5
    G1 X58 F12000
    G1 X78 F12000
    G1 Y323
    G1 X58 F12000
    G1 X78 F12000
    G1 Y322.5
    G1 X58 F12000
    G1 X78 F12000
    G1 Y322
    G1 X58 F12000
    G1 X75 F12000
    G1 Y321.5
    G2 I0.8 J0.8 F600
    G2 I0.8 J0.8 F600
    G2 I0.8 J0.8 F600
    G1 Y324 F600
    
    M106 S0

    G1 X95 F12000
    G1 Y316 F9000
    G1 Y312 F600
    M400

# Specialized for power lose recovery
[gcode_macro CLEAR_NOZZLE_PLR]
description: Specialised Nozzle Clean after power loss
gcode:
    {% set hotendtemp = params.HOTEND|default(250)|int %}
    {% if (printer.gcode_move.position.z ) < 35 %}
        G1 Z35 F900
    {% else %}
        G91
        G1 Z{5} F900 
        G90
    {% endif %}

    _MOVE_TO_CHUTE

    M106 S0
    M109 S{hotendtemp}

    G92 E0
    G1 E5 F50
    G92 E0
    G1 E80 F200
    G92 E0
    G1 E-2 F200
    G4 P300

    M106 S255
    G1 Y316 F30000
    G1 Y320 F3000
    G1 Y316 F30000
    G1 Y320 F3000
    G1 Y316 F30000
    G1 Y320 F3000
    G1 Y316 F12000
    G1 Y312 F600

[gcode_macro CLEAR_NOZZLE]
description: Clear Nozzle of any stuck filament
gcode:
    {% set hotendtemp = params.HOTEND|default(250)|int %}
    {% set purge = params.PURGE|default(0)|int %}
    {% set pei_wipe = params.PEI_WIPE|default(0)|int %}

    {% if (printer.gcode_move.position.z ) < 35 %}
        G1 Z35 F900
    {% else %}
        G91
        G1 Z{5} F900 
        G90
    {% endif %}

    _MOVE_TO_CHUTE

    M106 S0                                             # Turn off part cooling fan
    M109 S{hotendtemp}                                  # Wait for nozzle to reach full temperature
    {% if purge == 1 %}
        _PURGE_INTO_CHUTE                               # Hotend temp is set to 140 after this call
    {% else %}
        _ACTIVATE_PURGE_EJECTION                        # Hotend temp is set to 140 after this call
    {% endif %}
    TEMPERATURE_WAIT SENSOR=extruder MAXIMUM={170}

    # Wipe Nozzle over the PEI plate
    {% if pei_wipe == 1 %}
        _PEI_WIPE
    {% endif %}

    # Wipe Nozzle using silicon brush
    _BRUSH_WIPE
    M118 Nozzle cleared

    # Safely move nozzle to park position at back left 
    G1 Y300 F12000
    M400
    G1 X10 F12000

    # Cool hotend down
    M106 S255
    M104 S140
    TEMPERATURE_WAIT SENSOR=extruder MAXIMUM={150}
    M106 S0
    M400
    M118 Nozzle cooled
```
