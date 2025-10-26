# button_irq.py - Klipper Python module for IRQ-driven buttons
#
# Copyright (C) 2025  Menson <lms228@163.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging

class _IRQButtonMCU:
    def __init__(self, printer, mcu, debounce_us):
        self.printer = printer
        self.reactor = printer.get_reactor()
        self.mcu = mcu
        self.pin_list = []
        self.callbacks = []
        self.oid = mcu.create_oid()
        self.ack_count = 0
        self.state = 0
        self.invert = 0
        self.debounce_us = debounce_us

        self.mcu.register_response(self._handle_state, "irq_button_state", self.oid)
        self.mcu.register_config_callback(self._build_config)

    def setup_buttons(self, pin_params_list, callback):
        mask = 0
        shift = len(self.pin_list)
        for pin_params in pin_params_list:
            if pin_params.get('invert', False):
                self.invert |= 1 << len(self.pin_list)
            mask |= 1 << len(self.pin_list)
            self.pin_list.append(pin_params)
        self.callbacks.append((mask, shift, callback))

    def _build_config(self):
        logging.info("_irq_button debounce_us=%d", self.debounce_us)
        for pin in self.pin_list:
            self.mcu.add_config_cmd(
                "config_irq_button oid=%d pin=%s pull_up=%d debounce_us=%d invert=%d" %
                (self.oid, pin['pin'], pin.get('pullup', 0), self.debounce_us, pin.get('invert', 0))
            )
        cmd_queue = self.mcu.alloc_command_queue()
        self.ack_cmd = self.mcu.lookup_command(
            "irq_button_ack oid=%c count=%c", cq=cmd_queue)

    def _handle_state(self, msg):
        count = msg["count"]
        states = msg["state"]
        #logging.warning("IRQ button state oid=%d count=%d states=%s",
        #                 self.oid, count, states)
        for s in states:
            s = int(s) ^ self.invert
            if s != self.state:
                changed = s ^ self.state
                self.state = s
                for mask, shift, callback in self.callbacks:
                    if changed & mask:
                        value = (s & mask) >> shift
                        self.reactor.register_async_callback(
                            lambda et, c=callback, v=value: c(et, v))
        self.ack_cmd.send([self.oid, count])


class MCU_irq_button:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.irq_buttons = {}

    def register_buttons(self, pins, callback, debounce_us):
        ppins = self.printer.lookup_object('pins')
        mcu = mcu_name = None
        pin_params_list = []

        for pin in pins:
            pin_params = ppins.lookup_pin(pin, can_invert=True, can_pullup=True)
            if mcu is not None and pin_params['chip'] != mcu:
                raise ppins.error("IRQ button pins must be on same MCU")
            mcu = pin_params['chip']
            mcu_name = pin_params['chip_name']
            pin_params_list.append(pin_params)

        mcu_button = self.irq_buttons.get(mcu_name)
        if (mcu_button is None
            or len(mcu_button.pin_list) + len(pin_params_list) > 8):
            logging.warning(
                "Creating new IRQ button object for MCU '%s' with %d pins",
                mcu_name, len(pin_params_list))
            mcu_button = _IRQButtonMCU(self.printer, mcu, debounce_us)
            self.irq_buttons[mcu_name] = mcu_button

        mcu_button.setup_buttons(pin_params_list, callback)

def load_config(config):
    return MCU_irq_button(config)
