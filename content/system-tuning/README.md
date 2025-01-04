# Qidi Plus4 System Tuning

The Qidi Plus4 utilises a RockChip based CPU with 4 cores running at a peak of 1.2Ghz

As such, there can be instances under certain high loads where the CPU can struggle to keep up with the MCU systems controlling the motion systems,
which leads to the occasional "MCU: Timer Too Close" errors that causes Klipper to shut down.

There are a number of CPU intensive processes that can compete with Klipper for CPU resources

- `xindi` is Qidi's UI interface driving daemon that is responsible for converting clicks on the printer screen into Klipper actions, as well as driving USB storage, networking, and firmware updates
- `mjpg_streamer` is the video streaming encoding daemon that provides a video stream to monitor the current print
- `nginx` is the Web Server daemon that hosts the FluiddUI Web Interface service that slicers and a web browser can interact with

Unfortunately the above processes can sometimes get in the way of Klipper, and cause CPU stuttering that is bad enough to cause Host CPU Timer Too Close errors

Additionally, the CPU is configured to run in an on-demand frequency-scaling mode that can also introduce
stuttering as the Linux scheduler tries to dynamically adjust the CPU frequency to respond to high load scenarios.

Fortunately there are ways in which we can tune Qidi's system to better optimise the CPU power mode and resource usage.

## Installing a run-time system tuning script

I have developed a run-time service script that attempts to isolate non-Klipper essential services to an individual CPU core
as well as bind Klipper services the remaining 3 CPU cores.

Additionally, the CPU is placed into performance mode to prevent it from downclocking its frequencies when idle.  This allows it
to respond more quickly to the load spikes that Klipper can introduce.

## Installing the Tuning Script

Follow this sequence of steps:

1. ssh into your 3D Printer's Linux command shell

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
It also does a one-time system tuneup for the currently running system so there's no need to power-cycle your printer

4. Now exit out of the root shell like so with the following command:

```
exit
```

## Verifying

When you first ran `/etc/init.d/tuning reload` there would have been a lot of diagnostic output explaining what the script was doing.
You should see that all `xindi`, `mjpg_streamer`, and `nginx` processes and threads were affined to CPU 3, and all `klippy` processes
and threads were affined to CPUs 0-2.

To verify the Unix scheduling niceness changes run the `top` command and take note of the nice level for the `xindi`, `mjpg_streamer`,
and `nginx` processes.  These should be set to `1`, `2`, and `2` respectively.

Alternately, run the following command:

```
ps axl | egrep "mjpg|xindi|nginx" | egrep -v "bash|grep" | awk '{print $6 " " $13}'
```

and that will extract the Nice level of the processes, and should present output similar to the following:

```
2 nginx:
2 nginx:
2 nginx:
2 nginx:
2 nginx:
1 /root/xindi/build/xindi
2 ./mjpg_streamer
```

where the number at the start represents the Nice level of the process

## Uninstalling

In the event that the tuning script is causing any issues, it can be uninstalled via the following procedure:

Log into your printer via ssh and run the following command:

```
sudo /etc/init.d/tuning stop
sudo rm -f /etc/init.d/tuning /etc/rc6.d/S99tuning
```
