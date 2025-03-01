# **Temperature Monitoring with Distinct Audible Chimes**
## **Purpose**
My routine in the morning is often to sit down with coffee, start up the Plus4, and warm the bed to heat soak it for printing. I wanted a way for the beeper installed on the mainboard to sound a tone when the target temperatures I set to pre-warm my bed and/or chamber were met, so I know it is ready without having to check the screen or watch Fluidd.

This macro enables continuous monitoring of the bed and chamber temperatures on the Plus4. It emits distinct audible chimes when the bed or chamber reaches the set target temperature:

- **Bed Chime:** Three short beeps.  
- **Chamber Chime:** Two short beeps followed by one long beep.  

The macro runs automatically at startup and operates in the background, leveraging Klipper's built-in temperature monitoring to ensure efficient performance and minimize impact on CPU and memory.

## **Features**
- **Distinct Chimes:**
  - **Bed:** Three short beeps.
  - **Chamber:** Two short beeps followed by one long beep.
- **Single Alert Per Target:** Chimes only once when a target temperature is reached and resets the macro tracking.
- **Automatic Reset:** Resets and activates tracking when a new target temperature is set.
- **Continuous Monitoring:** Runs every second without impacting printer performance.
- **Startup Integration:** Automatically starts monitoring at boot using the `delayed_gcode` feature of Klipper.

## **Setup Instructions**

### **1. Add the Macro Code**
Add the following macro to your `gcode_macro.cfg` file:

```ini
[gcode_macro ENV_BEEP]
description: "Monitor bed and chamber temperatures and play distinct chimes when targets are reached"
variable_bed_triggered: False
variable_chamber_triggered: False
gcode:
  # Set up references for bed and chamber heaters
  {% set bed = printer["heater_bed"] if "heater_bed" in printer else None %}
  {% set chamber = printer["heater_generic chamber"] if "heater_generic chamber" in printer else None %}

  # Check Bed Heater
  {% if bed is not none %}
    {% if bed.target > 0 %}
      {% if bed.temperature >= bed.target and bed_triggered == False %}
        { action_respond_info("Bed has reached target temperature: " ~ bed.target ~ "°C") }
        # Play bed chime (three short beeps)
        SET_PIN PIN=beeper VALUE=1
        G4 P200  ; Short beep
        SET_PIN PIN=beeper VALUE=0
        G4 P100  ; Pause
        SET_PIN PIN=beeper VALUE=1
        G4 P200  ; Short beep
        SET_PIN PIN=beeper VALUE=0
        G4 P100  ; Pause
        SET_PIN PIN=beeper VALUE=1
        G4 P200  ; Short beep
        SET_PIN PIN=beeper VALUE=0
        SET_GCODE_VARIABLE MACRO=ENV_BEEP VARIABLE=bed_triggered VALUE=True
      {% endif %}
    {% else %}
      # Reset if no target is set
      SET_GCODE_VARIABLE MACRO=ENV_BEEP VARIABLE=bed_triggered VALUE=False
    {% endif %}
  {% endif %}

  # Check Chamber Heater
  {% if chamber is not none %}
    {% if chamber.target > 0 %}
      {% if chamber.temperature >= chamber.target and chamber_triggered == False %}
        { action_respond_info("Chamber has reached target temperature: " ~ chamber.target ~ "°C") }
        # Play chamber chime (two short beeps and one long beep)
        SET_PIN PIN=beeper VALUE=1
        G4 P200  ; Short beep
        SET_PIN PIN=beeper VALUE=0
        G4 P100  ; Pause
        SET_PIN PIN=beeper VALUE=1
        G4 P200  ; Short beep
        SET_PIN PIN=beeper VALUE=0
        G4 P100  ; Pause
        SET_PIN PIN=beeper VALUE=1
        G4 P500  ; Long beep
        SET_PIN PIN=beeper VALUE=0
        SET_GCODE_VARIABLE MACRO=ENV_BEEP VARIABLE=chamber_triggered VALUE=True
      {% endif %}
    {% else %}
      # Reset if no target is set
      SET_GCODE_VARIABLE MACRO=ENV_BEEP VARIABLE=chamber_triggered VALUE=False
    {% endif %}
  {% endif %}
```

### **2. Add Periodic Monitoring**
Add the following `delayed_gcode` entries to your `printer.cfg` file. These ensure the macro runs every second, and periodic monitoring begins automatically at startup:

**a) Periodic Monitoring Setup**
```ini
[delayed_gcode ENV_BEEP_MONITOR]
initial_duration: 1.0  # Start monitoring 1 second after initialization
gcode:
  ENV_BEEP
  UPDATE_DELAYED_GCODE ID=ENV_BEEP_MONITOR DURATION=1.0
```
**b) Start Monitoring at Initialization
```ini
[delayed_gcode START_ENV_BEEP]
initial_duration: 1.0  # Delay start by 1 second
gcode:
  UPDATE_DELAYED_GCODE ID=ENV_BEEP_MONITOR DURATION=1.0
```
## **Save and Restart**
Save the changes to both configuration files (`printer.cfg` and `gcode_macro.cfg`).

Restart Klipper by choosing **‘SAVE & RESTART’** in Fluidd or by running the restart command in the console:
```gcode
RESTART
```
## **How It Works**
1. The macro checks the current and target temperatures of the bed and chamber heaters every second.
2. If a heater reaches its target:
- Plays a unique chime for the bed or chamber.
- Displays a message in the terminal or Fluidd/Mainsail interface.
3. Once the chime plays, it will not trigger again until a new target is set.

## **Testing the Macro**

1. **Set Target Temperatures:**

   - For the bed:
     ```gcode
     SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=60
     ```
   - For the chamber:
     ```gcode
     SET_HEATER_TEMPERATURE HEATER=chamber TARGET=40
     ```

2. **Observe the Behavior:**

   - When the bed reaches its target, you will hear three short beeps.
   - When the chamber reaches its target, you will hear two short beeps followed by one long beep.

3. **Reset the Macro:**

   - Set the target temperature back to `0` to reset the tracking:
     ```gcode
     SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=0
     SET_HEATER_TEMPERATURE HEATER=chamber TARGET=0
     ```

## **Customization Options**

1. **Chime Timing:**

   - Adjust the `P` values in the `G4` commands to modify beep duration or pause length.
   - Example: `G4 P300` for a longer beep.

2. **Monitoring Frequency:**

   - Change the `DURATION` in `[delayed_gcode ENV_BEEP_MONITOR]` to control the interval (e.g., every 2 seconds):
     ```ini
     UPDATE_DELAYED_GCODE ID=ENV_BEEP_MONITOR DURATION=2.0
     ```

3. **Disable Automatic Startup:**

   - Remove the `[delayed_gcode START_ENV_BEEP]` section if you prefer to start monitoring manually using the macro directly:
     ```gcode
     ENV_BEEP
     ```

## **Example Terminal Output**

- When the bed reaches its target:

     "//Bed has reached target temperature: 60°C"

- When the chamber reaches its target:

     "//Chamber has reached target temperature: 40°C"

