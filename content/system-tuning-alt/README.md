> [!INFO]
> This tuning method is an alternative to [Qidi Plus4 System Tuning](/content/system-tuning/README.md):
> 1. It doesn't use IRQ remapping, which doesn't play a significant role on a modern kernel.
> 2. It's a different method for setting process priorities.
> 3. Only the xindi process requires kernel affinity; everything else is adequately scheduled by the scheduler without significant losses.

# Qidi Plus4 System Tuning - Alternative version

Sometimes you may encounter the following error on your printer:
> MCU 'mcu' shutdown: Timer too close

These errors are caused by a delay in data processing between the MCU and the Klipper process.
The printer has a fairly wide data bus and powerful MCUs.
The problem persists with Klipper - it simply doesn't have enough resources to operate.

> [!IMPORTANT]
> There are many other causes for the "MCU shutdown" error.
> For example, "Lost communication with MCU" is most often a cable issue or a static shock from the filament.
> This article only addresses the "Timer too close" software error.

## Process priority

The newer process scheduling mechanism (cgroup CPU weight, default - 100) will be used to specify processor priority, rather than nice.
Parameters will be specified as a service file extension (systemd drop-in).

The xindi process jumps between processors extremely frequently and will be bound to the last core. It will also be assigned a per-core load quota. This will cause lag when using the screen (especially when loading images), but will prevent it from rapidly consuming all resources.

```shell
sudo mkdir -p /etc/systemd/system/klipper.service.d/ /etc/systemd/system/makerbase-client.service.d/ /etc/systemd/system/moonraker.service.d/ /etc/systemd/system/webcamd.service.d/
echo -e "[Service]\nCPUWeight=700" | sudo tee /etc/systemd/system/klipper.service.d/override.conf
echo -e "[Service]\nCPUWeight=80" | sudo tee /etc/systemd/system/moonraker.service.d/override.conf
echo -e "[Service]\nCPUWeight=10" | sudo tee /etc/systemd/system/webcamd.service.d/override.conf
echo -e "[Service]\nCPUWeight=10\nCPUQuota=25%\nCPUAffinity=3" | sudo tee /etc/systemd/system/makerbase-client.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart klipper makerbase-client moonraker webcamd
```

## CPU Frequency

> [!WARNING]
> Important - all changes from now on are at your own risk.

> [!WARNING]
> Start with good board cooling. You need better cooling!

For some reason, Qidi uses dtb files (similar to BIOS settings) with a frequency limit of 1.2 GHz. However, there is an Armbian dtb file with a frequency of ~1.3 GHz and a slightly higher voltage:


| Frequency | Qidi uV   | Armbian uV |
|-----------|-----------|------------|
| 408MGz    | 950000    | 950000     |
| 600MGz    | 950000    | 950000     |
| 816MGz    | 1000000   | 1050000    |
| 1008MGz   | 1100000   | 1150000    |
| 1200MGz   | 1275000   | 1225000    |
| 1296MGz   | Disabled  | 1300000    |

There are also differences in RAM voltage - a little less in Armbian.

If you have good cooling, you can slightly overclock the SOC:

```shell
sudo cp /boot/extlinux/extlinux.conf /root/extlinux-orig.conf
test -e /boot/dtb-5.16.20-rockchip64/rockchip/rk3328-roc-cc.dtb  && sudo sed -i 's|\(\s*fdt\s\).*|\1/dtb-5.16.20-rockchip64/rockchip/rk3328-roc-cc.dtb|' /boot/extlinux/extlinux.conf
```

Just in case, let's comment out the maximum frequency limit for cpufrequtils (although mine was already ~1.3GHz out of the box):

```shell
sudo sed -i 's/^[^#]*\s*MAX_SPEED=/#&/' /etc/default/cpufrequtils
```

You'll need to power cycle the printer to apply the settings. After powering up, the output will show:

```shell
/usr/bin/cpufreq-info -c 0
```

You should see a frequency of 1.30 GHz. For example:

```
  current CPU frequency is 1.30 GHz (asserted by call to hardware).
  cpufreq stats: 408 MHz:0.00%, 600 MHz:9.10%, 816 MHz:0.00%, 1.01 GHz:0.00%, 1.20 GHz:0.00%, 1.30 GHz:90.90%  (87511)
```

## Uninstall

To disable priority, simply delete the drop-in files:

```shell
sudo rm -v /etc/systemd/system/klipper.service.d/override.conf /etc/systemd/system/makerbase-client.service.d/override.conf /etc/systemd/system/moonraker.service.d/override.conf /etc/systemd/system/webcamd.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart klipper makerbase-client moonraker webcamd
```

To disable overclocking, run the following command and power cycle the printer:

```shell
test -e /boot/dtb/rockchip/rk3328-roc-cc.dtb && sudo sed -i 's|\(\s*fdt\s\).*|\1/dtb/rockchip/rk3328-roc-cc.dtb|' /boot/extlinux/extlinux.conf
```