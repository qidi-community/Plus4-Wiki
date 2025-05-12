# Disabling Wifi 8188gu module
As of QIDI's latest Plus4 firmware release, 1.6, the USB wireless module included 
in current machines is using an rtlink dongle that is creating a kernel thread that
is consuming considerably more CPU cycles than is expected. Due to the finite 
compute available on the SOC, it's best to preserve it for klipper. 

This can be achieved in by simply removing the dongle from the Plus4 system board or
more dramatically disabling the driver module from loading when the printer is
booting up. 

## Confirm The Issue
The easiest way to observe impact is running the `top` or `htop` commands from
the command line. If you see `RTW_CMD_THREAD` and CPU is high, you are impacted. In this screenshot, the user's printer is consuming a considerable amount of CPU at 24.3%

![](htop.png)

## Option 1: Unplug the module from the board
Remove the system fan board cover and examine the USB ports on the side right side of
the board. The USB dongle looks like this, but could vary:

![](IMG_5262.JPEG)

Once removed, you need to restart your printer so the module isn't loaded. Until the
machine is restarted, the module will remain loaded and continue to needlessly consume
CPU cycles.

## Option 2: Blacklist the Driver Module
If you'd rather NOT remove the dongle, you can simply blacklist the module from loading
in the first place. To do so, run the following commands:

ssh into your 3D Printer's Linux command shell (see [ssh-access](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/ssh-access) for details)
sudo -i
`cd /etc/modprobe.d`
`ls`
`echo "blacklist 8188gu" > blacklist-8188gu.conf`
`echo "blacklist cfg80211" > blacklist-cfg80211.conf`
`echo "blacklist rfkill" > blacklist-rfkill.conf`
`ls`
verify 3 new blacklist-*.conf files exist
`update-initramfs -u`

## Restart the Printer

> [!NOTE]
> If you've edited the files through Fluidd, Use the orange "Save & Restart" button up top

The files we've just edited are not necessarily written to disk yet. 
To force this to happen, run the command `sync`. If that comes back with no further remarks and an exitcode of `0`, you can powercycle the printer.

![image](https://github.com/user-attachments/assets/fde60fab-cb96-482a-aad2-c40e5a41a9f3)

## Validate The Fix
Once you have restarted your Plus4, connect via `ssh` to your printer again and run the following command:

`for MODULE in 8188gu cfg80211 rfkill ; do lsmod | grep -qw "${MODULE}" && echo "Module '${MODULE}' is loaded." || echo "Module '${MODULE}' is NOT loaded." ; done`

