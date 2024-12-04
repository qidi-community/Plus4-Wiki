# Chamber Temperature Manager

## Add the following to your `gcode_macro.cfg` file

```
[gcode_macro MANAGE_CHAMBER_TEMP]
gcode:
    {% set target = printer['heater_generic chamber'].target %}
    {% set temperature = printer['heater_generic chamber'].temperature %}
    {% if temperature > 70 %}
        M106 P3 S255                    # Too hot! Set the chamber circulation fan to 100%
    {% else %}
        {% if temperature < target %}
            M106 P3 S0                    # Disable Chamber Circulation Fan
        {% else %}
            {% set speed = ([(temperature - target) * 50, 255] | min) | int %}
            M106 P3 S{speed}
        {% endif %}
    {% endif %}
```
