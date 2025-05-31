# Filament Changes for Multi-Material Prints (Without MMU)

When you're doing filament changes for a multimaterial print (not using a MMU), the general advice is to put a pause command at the beginning of that layer

However, this method doesn't account for differences in filament settings (like temperature, retraction, etc.). So, even if you pause the print, you still need to configure different filament types in OrcaSlicer to get the correct behavior. On top of this, it doesn't allow multiple filament types in a single layer (although I would avoid too much of this since filament changes aren't fast)
# How (Method 1 - automatic pausing)

To make it work, just use the following as your "Change Filament G-code" for the machine gcode settings in orcaslicer

```ngc
M0
```

This automatically puts a print pause command at layer changes, regardless of whether it's at a particular layer height or not, allowing you to manually change filaments using the screen.