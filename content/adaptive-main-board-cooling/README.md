# Adaptive Main Board Cooling Configuration

> [!IMPORTANT]
> If configuration files from the deprecated [config-xplus4](https://github.com/qidi-community/config-xplus4) repository were previously imported, a variation of this configuration is already installed and active. To verify, access the Fluidd UI in a web browser, press the `x` key on the keyboard, and look for a folder called `config-xplus4`. If it is not present, this guide can be implemented as documented. The `config-xplus4` modifications conflict with this guide and must be removed before proceeding.

## Overview

By default, the main board cooling fan operates only when the X/Y stepper motors are active (during homing and printing). While this reduces noise during idle periods, it leaves the main board's SoC and various components without adequate cooling.

This configuration provides continuous cooling. The main board fan runs at a low speed (`min_speed`) during idle periods to maintain acceptable temperatures. When the board temperature exceeds the configured `target_temp`, the fan speed increases to maintain thermal stability.

This enhanced version can optionally monitor TMC stepper driver temperatures. The fan speed is determined by the highest temperature reading between the host sensor and any configured stepper drivers. This ensures adequate cooling even when stepper drivers heat up during printing. After steppers are disabled, cooling continues for 2 minutes to allow proper driver cool-down.

> [!TIP]
> While this configuration works with the stock 40mm fan, upgrading to an 80mm fan with a 3D-printed main board cover, or installing a [high-quality 4020 fan](https://www.amazon.com/dp/B0CHYF6S2N) is recommended. These upgrades provide significantly better airflow with minimal noise increase, ensuring optimal cooling for the main board, SoC, and stepper drivers during both idle and active operation.

## Installation Steps

### Step 1: Edit printer.cfg

Open the Fluidd UI and navigate to the `Configuration` tab. Locate and open the `printer.cfg` file.

#### Comment out the existing controller_fan section

Locate the `[controller_fan board_fan]` section and comment out all lines:

> [!WARNING]  
> Different firmware versions may have varying lines in the `[controller_fan board_fan]` section. All lines in this section must be commented out, regardless of their content.
```
# [controller_fan board_fan]
# pin: U_1:PC4
# max_power: 1.0
# shutdown_speed: 1.0
# cycle_time: 0.01
# fan_speed: 1.0
# heater: chamber
# stepper: stepper_x, stepper_y
```

#### Add the new temperature_fan section

Below the commented-out section, add the following configuration:
```
[temperature_fan board_fan]
pin: U_1:PC4
sensor_type: temperature_host
stepper: stepper_x, stepper_y
control: pid
pid_Kp: 5
pid_Ki: 2
pid_Kd: 5
pid_deriv_time: 2.0
target_temp: 50
min_temp: 0
max_temp: 100
min_speed: 0.3
max_speed: 1.0
max_power: 1.0
shutdown_speed: 1.0
cycle_time: 0.01
off_below: 0
```

> [!NOTE]
> The `stepper` parameter is optional. To monitor only host temperature without stepper driver monitoring, remove the `stepper: stepper_x, stepper_y` line.

#### Save without restarting

Click the `SAVE` button (not `SAVE & RESTART`) to preserve changes without restarting Klipper.

### Step 2: Install the enhanced temperature_fan module

Connect to the printer via SSH and execute the following commands:
```bash
cp /home/mks/klipper/klippy/extras/temperature_fan.py /home/mks/klipper/klippy/extras/temperature_fan.py.backup
wget -O /home/mks/klipper/klippy/extras/temperature_fan.py https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/adaptive-main-board-cooling/temperature_fan.py
rm /home/mks/klipper/klippy/extras/__pycache__/temperature_fan*.pyc
```

### Step 3: Restart Klipper
```bash
sudo systemctl restart klipper
```

The adaptive main board cooling system is now active.

## Restoring Original Configuration

To revert to the original configuration:

1. In `printer.cfg`, remove the `[temperature_fan board_fan]` section and uncomment the `[controller_fan board_fan]` section
2. Click the `SAVE` button
3. Connect via SSH and execute:
```bash
cp /home/mks/klipper/klippy/extras/temperature_fan.py.backup /home/mks/klipper/klippy/extras/temperature_fan.py
rm /home/mks/klipper/klippy/extras/__pycache__/temperature_fan*.pyc
sudo systemctl restart klipper
```