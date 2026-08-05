# QIDI BOX — Sandbox-Verified Fix Bundle (2026-08-05)

> ## ⚠️ IMPORTANT DISCLAIMER
>
> **This bundle has NOT been tested on a physical QIDI Plus 4 printer.**
>
> All fixes were verified in a **Klipper software sandbox only** (Klipper's own CI file-output
> debug mode — virtual MCUs, no serial, no hardware). The sandbox runs **mainline Klipper**, while
> the real printer runs QIDI's fork (1.8.1), so fork-only API calls were guarded but not exercised
> on real hardware.
>
> **Use at your own risk.** Follow the install checklist, keep backups of your `*.so` files, and be
> ready to restore. If in doubt, test one change at a time. This is a community contribution with
> no guarantees — same as the parent module set.

---

## What this is

A verified patch set on top of the community `.so → .py` swap
(`customisable_qidibox_firmware`). It fixes **9 crashes/bugs** found by running the swap's modules
through a full Klipper sandbox (all box commands: load/unload, tool change, purge, temp set, RFID,
self-inspection, retry paths, unload macro).

- **6 fixes are fork-independent** (real-printer relevant)
- **3 fixes are mainline-drift shims** (only needed for FreeDi/mainline Klipper installs; the QIDI
  fork already has those APIs)

## Files

```
sandbox-fixes-2026-08-05/
├── patches/                          # apply with: patch -p1 < <file>
│   ├── box_extras.py.patch           # fixes 2,3,6,7,8,9
│   ├── aht20_f.py.patch              # fix 1
│   ├── box_stepper.py.patch          # fix 4 (mainline-drift)
│   ├── filament_motion_sensor.py.patch  # fix 5 (mainline-drift)
│   └── unload-macro-E-25.patch       # macro fix (stock unload extruded 25 mm)
└── required_config/                  # files the swap silently depends on
    ├── box_macros.cfg                # companion macro file (CLEAR_FLUSH dependency)
    ├── officiall_filas_list.cfg      # filament temp list (real, from QIDI firmware dump)
    └── box_extras.example.cfg        # example [box_extras] incl. filament_list_path
```

## Fix inventory

| # | File | Fix | Class |
|---|------|-----|-------|
| 1 | aht20_f.py | 4× None-guards on i2c reads (connect/CCP/AFE paths) — prevents connect crash when a read returns None | fork-independent |
| 2 | box_extras.py | accept `buffer_pin` config option (the auto-generated box.cfg always emits it; without this the .py swap fails to BOOT) | fork-independent |
| 3 | box_extras.py | E_UNLOAD: `get_temp_by_num()` None → 190 °C default (front-panel unload crash) | fork-independent |
| 4 | box_stepper.py | `note_kinematic_activity()` → `get_last_move_time()` (removed from mainline) | mainline-drift |
| 5 | filament_motion_sensor.py | QIDI-fork sensor + `note_filament_present(eventtime, bool)` signature | mainline-drift |
| 6 | box_extras.py | `set_box_temp`: `box_max_temps` KeyError + temp_info None guards (BOX_TEMP_SET crash when no box detected) | fork-independent |
| 7 | box_extras.py | TRY_MOVE_AGAIN: `_00`-suffix int-normalization + 2× None-temp guards (retry-button crash) | fork-independent |
| 8 | box_extras.py | `heater.set_can_wait()` guarded with `hasattr` (QIDI-fork-only API — TOOL_CHANGE_START crashes mainline) | mainline-drift |
| 9 | box_extras.py | `filament_list_path` config option (hardcoded `/home/mks/...` path broke non-QIDI hosts) + 3× None-guards (button_extruder_load ×2, QDE_004_009 retry path) | fork-independent |
| — | box.cfg macro | `G1 E25 F300` → `G1 E-25 F300` in `UNLOAD_FILAMENT` (stock unload EXTRUDED 25 mm instead of retracting — verified against QIDI's own generated template) | fork-independent |

## Install checklist (ALL items verified required in sandbox)

1. **`box_macros.cfg`** must be present — the registered `CLEAR_FLUSH` command runs `BOX_CLEAR_FLUSH`;
   without this file flushing **silently no-ops** (clogged nozzle / color bleed risk).
2. **`officiall_filas_list.cfg`** + `filament_list_path` in `[box_extras]` — temp lookups read this
   file; the hardcoded default path only exists on QIDI printers.
3. **`[filament_switch_sensor fila]`** section must exist (macros reference `SENSOR=fila`; missing →
   SET_FILAMENT_SENSOR error → shutdown).
4. **`[box_extras]` pins** (real, from QIDI's own template): `b_button_pin: ^mcu_box1:PB1`,
   `b_endstop_pin: mcu_box1:PA9`, `e_endstop_pin: mcu_box1:PA10`, `buffer_pin: ^mcu_box1:PB0`.
5. Box includes load AFTER heaters/extruder (box includes at the END of printer.cfg).

## What was NOT fixed (stock-firmware side)

- **QDE_004_024 / M104 S0 temp-stability** (GitHub issue I-12): emitted by the stock `.so` module,
  not the community `.py`. The sandbox confirmed the `.py` path handles M104 S0 + re-heat cleanly,
  but the `.so` behavior needs QIDI to fix.
- **Purge amounts** (issue I-06): `EXTRUSION_AND_FLUSH` hardcodes ~180 mm of purge per change — a
  separate config-level change.

## How it was verified (reproducible)

- Klipper file-output debug mode (`-d dict -o out -i gcode`), synthesized STM32-pin dictionary,
  3 virtual MCUs (mainboard/toolhead/box).
- 9 test files, all exit 0 with clean "Exiting" markers: boot, box command surface, unload macro
  (E-25 A/B), auto-reload + retry, **tool change** (TOOL_CHANGE_START/END + BOX_CHANGE_FILAMENT),
  **purge** (EXTRUSION_AND_FLUSH), **temp stability** (M104 S0 + re-heat), **misc batch**
  (RELOAD_ALL / CLEAR_RUNOUT_NUM / TIGHTEN_FILAMENT).
- Fork-only command warnings observed on mainline (fine on the real fork): `QIDI_PROBE_PIN_2`,
  `BED_MESH_CLEAR`, `CLEAR_MOTION_DATA`.
- **Again: sandbox only. Not yet tested on a physical printer.**

## Related

- Parent module set: `../README.md` (customisable_qidibox_firmware)
- Full sandbox + findings log maintained separately (see session docs 2026-08-05)
