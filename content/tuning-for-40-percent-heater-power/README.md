# Tuning Chamber Heater Warmup Times

## Introduction

> [!CAUTION]
> For firmware v1.6.0 or later, you have two choices:
> 1. Don't use this warmup sequence at all.
> 2. Use the [Improved PRINT_START macro](#Improved-PRINT_START-macro) in addition to the steps detailed in [Firmware v1.6.0 - Required Steps](#firmware-v160---required-steps).

***

With the 1.4.3 Firmware Release from Qidi, the stock chamber heater power was dropped from a 70% duty cycle to a 40% duty cycle.

This now made chamber warmup times considerably slower as a result, however we can make some configuration changes to make it not so bad.

Now keep in mind that the primary point of slowness during a print start warmup was actually the print bed, and not the chamber heater warmup,
and we can use this to our advantage to improve the overall situation.

## Test Baseline

### Initial Conditions

- Room Temperature: 23C
- Starting Chamber Temperature: 23C
- Starting Print Bed Temperature: 23C

### Target Conditions

- Chamber: 60C
- Print Bed: 100C

### What are we measuring here?

It makes the most sense to measure the time elapsed between when a print is sent to the printer,
and the time when the bed meshing starts for the print.  This really is the only time that matters here.

## Test 1 - Warmup times at 70% heater power

It was observed that while the chamber temperature would reach the target within 10 minutes,
the print bed would only reach 100C after 16 minutes and 30 seconds before the bed mesh started.

## Test 2 - Warmup times at 40% heater power, stock configuration

It was observed that it took 25 minutes to the time that the bed meshing started

## Test 3 - Warmup times at 40% heater power with tuned `PRINT_START` and `M191` macros

A time of 19m30s was observed to the time that the bed meshing started.

## Improved PRINT_START macro

Change the `PRINT_START` macro within `gcode_macro.cfg` to the following in its entirety.
I've added detailed comments to (almost) every line so it is easier to understand what all
the gcode is doing.

**Note:** I recommend just commenting out the stock `PRINT_START` macro by putting a
`#` at the start of all of the original macro lines.
Then copy-paste this new macro in either before or after the original macro.
This will allow you to easily revert to the original macro should you wish to do so.

```
[gcode_macro PRINT_START]
gcode:
    {% set bedtemp = params.BED|int %}
    {% set hotendtemp = params.HOTEND|int %}
    {% set chambertemp = params.CHAMBER|default(0)|int %}

    # AUTOTUNE_SHAPERS                  # Nothing ever makes uses of this though
    # set_zoffset                       # Sample the Z offset (but why even do this now?)
    M141 S{chambertemp}                 # Initiate Chamber Warmup as early as possible
    M140 S{bedtemp}                     # Initiate Print Bed Warmup as early as possible
    M400                                # Wait for all prior G-code commands to be processed by MCU
    M104 S0                             # Make sure hotend is off
    M106 P3 S0                          # Turn off chamber circulation/exhaust fan
    M106 S255                           # Turn on part cooling fan to full speed

    {% if chambertemp > 0 %}
        M106 P2 S255                    # Set AUX to full to help mix chamber air fully
    {% else %}
        M106 P2 S0                      # Turn off auxiliary part cooling fan
    {% endif %}

    M400                                # Wait for all prior G-code commands to processed before G28
    G28                                 # Home all axes
    CLEAR_NOZZLE HOTEND={hotendtemp}    # Do nozzle purge and wipe

    {% if chambertemp > 0 %}            # Special chamber handling for fastest thorough warmup times
        M106 P0 S255                    # Ensure part cooling fan is full speed for better air mixing
        M106 P2 S255                    # Ensure AUX is at 100% after CLEAR_NOZZLE was called
        G0 Z5 F600                      # Bring print bed to Z=5mm.  This helps with chamber heating
        G0 X152 Y152 F6000              # Bring print head to middle of print bed
        M191 S{chambertemp-5}           # Wait for chamber to reach 5C less than the target temperature
        M141 S{chambertemp}             # Reset chamber target to full target
        M106 P2 S0                      # Turn off AUX Fan
        M106 P0 S0                      # Turn off part cooling fan
    {% endif %}

    G0 X5 Y5 F6000                      # Move print head to front-left in case of any oozing
    M104 S140                           # Set nozzle to 140 so any remaining filament stuck to nozzle is softened
    M190 S{bedtemp}                     # Wait for print bed to reach target temperature
    G29                                 # Perform Z-offset, and bed meshing measurements
    M104 S0                             # Ensure hotend is fully off to minimise any oozing

    {% if chambertemp == 0 %}           # No chamber temp set. This means we're likely printing PLA/PETG.
        M106 P3 S255                    # Set the chamber circulation fan to 100% to minimise heat creep
    {% endif %}

    G0 Z5 F600                          # Move plate to Z=5mm
    G0 X5 Y5 F6000                      # Move print head to front-left
    M141 S{chambertemp}                 # Ensure chamber is set to on after G29 was called earlier
    M109 S{hotendtemp}                  # Commence hotend warmup
    M204 S10000                         # Set velocity limits
    SET_PRINT_STATS_INFO CURRENT_LAYER=1
    ENABLE_ALL_SENSOR
    save_last_file
```

Additionally, in `printer.cfg` find the `[verify_heater heater_bed]` section, and change the `check_gain_time` from `60` to `360` as in the following example.
This is required because the print bed is being blasted by the fan to heat the air up faster, which means that the print bed itself heats
up more slowly.  If we don't raise this check gain time a bit, then the firmware may throw an error because it is not seeing the print
bed warm up quickly enough.

```
[verify_heater heater_bed]
max_error: 200
check_gain_time:360
hysteresis: 10
heating_gain: 1
```

### Discussion on why it works

- Some needless commands were commented out, but left in place if ever needed at a future time.
- The print bed is raised up and the auxiliary fan and print head fans are used to transfer as much heat from the print bed to the chamber air as possible
- This is basically using the print bed's heater to its fullest effect to boost the chamber heater in warming the chamber air
- The `M191` chamber wait target is lowered to 5C less than the true target meaning the chamber wait ends a bit sooner
- While Z-offset and bed-meshing takes place, the chamber continues to warm up to the target in the meantime
- The chamber is observed to be fully up to temperature by the time the actual print begins

### Additional Notes

It is **absolutely essential** that the `Activate Temperature Control` option is disabled in the filament settings in your slicer.
If this feature is active, then the slicer will instruct the printer to attempt to warm the chamber without the assistance of the print bed heater,
and there are reports that this can take up to 1 hour for the chamber to reach 60C.

![DISABLE THIS!](./disable-me.png "You REALLY don't want this enabled!")

## Firmware v1.6.0 - Required Steps

> [!CAUTION]
> Do not follow these steps if on firmware earlier than v1.6.0 !!

### Modifying heaters.py

1. SSH into the printer
2. Write a new file named `heaters.patch` with these contents:
<details open>
<summary>Patch for heaters.py</summary>

```patch
--- a/klippy/extras/heaters.py
+++ b/klippy/extras/heaters.py
@@ -234,7 +234,10 @@ class ControlPID:
         #logging.debug("pid: %f@%.3f -> diff=%f deriv=%f err=%f integ=%f co=%d",
         #    temp, read_time, temp_diff, temp_deriv, temp_err, temp_integ, co)
         bounded_co = max(0., min(self.heater_max_power, co))
-        if self.heater.name == "chamber" and heater_bed.heater_bed_state != 2 and heater_bed.is_heater_bed == 1:
+        # We add this DISABLE_BED_CHECK flag so that the chamber heater can be controlled independently of the bed heater
+        # This should not be used in normal operation with the stock piezo sensor
+        DISABLE_BED_CHECK = True
+        if self.heater.name == "chamber" and heater_bed.heater_bed_state != 2 and heater_bed.is_heater_bed == 1 and not DISABLE_BED_CHECK:
             self.heater.set_pwm(read_time, 0.)
         else:
             self.heater.set_pwm(read_time, bounded_co)
-- 
```

</details>

3. Apply the patch 
```
patch /home/mks/klipper/klippy/extras/heaters.py < /path/to/heaters.patch
```

4. If that was succesfull you will see something like `patching file heaters.py` without any further output and an exitcode of `0` (execute `echo $?`, which is the exitcode of the last executed command).

![image](https://github.com/user-attachments/assets/1ad7766f-907d-47b0-a58f-577d708bb5b0)

### Explanation

We have modified the code in heaters.py to add a `DISABLE_BED_CHECK = True` flag. 
Where normally the chamber heater does not turn on unless the bed is within 2 degrees of the target bed temp, we ignore this using our new flag.

Set `DISABLE_BED_CHECK = False` if you want to revert to the default behavior.

```python
        # We add this DISABLE_BED_CHECK flag so that the chamber heater can be controlled independently of the bed heater
        # This should not be used in normal operation with the stock piezo sensor
        DISABLE_BED_CHECK = True
        if self.heater.name == "chamber" and heater_bed.heater_bed_state != 2 and heater_bed.is_heater_bed == 1 and not DISABLE_BED_CHECK:
            self.heater.set_pwm(read_time, 0.)
        else:
            self.heater.set_pwm(read_time, bounded_co)
        # Store state for next measurement
        self.prev_temp = temp
        self.prev_temp_time = read_time
        self.prev_temp_deriv = temp_deriv
        if co == bounded_co:
            self.prev_temp_integ = temp_integ
        if self.heater.name == "heater_bed" :
            if target_temp < 70:
                heater_bed.heater_bed_state = 0
            elif temp < target_temp - 2.:
                heater_bed.heater_bed_state = 1
            else:
                heater_bed.heater_bed_state = 2
```
## Restart the Printer

> [!NOTE]
> If you've edited the files through Fluidd, Use the orange "Save & Restart" button up top

The files we've just edited are not necessarily written to disk yet. 
To force this to happen, run the command `sync`. If that comes back with no further remarks and an exitcode of `0`, you can powercycle the printer.

![image](https://github.com/user-attachments/assets/fde60fab-cb96-482a-aad2-c40e5a41a9f3)
