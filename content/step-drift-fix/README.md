# The (possible) issue

Klipper (potentially) acucmulates microstep errors - this is no longer and issue on Mainline klipper but (may) be an issue on our printers still

I may have also this when I was testing out some repeated probing tests (hundreds of probes) - the issue persisted despite implementing the changes/fixes that Stew675 mentioned in the More Accurate Bed Meshing guide.
https://github.com/qidi-community/Plus4-Wiki/blob/main/content/more-accurate-bed-meshing/README.md

In addition to that, you can read more about the issue 
here: https://github.com/OpenNeptune3D/OpenNept4une/issues/224,
here: https://github.com/Klipper3d/klipper/issues/6711
and here: https://github.com/Klipper3d/klipper/pull/6712/commits/b525a0904ecf9abdc16d073c76d8d2c757f5bcbe

The root cause is in how Klipper calculates endstop trigger time during the probing process. There's a discrepancy between when the endstop is triggered and when the motion stops, and current code doesn't properly account for the oversampling window. Once again, this isn't an issue in current klipper but it may be an issue in this one.

The problem is especially noticeable with:
- Higher microstepping configurations (32 or 64)
- Faster probe speeds
- Multiple probe samples per point

>[!IMPORTANT]
> This may not actually be needed at all - this is only included because I went through the effort of doing this and perhaps this can be useful if you identify this to be an issue for you. However, chances are simply following Stew675's steps will avoid it altogether.

# What to do

> If you aren't comfortable implementing something like this, adding the fixes from [Stew675's repository (link)](https://github.com/qidi-community/Plus4-Wiki/blob/main/content/more-accurate-bed-meshing/README.md) does improve it without firmware changes and is less hacky. 

1. SSH into the machine (if you don't know how to do this already, it is probably better not to do this mod)
2. Navigate to `/~klipper/klippy/`
3. Make a backup just in case `cp mcu.py mcu.py.bak`
4. `cp mcu.py.bak ~/printer_data/config/mcu.py.bak`
5. Copy it into config files for easy editing `cp mcu.py ~/printer_data/config/mcu.py`
6. Make changes according to the Github commit. Note that they're not the same version so line numbers don't exactly match up [GitHub Commit link)](https://github.com/Klipper3d/klipper/pull/6712/commits/b525a0904ecf9abdc16d073c76d8d2c757f5bcbe)
7. Copy back in the ssh session `cp -f ~/printer_data/config/mcu.py mcu.py`
8. Restart Klipper `sudo systemctl restart klipper`
9. Reboot the machine and enjoy more accurate probes
10. If you made the changes previously using Stew675's method of reduzing step count, you may consider restoring the default Qidi values, since the underlying issue is more effectively addressed

>[!NOTE]
> If you messed up something and klipper doesn't start, you can see it via `journalctl -u klipper -n 50` and check the error.

I have included the altered mcu.py and the mcu.py.bak in the repo. Note that these instructions and these files are for v1.6.0 firmware, and using this file on future or past updates will probably change/break this and your machine.