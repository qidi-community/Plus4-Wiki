#!/bin/bash

FILE_TO_PATCH="/home/mks/klipper/klippy/extras/heaters.py"
BACKUP_FILE="/tmp/heaters.py.bkp"
PATCH_FILE="/tmp/heaters_patch.diff"

cat > "$PATCH_FILE" << 'EOF'
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
EOF

echo "Creating backup of $FILE_TO_PATCH to $BACKUP_FILE..."
cp $FILE_TO_PATCH $BACKUP_FILE
if [ $? -ne 0 ]; then
    echo "Error: Failed to create backup!"
    echo "Please proceed with the patch manually."
    exit 1
fi

echo "Applying patch..."
patch $FILE_TO_PATCH < $PATCH_FILE

if [ $? -eq 0 ]; then
    echo "Patch applied successfully!"
    echo "Backup saved as: $BACKUP_FILE"
else
    echo "Patch failed! Reverting to backup..."
    echo "Maybe you already had applied the patch?"
    cp "$BACKUP_FILE" "$FILE_TO_PATCH"
    if [ $? -eq 0 ]; then
        echo "File reverted to original state."
    else
        echo "Error: Failed to restore backup!"
    fi
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Clean up patch file
rm -f "$PATCH_FILE"

echo "Done!"