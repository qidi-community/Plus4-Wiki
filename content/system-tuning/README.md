> [!IMPORTANT]
> The original version of the tuning script had a compatibility issue with `xindi`.  This has now been resolved. Please re-download and apply the updated tuning script if you installed a version prior to 8th Jan 2025.

# Qidi Plus4 System Tuning

If you've ever encountered the following error, or just want to make your Plus4 a little more responsive overall, this is the page for you.

![Timer Too Close](./timer_too_close.jpg "It's too close!")

## Introduction

The Qidi Plus4 utilises a RockChip based CPU with 4 cores running at a peak of 1.2Ghz

As such, there can be instances under certain high loads where the CPU can struggle to keep up with the MCU systems controlling the motion systems,
which leads to the occasional "MCU: Timer Too Close" (TCC in short) errors that causes Klipper to shut down.

There are a number of CPU intensive processes that can compete with Klipper for CPU resources

- `xindi` is Qidi's UI interface driving daemon that is responsible for converting clicks on the printer screen into Klipper actions, as well as driving USB storage, networking, and firmware updates
- `mjpg_streamer` is the video streaming encoding daemon that provides a video stream to monitor the current print
- `nginx` is the Web Server daemon that hosts the FluiddUI Web Interface service that slicers and a web browser can interact with
- `moonraker` is the API process that acts as an intermediary between Klipper and Web UI's such as Fluidd or Mainsail

Unfortunately the above processes can sometimes get in the way of Klipper, and cause CPU stuttering that is bad enough to cause TCC errors.

Additionally, the CPU is configured to run in an on-demand frequency-scaling mode that can also introduce stuttering as the Linux scheduler tries to dynamically adjust the CPU frequency to respond to high load scenarios.

Fortunately there are ways in which we can tune Qidi's system to better optimise the CPU power mode and resource usage.

## Installing a run-time system tuning script

I have developed a run-time service script that attempts to isolate non-Klipper essential services to an individual CPU core
as well as bind Klipper services the remaining 3 CPU cores.

Additionally, the CPU is placed into performance mode to prevent it from scaling its frequencies when idle.  This allows it
to respond more quickly to the load spikes that Klipper can introduce.

While ideally this installation procedure should be run when not printing anything, it is not a requirement.  It is generally safe
to install and run this script at any time.

## Installing the Tuning Script

To install and activate the tuning, follow this sequence of steps:

1. ssh into your 3D Printer's Linux command shell (see [ssh-access](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/ssh-access) for details)

2. Obtain a root shell on your printer like so:

```
sudo bash
```

3. Now run the following commands:

```
wget -O - https://raw.githubusercontent.com/qidi-community/Plus4-Wiki/refs/heads/main/content/system-tuning/tuning > /etc/init.d/tuning
chmod 755 /etc/init.d/tuning
ln -sf /etc/init.d/tuning /etc/rc3.d/S99tuning
/etc/init.d/tuning reload
```

This installs the tuning script and sets it up to run at system startup when the printer is powered on
It also does a one-time system tuneup for the currently running system so there's no need to power-cycle your printer.

> [!NOTE]
> `mjpg_streamer` often creates transient short-lived threads, and so the script may occasionally complain that it cannot find one of the `mjpg_streamer` processes.  In the chance that this error is seen, then it can be safely ignored.

4. Now exit out of the root shell like so with the following command:

```
exit
```

## Verifying CPU Performance Mode

Run the following command:

```
/usr/bin/cpufreq-info -c 0
```

This should generate output similar to the following:

```
cpufrequtils 008: cpufreq-info (C) Dominik Brodowski 2004-2009
Report errors and bugs to cpufreq@vger.kernel.org, please.
analyzing CPU 0:
  driver: cpufreq-dt
  CPUs which run at the same hardware frequency: 0 1 2 3
  CPUs which need to have their frequency coordinated by software: 0 1 2 3
  maximum transition latency: 62.0 us.
  hardware limits: 408 MHz - 1.20 GHz
  available frequency steps: 408 MHz, 600 MHz, 816 MHz, 1.01 GHz, 1.20 GHz
  available cpufreq governors: conservative, ondemand, userspace, powersave, performance, schedutil
  current policy: frequency should be within 1.20 GHz and 1.20 GHz.
                  The governor "performance" may decide which speed to use
                  within this range.
  current CPU frequency is 1.20 GHz (asserted by call to hardware).
  cpufreq stats: 408 MHz:0.00%, 600 MHz:0.03%, 816 MHz:0.00%, 1.01 GHz:0.00%, 1.20 GHz:99.96%  (520)
```

The important lines here at the 3 lines starting at `current_policy:`

The above output is informing us that the CPU will choose a frequency between 1200MHz and 1200Mhz (ie. a constant 1200Mhz) and that the `performance` CPU frequency governor is active.

This verifies that the CPU on the Plus4 is now operating in its highest possible performance mode.

## Verifying Process Niceness

When you first ran `/etc/init.d/tuning reload` there would have been a lot of diagnostic output explaining what the script was doing.
You should see that all `xindi` was affined to CPU 0, that `mjpg_streamer`, `moonraker`, and `nginx` processes and threads were affined to CPU 3, and all
`klippy` processes and threads were affined to CPU 1 and 2.

![image](https://github.com/user-attachments/assets/76b5972c-c30f-41f5-a399-519fe4b940bb)

To verify the Unix scheduling niceness changes run the `top` command and take note of the nice level for the `xindi`, `mjpg_streamer`,
and `nginx` processes (in the `NI` column). The values should be set to `1`, `2`, and `1` respectively.  The script does not adjust the niceness level of
either `klippy` or `moonraker` (ie. the `python` commands and line 2 and 3 of the screenshot) so their nice levels should remain at `0`.

![image](https://github.com/user-attachments/assets/831cb6c1-9605-426c-a46e-ddd5a999b699)

Alternately, run the following command:

```
ps axl | egrep "mjpg|xindi|nginx" | egrep -v "bash|grep" | awk '{print $6 " " $13}'
```

and that will extract the Nice level of the processes, and should present output similar to the following:

```
2 ./mjpg_streamer
1 /root/xindi/build/xindi
1 nginx:
1 nginx:
1 nginx:
1 nginx:
1 nginx:
```

where the number at the start represents the Nice level of the process

## What if I restart `mjpg_streamer` by changing values in `webcam.txt`?

In the event that you modify the `webcam.txt` parameters, this will intiate a new set of `mjpg_streamer` process/threads
and the tuning script will need to be manually re-run if you don't wish to power-cycle the printer.  This can be achieved
at any time with the following command:

```
sudo /etc/init.d/tuning reload
```

which will re-apply the tuning to the currently running system

## Deactivating the Tuning

If you wish to deactivate the system performance tuning, without uninstalling the script, run the following command:

```
sudo /etc/init.d/tuning stop
```

This can be useful when making comparisons as to how the printer behaves with, and without, the tuning parameters active


## Uninstalling

In the event that the tuning script is causing any issues, it can be uninstalled via the following procedure:

Log into your printer via ssh and run the following command:

```
sudo /etc/init.d/tuning stop
sudo rm -f /etc/init.d/tuning /etc/rc6.d/S99tuning
```
