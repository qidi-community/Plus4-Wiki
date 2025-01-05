# Disabling Wifi 8188gu module
As of QIDI's latest Plus4 firmware release, 1.6, the USB wireless module included 
in current machines is using an rtlink dongle that is creating a kernel thread that
is consuming considerably more CPU cycles than is expected. Due to the finite 
compute available on the SOC, it's best to preserve it for klipper. 

This can be achieved in by simply removing the dongle from the Plus4 system board or
more dramatically disabling the driver module from loading when the printer is
booting up. 

## Validating You Are Impacted
The easiest way to visually see impact is running the `top` or `htop` commands from
the command line. If you see `RTW_CMD_THREAD` and CPU is high, you are impacted.

## Option 1: Unplug the module from the board
Remove the system fan board cover and examine the USB ports on the side right side of
the board. The USB dongle looks like this:

Once removed, you need to restart your printer so the module isn't loaded. Until the
machine is restarted, the module will remain loaded and continue to needlessly consume
CPU cycles.

## Option 2: Blacklist the Driver Module
If you'd rather NOT remove the dongle, you can simply blacklist the module from loading
in the first place. To do so, execute this simple one liner to create the this file:

`sudo bash -c "echo 'blacklist 8188eu' > /etc/modprobe.d/blacklist-8188gu.conf"`

