# Filament Changes for Multi-Material Prints (Without MMU)

When you're doing filament changes for a multimaterial print (not using a MMU), the general advice is to put a pause command at the beginning of that layer

However, this method doesn't account for differences in filament settings (like temperature, retraction, etc.). So, even if you pause the print, you still need to configure different filament types in OrcaSlicer to get the correct behavior. On top of this, it doesn't allow multiple filament types in a single layer (although I would avoid too much of this since filament changes aren't fast)
# How (Method 1 - automatic pausing)

To make it work, just use the following as your "Change Filament G-code" for the machine gcode settings in orcaslicer

```ngc
M0
```

Alternatively, if you would like to get some beeps (beep-beep-beep-beeeeeeeeep) to let you know it's filament change time

```ngc
; Thanks to lortsie wiki page for the beep commands
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
G4 P100  ; Pause
SET_PIN PIN=beeper VALUE=1
G4 P1000  ; Short beep
SET_PIN PIN=beeper VALUE=0
G4 P100  ; Pause

M0
```

This automatically puts a print pause command at layer changes, regardless of whether it's at a particular layer height or not, allowing you to manually change filaments using the screen.

>[!NOTE]
>Make sure to also check the `Manual Filament Change` box under the `MultiMaterial / Single Extruder multi-material setup` or your print will pause at the start after making the purge lines