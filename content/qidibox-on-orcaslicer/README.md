# Minimal changes to make OrcaSlicer work with QidiBox

---

In `Machine start G-code`:

Change:
```
PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND=[nozzle_temperature_initial_layer] CHAMBER=[chamber_temperature]
```
To:
```
PRINT_START BED=[bed_temperature_initial_layer_single] HOTEND=[nozzle_temperature_initial_layer] CHAMBER=[chamber_temperature] EXTRUDER=[initial_no_support_extruder]
```

---

Within `Change filament G-code`:

replace all contents there with [the contents from this file](./change-filament-g-code)

eg. <img width="1911" height="564" alt="image" src="https://github.com/user-attachments/assets/0c22d4d6-8c8f-438b-a009-08accee8f010" />

