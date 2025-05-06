# Support fans that are controlled by gcode
#
# Copyright (C) 2016-2020  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
from . import fan

PIN_MIN_TIME = 0.100

class PrinterFanGeneric:
    cmd_SET_FAN_SPEED_help = "Sets the speed of a fan"
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self.handle_ready)
        self.fan = fan.Fan(config, default_shutdown_speed=1.)
        self.fan_name = config.get_name().split()[-1]
        self.fan_speed = config.getfloat('fan_speed', default=1.,
                                         minval=0., maxval=1.)
        self.idle_speed = config.getfloat(
            'idle_speed', default=self.fan_speed, minval=0., maxval=1.)
        self.idle_timeout = config.getint("idle_timeout", default=0, minval=0)

        gcode = self.printer.lookup_object("gcode")
        gcode.register_mux_command("SET_FAN_SPEED", "FAN",
                                   self.fan_name,
                                   self.cmd_SET_FAN_SPEED,
                                   desc=self.cmd_SET_FAN_SPEED_help)
        self.fan_on = True
        self.last_on = self.idle_timeout
        self.last_speed = 0.0
        self.target_speed = 0.0
    def handle_ready(self):
        reactor = self.printer.get_reactor()
        reactor.register_timer(self.callback, reactor.monotonic()+PIN_MIN_TIME)
    def get_status(self, eventtime):
        return self.fan.get_status(eventtime)
    def cmd_SET_FAN_SPEED(self, gcmd):
        speed = gcmd.get_float('SPEED', 0.)
        self.last_speed = self.target_speed
        self.target_speed = speed
        if speed > 0:
            self.fan.set_speed_from_command(speed)
    def callback(self, eventtime):
        set_speed = self.target_speed
        if set_speed > 0:
            self.last_speed = set_speed
            self.last_on = 0
        elif self.last_speed > 0:
            if self.last_on < self.idle_timeout:
                set_speed = self.last_speed
                self.last_on += 1
            else:
                self.last_speed = 0
                self.last_on = self.idle_timeout

        curtime = self.printer.get_reactor().monotonic()
        print_time = self.fan.get_mcu().estimated_print_time(curtime)
        self.fan.set_speed(print_time + PIN_MIN_TIME, set_speed)
        return eventtime + 1.0

def load_config_prefix(config):
    return PrinterFanGeneric(config)
