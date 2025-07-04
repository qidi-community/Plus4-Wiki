# Stew's Qidi Plus 4 Configs

Here in are irregularly updated unsanitized copies of the configuration that is currently running on my personal Qidi Plus 4

These configurations are provided as-is.  No warranties, express or implied, may be assumed when using these configurations.

They are merely intended as a point of reference.

## heaters.py

Included is my modified version of `/home/mks/klipper/klippy/extras/heaters.py`

This modified version uses the smoothed temperature value to feed into the PID algorithm when a heater's smooth time is >1.0s

## fan_generic.py

Replaces:  `/home/mks/klipper/klippy/extras/fan_generic.py`

Adds an `idle_timeout:` configuration line item that keep a fan running after turned off for the configured number of seconds

This is intended to be used for providing a cool-down functionality after a fan is turned off, such as the chamber circulation fan.
