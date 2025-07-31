import configparser
import pyudev
import re
import logging

class BoxButton:
    def __init__(self, config, pin, bc):
        printer = config.get_printer()
        buttons = printer.load_object(config, 'buttons')
        buttons.register_buttons([pin], bc)

class BoxEndstop:
    def __init__(self, config, name, pin, reuse=False):
        printer = config.get_printer()
        self.endstops = []
        ppins = printer.lookup_object('pins')
        if reuse:
            pin_params = ppins.parse_pin(pin, can_invert=True, can_pullup=True)
            self.endstop = pin_params['chip'].setup_pin('endstop', pin_params)
        else:
            self.endstop = ppins.setup_pin('endstop', pin)
        self.endstops.append((self.endstop, name))
        query_endstops = printer.load_object(config, 'query_endstops')
        query_endstops.register_endstop(self.endstop, name)
        self.scram = False

    def add_stepper(self, stepper):
        self.endstop.add_stepper(stepper)
    def get_endstops(self):
        return self.endstops
    def set_scram(self, value):
        self.scram = value

class BoxOutput:
    def __init__(self, config, pin):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.mcu = self.printer.lookup_object('mcu')
        ppins = self.printer.lookup_object('pins')
        pin_params = ppins.parse_pin(pin, True, True)
        self.digital_out = pin_params['chip'].setup_pin('digital_out', pin_params)
        self.digital_out.setup_max_duration(0.)
        self.digital_out_value = 0.
        self.digital_out.setup_start_value(self.digital_out_value, 0.)
        self.last_time = 0

    def set_pin(self, value):
        if value != self.digital_out_value:
            curtime = self.reactor.monotonic()
            print_time = self.mcu.estimated_print_time(curtime) + 0.01
            if print_time - self.last_time > 0.01:
                self.digital_out.set_digital(print_time, value)
                self.digital_out_value = value
                self.last_time = print_time

class BoxMotion:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.box_motion_sensor = self.printer.load_object(config, 'filament_motion_sensor box_motion_sensor')
        self.detection_length = self.box_motion_sensor.detection_length / 0.01
        self.motion_speed = 5
        self.motion_time = 0
        self.motion_start_time = 0
        self.motion_end_time = 0
        self.start_motion = False
        self.last_state = 0
        self.stop_count = 0
        self.endstop_name = None
        self.box_motion_timer = self.printer.get_reactor().register_timer(self.update_box_motion)

        ###自检所需参数
        self.check_motion_active = False
        self.has_change = False
        self.change_num = 0
        self.time_limit = 0
        self.check_num = 0
        self.check_motion_timer = None
        self.motion_check_start_time = 0
        self.last_button_state = 0

    def init_box_motion(self, name=None, speed=0, start=0, end=0):
        self.endstop_name = name
        self.stop_count = 0
        self.motion_time = 0
        self.motion_start_time = start
        self.motion_end_time = end
        self.motion_speed = speed / 2
        self.start_motion = False
        self.last_state = self.box_motion_sensor.button_state
    def update_box_motion(self, eventtime):
        state = self.box_motion_sensor.button_state
        if self.start_motion == False:
            if state == self.last_state:
                if self.motion_time > 2.5:
                    self.box_scram()
            else:
                self.start_motion = True
                self.last_state = state
                self.motion_time = 0
        elif self.motion_start_time < self.motion_time < self.motion_end_time:
            if state == self.last_state:
                self.stop_count += 1
                speed = self.detection_length / self.stop_count
                if speed < self.motion_speed:
                    self.box_scram()
            else:
                self.last_state = state
                self.stop_count = 0
        self.motion_time += 0.01
        return eventtime + 0.01

    def box_scram(self):
        box_extras = self.printer.lookup_object('box_extras')
        if self.endstop_name == "e_endstop":
            box_extras.e_output.set_pin(0.)
            box_extras.e_endstop.set_scram(True)
        elif self.endstop_name == "b_endstop":
            box_extras.b_output.set_pin(1.)
            box_extras.b_endstop.set_scram(True)

    ###自检功能代码
    def check_motion_state(self,time_limit,check_num):
        self.change_num = 0
        self.time_limit = time_limit
        self.check_num = check_num
        self.has_change = False  
        self.last_button_state = self.box_motion_sensor.button_state
        self.check_motion_active = True
        self.motion_check_start_time = self.printer.get_reactor().monotonic()
        
        self.check_motion_timer = self.printer.get_reactor().register_timer(
            self._check_motion_callback, 
            self.printer.get_reactor().monotonic())

    def _check_motion_callback(self, eventtime):
        if not self.check_motion_active:
            return self.printer.get_reactor().NEVER

        elapsed = self.printer.get_reactor().monotonic() - self.motion_check_start_time
        if elapsed >= self.time_limit:
            self.check_motion_active = False
            return self.printer.get_reactor().NEVER

        current_state = self.box_motion_sensor.button_state
        if current_state != self.last_button_state:
            self.change_num += 1
            self.last_button_state = current_state
            if self.change_num == self.check_num:
                self.has_change = True  
        return eventtime + 0.1

    def stop_check_motion(self):
        if self.check_motion_active and self.check_motion_timer is not None:
            self.printer.get_reactor().unregister_timer(self.check_motion_timer)
            self.check_motion_timer = None
        self.check_motion_active = False

class ToolChange:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.exclude_tool = False
        self.last_position = [0., 0., 0., 0.]
        self.next_transform = None
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode_move = self.printer.load_object(config, 'gcode_move')
        self.gcode.register_command('TOOL_CHANGE_START', self.cmd_TOOL_CHANGE_START)
        self.gcode.register_command('TOOL_CHANGE_END', self.cmd_TOOL_CHANGE_END)

    def cmd_TOOL_CHANGE_START(self, gcmd):
        box_extras = self.printer.lookup_object('box_extras')
        f = gcmd.get_int('F', -1)
        value_f = box_extras.get_value_by_key('value_t' + str(f), 'slot' + str(f))
        t = gcmd.get_int('T', -2)
        value_t = box_extras.get_value_by_key('value_t' + str(t), 'slot' + str(t))
        box_extras.save_variable("is_tool_change", 1)
        if value_f == value_t and self.next_transform is None:
            self.gcode.run_script_from_command("MOVE_TO_TRASH\n")
            self.exclude_tool = True
            self.next_transform = self.gcode_move.set_move_transform(self, force=True)
            self.last_position = self.next_transform.get_position()
            toolhead = self.printer.lookup_object('toolhead')
            toolhead.get_extruder().get_heater().set_can_wait(False)
    def cmd_TOOL_CHANGE_END(self, gcmd):
        box_extras = self.printer.lookup_object('box_extras')
        box_extras.save_variable("is_tool_change", 0)
        if self.next_transform:
            self.exclude_tool = False
            self.gcode_move.set_move_transform(self.next_transform, force=True)
            self.next_transform = None
            self.gcode_move.reset_last_position()
            toolhead = self.printer.lookup_object('toolhead')
            toolhead.get_extruder().get_heater().set_can_wait(True)

    def get_position(self):
        return list(self.last_position)

    def move(self, newpos, speed):
        return

class BoxExtras:
    def __init__(self, config):
        self.printer = config.get_printer()
        reactor = self.printer.get_reactor()
        b_button_pin = config.get('b_button_pin')
        self.b_button = BoxButton(config, b_button_pin, self.b_button_callback)
        self.b_endstop_state = 0
        b_endstop_pin = config.get('b_endstop_pin')
        self.b_endstop = BoxEndstop(config, 'b_endstop', b_endstop_pin)
        self.b_output = BoxOutput(config, b_endstop_pin)
        self.b_motion = BoxMotion(config)
        self.b_endstop_timer = reactor.register_timer(self.update_b_endstop)
        e_endstop_pin = config.get('e_endstop_pin')
        self.e_endstop = BoxEndstop(config, 'e_endstop', e_endstop_pin)
        self.e_output = BoxOutput(config, e_endstop_pin)
        self.e_endstop_timer = reactor.register_timer(self.update_e_endstop)

        self.tool_change = ToolChange(config)
        self.can_load_slot = True
        self.printer.register_event_handler("klippy:ready", self.handle_connect)
        self.print_stats = self.printer.load_object(config, 'print_stats')
        self.gcode_macro_resume = self.printer.lookup_object('gcode_macro RESUME_PRINT')
        self.save_variables = self.printer.load_object(config, 'save_variables')
        self.gcode_move = self.printer.lookup_object('gcode_move')
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('RELOAD_ALL', self.cmd_RELOAD_ALL)
        self.gcode.register_command('CLEAR_FLUSH', self.cmd_CLEAR_FLUSH)
        self.gcode.register_command('CLEAR_OOZE', self.cmd_CLEAR_OOZE)
        self.gcode.register_command('CUT_FILAMENT', self.cmd_CUT_FILAMENT)
        self.gcode.register_command('AUTO_RELOAD_FILAMENT', self.cmd_AUTO_RELOAD_FILAMENT)
        self.gcode.register_command('TRY_MOVE_AGAIN', self.cmd_RETRY)
        self.gcode.register_command('E_LOAD', self.button_extruder_load)
        self.gcode.register_command('E_UNLOAD', self.button_extruder_unload)
        self.gcode.register_command('E_BOX', self.button_box_unload)
        self.gcode.register_command('MOTION_TIPS', self.motion_tips)
        self.gcode.register_command('CLEAR_RUNOUT_NUM', self.cmd_CLEAR_RUNOUT_NUM)

        self.box_print_heat_state = [0,0,0,0]
        self.gcode.register_command('BOX_TEMP_SET', self.set_box_temp)
        self.gcode.register_command('DISABLE_BOX_HEATER', self.cmd_disable_box_heater)

        self.heating_timers = {}  
        self.gcode.register_command('RUN_STEPPER', self.cmd_RUN_STEPPER)
        self.gcode.register_command('DISABLE_BOX_DRY', self.cmd_DISABLE_BOX_DRY)
        self.gcode.register_command('ENABLE_BOX_DRY', self.cmd_ENABLE_BOX_DRY)
        self.set_box_drying_state = self._create_drying_state_setter()

        self.gcode.register_command('INIT_RFID_READ', self.cmd_INIT_RFID_READ)
        self.gcode.register_command('BOX_SELF_INSPECTION', self.cmd_SELF_INSPECTION)

        self.gcode.register_command('TIGHTEN_FILAMENT', self.cmd_TIGHTEN_FILAMENT)

        self.box_button_state = 0

        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='tty')

        self.sensor_str_tips = "b_endstop_state = {b_endstop_state}\ne_endstop_state = {e_endstop_state}\n"
        self.box_sensor_str_tips = "slot{slot_num} = {state}\n"

    def b_button_callback(self, eventtime, state):
        self.b_endstop_state = state
    def handle_connect(self):
        self.filament_hall = self.printer.lookup_object('hall_filament_width_sensor')
        slot_sync = self.get_value_by_key("slot_sync", "slot-1")
        if slot_sync != "slot-1":
            try:
                box_stepper = self.printer.lookup_object(f'box_stepper {slot_sync}')
            except Exception as e:
                self.gcode.respond_raw("!! QDE_004_010 The current feeding status is incorrect. Please exit the filament from the extruder.")
                self.save_variable('retry_step', 'QDE_004_010_00')
                reactor = self.printer.get_reactor()
                reactor.register_timer(self.delayed_init_error_raw, reactor.monotonic() + 3)
            else:
                if self.filament_hall.diameter > 0.5:
                    box_stepper.slot_sync(True)
                else:
                    box_stepper.slot_sync(False)
        can_run_init_read = self.get_value_by_key("auto_init_detect", 0)
        reactor = self.printer.get_reactor()
        reactor.register_timer(self.delayed_init_rfid, reactor.monotonic() + 5)
        reactor.register_timer(self.delayed_self_inspection, reactor.monotonic() + 3)
        # if self.b_endstop_state and can_run_init_read == 1:
        #     reactor = self.printer.get_reactor()
        #     reactor.register_timer(self.delayed_init_rfid, reactor.monotonic() + 5)
        # if not self.b_endstop_state:
        #     reactor = self.printer.get_reactor()
        #     reactor.register_timer(self.delayed_self_inspection, reactor.monotonic() + 3)
    def delayed_init_rfid(self, eventtime):
        can_run_init_read = self.get_value_by_key("auto_init_detect", 0)
        if self.b_endstop_state and can_run_init_read == 1 and self.printer.lookup_object('idle_timeout').get_status(eventtime)['printing_time'] == 0:
            self.gcode.run_script("INIT_RFID_READ\nM400\n")
            #self.cmd_INIT_RFID_READ()
        return self.printer.get_reactor().NEVER
    def delayed_self_inspection(self, eventtime):
        if not self.b_endstop_state and self.printer.lookup_object('idle_timeout').get_status(eventtime)['printing_time'] == 0 :
            self.box_button_state = 1
            self.gcode.run_script("BOX_SELF_INSPECTION")
            #self.cmd_SELF_INSPECTION()
        return self.printer.get_reactor().NEVER
    def delayed_init_error_raw(self, eventtime):
        self.gcode.respond_raw("!!Code:QDE_004_010; Message:The current feeding status is incorrect. Please exit the filament from the extruder.")
        self.save_variable('retry_step', 'QDE_004_010_00')
        return self.printer.get_reactor().NEVER
    def update_b_endstop(self, eventtime):
        self.b_output.set_pin(self.b_endstop_state)
        return eventtime + 0.01
    def update_e_endstop(self, eventtime):
        if self.filament_hall.diameter > 0.5:
            self.e_output.set_pin(0.)
        else:
            self.e_output.set_pin(1.)
        return eventtime + 0.01

    def cmd_RELOAD_ALL(self, gcmd):
        if self.print_stats.state != "printing" and self.b_endstop_state:
            rfid = self.get_value_by_key("auto_read_rfid",1)
            first = gcmd.get_int('FIRST', 0)
            self.can_load_slot = False
            current_tty_count = self.get_value_by_key('box_count')
            slot_count = 4 * current_tty_count
            while not self.can_load_slot:
                self.can_load_slot = True
                for i in range(first, first + slot_count):
                    if i >= slot_count:
                        i = i - slot_count
                    slot_state = self.get_value_by_key("slot" + str(i), 0)
                    if slot_state == 3 or slot_state == -1:
                        self.can_load_slot = False
                        rfid_device = f"card_reader_{(i // 2) + 1}"
                        box_stepper = self.printer.lookup_object('box_stepper slot' + str(i))
                        if rfid == 1:
                            box_rfid = self.printer.lookup_object('box_rfid ' + rfid_device)
                            box_rfid.start_rfid_read(box_stepper)
                        load_success = box_stepper.slot_load()
                        if not load_success:
                            self.can_load_slot = True
                            return
        elif self.print_stats.state != "printing" and not self.b_endstop_state:
            stepper_num = gcmd.get_int('FIRST', 0)
            stepper = self.printer.lookup_object('box_stepper slot' + str(stepper_num))
            self.can_load_slot = False
            stepper.do_move(50, 80, 50)
            stepper.disable_stepper()
            self.save_variable(stepper.stepper_name, 3)
        self.can_load_slot = True
    def cmd_CLEAR_FLUSH(self, gcmd):
        self.gcode.run_script_from_command("BOX_CLEAR_FLUSH")
    def cmd_CLEAR_OOZE(self, gcmd):
        self.gcode.run_script_from_command("BOX_CLEAR_OOZE")
    
    def cmd_CUT_FILAMENT(self, gcmd):
        t = gcmd.get_int('T', -1)
        slot = self.get_value_by_key('value_t' + str(t), 'slot' + str(t))
        slot_state = self.get_value_by_key(slot, -1)
        if slot_state != 0:
            self.gcode.run_script_from_command("BOX_MOVE_TO_CUTTER")
            loaded_extruder = self.get_value_by_key('last_load_slot','slot-1')
            if loaded_extruder != 'slot-1' and self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
                stepper = self.printer.lookup_object('box_stepper ' + str(loaded_extruder))
                stepper.dwell(0.5)
                stepper.do_move(-35, 50, 50)
                stepper.dwell(0.5)
                stepper.disable_stepper()
            self.gcode.run_script_from_command("BOX_DO_CUT")

    def cmd_AUTO_RELOAD_FILAMENT(self, gcmd):
        if self.b_endstop_state:
            slot_sync = self.get_value_by_key("slot_sync", "slot-1")
            if slot_sync != "slot-1":
                box_stepper = self.printer.lookup_object('box_stepper ' + slot_sync)
                next_slot = box_stepper.switch_next_slot()
                if next_slot != -1:
                    print_temp = self.gcode_macro_resume.variables.get('etemp', 250)
                    self.gcode.respond_info(str(print_temp))
                    # stew675 - The following line is untested, so leaving commented out for now
                    # self.gcode.run_script_from_command("BOX_AUTO_RELOAD_FILAMENT HOTEND=" + str(print_temp) + " EXTRUDER=" + str(next_slot))
                    self.gcode.run_script_from_command("M109 S" + str(print_temp) + "\nG1 E25 F300\nEXTRUDER_LOAD SLOT=slot" + str(next_slot) + "\nG1 E100 F300\nG1 E-1 F1800\nCLEAR_FLUSH\nRESUME")
                    return
        self.gcode.respond_info("Code:QDE_004_023; Message:Auto reload failed.")
        self.save_variable('retry_step', 'QDE_004_023_00')

    def cmd_RETRY(self, gcmd):
        retry_step = self.get_value_by_key('retry_step')
        rfid = bool(gcmd.get_int('RFID', 0))
        if retry_step is None:
            self.gcode.respond_info("No step to retry")
            return
        match = re.match(r"(.+)_(\d+)$", retry_step)
        step_name = None
        stepper_number = None
        if match:
            step_name = match.group(1)  
            stepper_number = match.group(2) 
        else:
            self.gcode.respond_info("Invalid retry_step format")
        self.save_variable('retry_step', None)
        retry_stpper = self.printer.lookup_object('box_stepper slot' + stepper_number)
        self.gcode.run_script_from_command("DISABLE_ALL_SENSOR")

        if step_name == 'QDE_004_001':
            return
        elif step_name == 'QDE_004_002':
            loaded_extruder = self.get_value_by_key('last_load_slot','slot-1')
            temp_stepper = self.printer.lookup_object('box_stepper ' + loaded_extruder)
            temp_stepper.cmd_EXTRUDER_UNLOAD(gcmd)
            retry_stpper.slot_load()
            return
        elif step_name == 'QDE_004_003':
            retry_stpper.cmd_SLOT_UNLOAD(gcmd)
            return
        elif step_name == 'QDE_004_004':
            retry_stpper.cmd_EXTRUDER_UNLOAD(gcmd)
            retry_stpper.cmd_SLOT_UNLOAD(gcmd)
            return
        elif step_name == 'QDE_004_005':
            if self.print_stats.state == "paused":
                    print_temp = self.gcode_macro_resume.variables.get('etemp', 250)
                    self.gcode.run_script_from_command("M109 S%s" %(str(print_temp)))
                    retry_stpper.cmd_EXTRUDER_LOAD(gcmd)
            else:
                print_temp = self.get_temp_by_slot(retry_stpper.stepper_name)['max_temp']
                self.gcode.run_script_from_command("M109 S%s" %(str(print_temp)))
                retry_stpper.cmd_EXTRUDER_LOAD(gcmd)
                self.gcode.run_script_from_command("M104 S0")
                return
        elif step_name == 'QDE_004_006':
            if self.print_stats.state == "paused":
                    print_temp = self.gcode_macro_resume.variables.get('etemp', 250)
                    self.gcode.run_script_from_command("M109 S%s" %(str(print_temp)))
                    retry_stpper.cmd_EXTRUDER_LOAD(gcmd)
            else:
                print_temp = self.get_temp_by_slot(retry_stpper.stepper_name)['max_temp']
                self.gcode.run_script_from_command("M109 S%s" %(str(print_temp)))
                retry_stpper.cmd_EXTRUDER_LOAD(gcmd)
                self.gcode.run_script_from_command("M104 S0")
                return
        elif step_name == 'QDE_004_007':
            pass
        elif step_name == 'QDE_004_009':
            if self.print_stats.state == "paused":
                    print_temp = self.gcode_macro_resume.variables.get('etemp', 250)
                    self.gcode.run_script_from_command("M109 S%s" %(str(print_temp)))
                    retry_stpper.cmd_EXTRUDER_UNLOAD(gcmd)
            else:
                print_temp = self.get_temp_by_slot(retry_stpper.stepper_name)['max_temp']
                self.gcode.run_script_from_command("M109 S%s" %(str(print_temp)))
                retry_stpper.cmd_EXTRUDER_UNLOAD(gcmd)
                self.gcode.run_script_from_command("M104 S0")
                return
        self.gcode.run_script_from_command("M400\n")
        current_retry_step = self.get_value_by_key('retry_step')
        if current_retry_step is None:
            self.gcode.run_script_from_command("RESUME_PRINT TOOL_CHANGE=1\n")   
    
    def button_extruder_load(self, gcmd):
        self.box_button_state = 1
        selected_slot = gcmd.get_int('SLOT', 16)
        stepper = self.printer.lookup_object('box_stepper slot' + str(selected_slot))

        # Assume a default old filament temperature of 190C
        old_filament_extrude_temp = 190

        if not self.b_endstop_state:
            # There's some filament that's already loaded.  Try to unload it
            loaded_extruder = self.get_value_by_key('last_load_slot','slot-1')
            if loaded_extruder == 'slot-1':
                # We have no information about the loaded filament however.  Throw an error
                self.gcode.respond_raw("!!Code:QDE_004_021; Message:Unable to recognize loaded filament.")
                self.save_variable('retry_step', 'QDE_004_021_00')
                self.gcode.run_script_from_command("M400\n")
                self.box_button_state = 0
                self.gcode.run_script_from_command("M104 S0\n")
                stepper.disable_stepper()
                return

            # Unload the old filament and purge what we can.  Use minimum temperatures to minimise oozing
            old_filament_extrude_temp = self.get_temp_by_slot(loaded_extruder)['min_temp']
            self.gcode.run_script_from_command("BOX_MOVE_HEATING HOTEND=%s" %(str(old_filament_extrude_temp)))
            self.printer.lookup_object('box_stepper ' + str(loaded_extruder)).cmd_EXTRUDER_UNLOAD(gcmd)
            self.gcode.run_script_from_command("M400\nM83\nG1 E20 F300\nM400")

        # Load in the new filament.  Use the higher of the new filament and any old filament temperatures
        new_filament_extrude_temp = self.get_temp_by_num(selected_slot)['min_temp']
        extrude_temp = max(new_filament_extrude_temp, old_filament_extrude_temp)
        self.gcode.run_script_from_command("BOX_MOVE_HEATING HOTEND=%s" %(str(extrude_temp)))
        stepper.cmd_EXTRUDER_LOAD(gcmd)

        # Purge out any old filament remaining in the hotend
        self.gcode.run_script_from_command("BOX_EXTRUDE HOTEND=%s" %(str(extrude_temp)))
        self.gcode.run_script_from_command("G1 X95 Y290\nM400")
        stepper.disable_stepper()
        self.box_button_state = 0

    def button_extruder_unload(self, gcmd):
        self.box_button_state = 1
        selected_slot = gcmd.get_int('SLOT', 16)
        stepper = self.printer.lookup_object('box_stepper slot' + str(selected_slot))
        
        if self.b_endstop_state:
            # There's no filament loaded however.  We don't need to do anything
            self.gcode.run_script_from_command("M400\n")
            self.box_button_state = 0
            return False

        extrude_temp = self.get_temp_by_num(selected_slot)['min_temp']
        self.gcode.run_script_from_command("BOX_MOVE_HEATING HOTEND=%s" %(str(extrude_temp)))
        self.gcode.run_script_from_command("M400\nCUT_FILAMENT\nMOVE_TO_TRASH\nM83")
        stepper.cmd_EXTRUDER_UNLOAD(gcmd,False)
        # stew675 - This next line tries to drain any filament left between extruder and hotend.  No need to move to a macro
        self.gcode.run_script_from_command("M83\nG1 E25 F300\nM400\nCLEAR_FLUSH\nCLEAR_OOZE\nG1 X95 Y290\nM104 S0\nM400")
        self.box_button_state = 0
        return True

    def button_box_unload(self, gcmd):
        self.box_button_state = 1
        selected_slot = gcmd.get_int('SLOT', 16)
        stepper = self.printer.lookup_object('box_stepper slot' + str(selected_slot))
        self.gcode.run_script_from_command("DISABLE_ALL_SENSOR")
        if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
            loaded_extruder = self.get_value_by_key('last_load_slot','slot-1')
            extruder_unload_success = False
            if loaded_extruder == stepper.stepper_name:
                extruder_unload_success = self.button_extruder_unload(gcmd)
            else:
                stepper.cmd_SLOT_UNLOAD(gcmd)
                self.box_button_state = 0
                return
                #self.gcode.respond_info("Unable to identify the filament inside the extruder. Please manually exit the filament from the extruder first.")
            if extruder_unload_success:
                stepper.cmd_SLOT_UNLOAD(gcmd)
            else:
                self.gcode.respond_raw("Extruder unloading failure.Please try again.")
        else:
            if self.get_value_by_key('last_load_slot','slot-1') == stepper.stepper_name and not self.b_endstop_state:
                stepper.cmd_EXTRUDER_UNLOAD(gcmd)
                self.gcode.run_script_from_command("M400\n")
            if not stepper.r_endstop_state:
                stepper.cmd_SLOT_UNLOAD(gcmd)
            else:
                pass
        self.gcode.run_script_from_command("M400\n")
        self.box_button_state = 0

    def cmd_INIT_RFID_READ(self, gcmd):
        can_run_init_read = self.get_value_by_key("auto_init_detect", 0)
        if can_run_init_read == 0 :
            return
        if self.b_endstop_state:
            self.can_load_slot = False
            current_tty_count = self.get_value_by_key("box_count", 0)
            slot_count = 4 * current_tty_count
            while not self.can_load_slot:
                self.can_load_slot = True
                for i in range(0, slot_count):
                    stepper = self.printer.lookup_object('box_stepper slot' + str(i))
                    if not stepper.r_endstop_state:
                        self.can_load_slot = False
                        load_success = stepper.cmd_SLOT_RFID_READ("")
                        if not load_success:
                            self.can_load_slot = True
                            return
                self.can_load_slot = True
                
        self.can_load_slot = True

    def set_box_temp(self, gcmd):
        temp_values = [gcmd.get_int(f'VT{i}', -1) for i in range(16)]
        box_max_temps = {}
        for i in range(0,self.get_value_by_key('box_count', 0)):
            current_box_max_temp = -1
            for j in range(0,4):
                slot = 'slot' + str(j + 4 * i)
                stepper = self.printer.lookup_object('box_stepper slot' + str(j + 4 * i))
                if not stepper.r_endstop_state:##had load filament
                    #filament = self.get_value_by_key(f'filament_slot' + str(j + 4 * i))
                    box_max_temp = self.get_box_temp_by_slot(slot)['max_temp']
                    if current_box_max_temp == -1:
                        current_box_max_temp = box_max_temp
                    else:
                        current_box_max_temp = min(box_max_temp,current_box_max_temp)
            box_max_temps[f'box_{i}'] = current_box_max_temp
            box_max_temps[f'box_{i}'] = {
                'max_temp': current_box_max_temp,
                'set': int(-1)}

        for idx, value in enumerate(temp_values):
            if value == -1:
                continue
            value_t= f'value_t' + str(idx)
            slot = self.get_value_by_key(value_t, 'slot' + str(idx))
            stepper = self.printer.lookup_object('box_stepper ' + str(slot))
            slot_num = stepper.stepper_num

            box_num = slot_num // 4 
            if box_max_temps[f'box_{box_num}']['set'] == -1:
                if value >= box_max_temps[f'box_{box_num}']['max_temp']:
                    box_max_temps[f'box_{box_num}']['set'] = box_max_temps[f'box_{box_num}']['max_temp']
                else:
                    box_max_temps[f'box_{box_num}']['set'] = value#max(box_max_temps[f'box_{box_num}']['set'],value)
            else:
                box_max_temps[f'box_{box_num}']['set'] = min(box_max_temps[f'box_{box_num}']['set'],value)

        for i in range(0,self.get_value_by_key('box_count', 0)):
            set_temp = box_max_temps[f'box_{i}']['set']
            box_id = i + 1
            heat_box_command = "SET_HEATER_TEMPERATURE HEATER=heater_box" + str(box_id) + " TARGET=" + str(set_temp)
            if set_temp > 0:
                self.box_print_heat_state[i] = 1
                self.gcode.run_script_from_command(heat_box_command)
            ##test_message
            #self.gcode.respond_raw(heat_box_command)
            #self.gcode.respond_raw(f"Box {i} max_temp: {box_max_temps[f'box_{i}']['max_temp']}")
            #self.gcode.respond_raw(f"Box {i} set_temp: {box_max_temps[f'box_{i}']['set']}")
    
    def cmd_disable_box_heater(self, gcmd):
        for i in range(1, self.get_value_by_key('box_count', 0) + 1):
            heat_box_command = "SET_HEATER_TEMPERATURE HEATER=heater_box" + str(i) + " TARGET=0"
            if self.box_print_heat_state[i-1] != 0:
                self.gcode.run_script_from_command(heat_box_command)

    def get_status(self, eventtime=None):
        hall_sensor = self.printer.lookup_object('hall_filament_width_sensor')
        e_endstop_state = 1 if hall_sensor.diameter > 0.5 else 0
        return {'box_button_state': self.box_button_state,
                'b_endstop_state': self.b_endstop_state,
                'e_endstop_state': e_endstop_state,
                }
    
    def _create_drying_state_setter(self):
        def set_drying_state(box_num, state):
            for i in range(4):
                slot_num = (box_num - 1) * 4 + i
                try:
                    stepper = self.printer.lookup_object(f'box_stepper slot{slot_num}')
                    stepper.is_drying = state
                except Exception as e:
                    self.printer.lookup_object('gcode').respond_raw(
                        f"!!Error setting slot{slot_num}: {str(e)}")
        return set_drying_state
    
    def cmd_RUN_STEPPER(self, gcmd):
        stepper_num = gcmd.get_int('STEPPER', 0)
        stepper = self.printer.lookup_object('box_stepper slot'+ str(stepper_num))
        stepper.do_move(-50, 80, 50)
        stepper.dwell(0.5)
        stepper.disable_stepper()
    
    def cmd_ENABLE_BOX_DRY(self, gcmd):
        reactor = self.printer.get_reactor()
        box_num = gcmd.get_int('BOX', 0)
        box_count = self.get_value_by_key('box_count', 1)
        end_time_h = gcmd.get_int('END_TIME', 8)
        end_time = end_time_h * 60 * 60
        box_temp = gcmd.get_int('TEMP', 0)
        
        # 验证BOX编号
        if box_num < 1 or box_num > box_count:
            gcmd.respond_raw(f"!!Invalid BOX number. Available: 1-{box_count}")
            return
        
        if end_time <= 0 or box_temp <= 0:
            self.gcode.respond_info("Parameter setting error, please reset.")
            return
        
        # 停止已有的加热循环
        if box_num in self.heating_timers:
            old_timer = self.heating_timers[box_num]['timer']
            reactor.unregister_timer(old_timer)
            self.set_box_drying_state(box_num, False)

        self.set_box_drying_state(box_num, True)

        #开启加热
        heat_box_command = "SET_HEATER_TEMPERATURE HEATER=heater_box" + str(box_num) + " TARGET=" + str(box_temp)
        self.gcode.run_script_from_command(heat_box_command)
        
        # 创建新的加热循环
        start_time = reactor.monotonic()
        timer = reactor.register_timer(
            lambda eventtime: self.heating_handler(eventtime, box_num, start_time, end_time),
            start_time + 300)
        
        self.heating_timers[box_num] = {
            'timer': timer,
            'start_time': start_time
        }
        gcmd.respond_info(f"BOX_DRY started for BOX {box_num}")

    def cmd_DISABLE_BOX_DRY(self, gcmd):
        reactor = self.printer.get_reactor()
        box_num = gcmd.get_int('BOX', 1)
        
        if box_num in self.heating_timers:
            timer_info = self.heating_timers.pop(box_num)
            reactor.unregister_timer(timer_info['timer'])
            self.set_box_drying_state(box_num, False)
            gcmd.respond_info(f"DISABLE_BOX_DRY for BOX {box_num}")
            heat_box_command = "SET_HEATER_TEMPERATURE HEATER=heater_box" + str(box_num) + " TARGET=0"
            self.gcode.run_script_from_command(heat_box_command)
        else:
            gcmd.respond_info(f"No active heating for BOX {box_num}")

    def heating_handler(self, eventtime, box_num, start_time, end_time):
        # 检查总运行时间
        if (eventtime - start_time) >= end_time:
            self.set_box_drying_state(box_num, False)
            self.heating_timers.pop(box_num, None)
            heat_box_command = "SET_HEATER_TEMPERATURE HEATER=heater_box" + str(box_num) + " TARGET=0"
            self.gcode.run_script_from_command(heat_box_command)
            return self.printer.get_reactor().NEVER
        
        try:
            # 获取该BOX的所有电机
            for i in range(4):
                slot_num = (box_num - 1) * 4 + i
                
                self.gcode.run_script_from_command("RUN_STEPPER STEPPER=" + str(slot_num) +"\nG4 P5000")
        except Exception as e:
            self.printer.lookup_object('gcode').respond_raw(f"!!Error in heating: {str(e)}")
            self.set_box_drying_state(box_num, False)
            self.heating_timers.pop(box_num, None)
            return self.printer.get_reactor().NEVER

        return eventtime + 300

    ####盒子自检
    def cmd_SELF_INSPECTION(self,gcmd):
        box_count = self.get_value_by_key('box_count',1)
        has_load_extrude = False
        slot_num = 0
        if self.get_value_by_key('last_load_slot','slot-1') != 'slot-1':
            stepper = self.printer.lookup_object('box_stepper ' + str(self.get_value_by_key('last_load_slot','slot-1')))
            if stepper.stepper_num < box_count * 4:
                if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
                    for i in range(0,box_count * 4):
                        loop_stepper = self.printer.lookup_object('box_stepper slot' + str(i))
                        loop_stepper.slot_sync(False)
                    self.b_motion.check_motion_state(18,1)
                    stepper.do_move(-25, 80, 5)
                    stepper.dwell(0.5)
                    stepper.do_move(20, 80, 5)
                    stepper.dwell(0.5)
                    stepper.do_move(-30, 80, 5)
                    stepper.dwell(0.5)
                    stepper.do_move(40, 80, 5)
                    stepper.dwell(3)
                    stepper.disable_stepper()
                    self.b_motion.stop_check_motion()
                    has_load_extrude = True
                    slot_num = stepper.stepper_num
                    if self.b_motion.has_change:
                        self.save_variable('last_load_slot', "slot" + str(stepper.stepper_num))
                        stepper.slot_sync(True)
                        self.box_button_state = 0
                        return
                else:
                    self.b_motion.check_motion_state(5,3)
                    stepper.do_move(50, 80, 50)
                    stepper.dwell(0.5)
                    stepper.do_move(-50, 80, 50)
                    stepper.dwell(3)
                    stepper.disable_stepper()
                    self.b_motion.stop_check_motion()
                    if self.b_motion.has_change:
                        self.save_variable('last_load_slot', "slot" + str(stepper.stepper_num))
                        self.box_button_state = 0
                        return
        if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
            for i in range(0,box_count * 4):
                stepper = self.printer.lookup_object('box_stepper slot' + str(i))
                stepper.slot_sync(False)
            for i in range(0,box_count * 4):
                stepper = self.printer.lookup_object('box_stepper slot' + str(i))
                if stepper.r_endstop_state or stepper.stepper_name == self.get_value_by_key('last_load_slot','slot-1'):
                    continue
                self.b_motion.check_motion_state(18,1)
                stepper.do_move(-25, 80, 5)
                stepper.dwell(0.5)
                stepper.do_move(20, 80, 5)
                stepper.dwell(0.5)
                stepper.do_move(-30, 80, 5)
                stepper.dwell(0.5)
                stepper.do_move(40, 80, 5)
                stepper.dwell(3)
                stepper.disable_stepper()
                self.b_motion.stop_check_motion()
                if self.b_motion.has_change:
                    self.save_variable('last_load_slot', "slot" + str(i))
                    stepper.slot_sync(True)
                    self.box_button_state = 0
                    return
        else:
            for i in range(0,box_count * 4):
                stepper = self.printer.lookup_object('box_stepper slot' + str(i))
                if stepper.r_endstop_state or stepper.stepper_name == self.get_value_by_key('last_load_slot','slot-1'):
                    continue
                self.b_motion.check_motion_state(5,3)
                stepper.do_move(50, 80, 50)
                stepper.dwell(0.5)
                stepper.do_move(-50, 80, 50)
                stepper.dwell(5)
                stepper.disable_stepper()
                self.b_motion.stop_check_motion()
                if self.b_motion.has_change:
                    self.save_variable('last_load_slot', "slot" + str(i))
                    self.box_button_state = 0
                    return
        if has_load_extrude:
            stepper = self.printer.lookup_object('box_stepper slot' + str(slot_num))
            stepper.slot_sync(True)
        self.box_button_state = 0
        self.gcode.respond_info("Code:QDE_004_015; Message:Box self-inspection failed, please try manually withdrawing the fed filament.")
        self.save_variable('retry_step', 'QDE_004_015_00')

    def motion_tips(self, gcmd):
        self.gcode.respond_info("Code:QDE_004_013; Message:Detected wrapping filament,please check the filament.")
        self.save_variable('retry_step', 'QDE_004_013_00')

    def cmd_CLEAR_RUNOUT_NUM(self, gcmd):
        for i in range(16):
            self.save_variable('runout_' + str(i), 0)
    
    def cmd_TIGHTEN_FILAMENT(self,gcmd):
        command_t = gcmd.get_int('T', -1)
        if command_t == -1:
            return
        slot = self.get_value_by_key(f"value_t{int(command_t)}")
        stepper = self.printer.lookup_object('box_stepper ' + str(slot))
        stepper.dwell(0.5)
        stepper.do_move(20, 50, 10)
        stepper.dwell(0.5)
        stepper.do_move(-20, 50, 15)
        stepper.dwell(1)
    #Variable
    def save_variable(self, varname, value):
        newvars = dict(self.save_variables.allVariables)
        newvars[varname] = value
        # Write file
        varfile = configparser.ConfigParser()
        varfile.add_section('Variables')
        for name, val in sorted(newvars.items()):
            varfile.set('Variables', name, repr(val))
        filename = self.save_variables.filename
        try:
            f = open(filename, "w")
            varfile.write(f)
            f.close()
        except:
            msg = "Unable to save variable " + varname + " as " + str(value)
            raise self.gcode.error(msg)
        self.save_variables.loadVariables()
    def get_value_by_key(self, varname, default_value=0):
        value = self.save_variables.allVariables.get(varname, default_value)
        return value
    def get_key_by_value(self, value, default=None, keyword=None):
        all_variables = dict(self.save_variables.allVariables)
        for key, val in sorted(all_variables.items()):
            if val == value and keyword in key:
                return key
        return default
    def search_index_by_value(self, value):
        for i in range(4 * self.get_value_by_key('box_count')):
            slot_value = self.get_value_by_key(f"slot{i}")
            if slot_value == value:
                return i
        return -1
    
    def get_temp_by_num(self, num):
        list_path="/home/mks/printer_data/config/officiall_filas_list.cfg"
        filament_id = self.get_value_by_key(f"filament_slot{num}",1)
        section = f"fila{filament_id}"
        config = configparser.ConfigParser()
        config.read(list_path)
        if section in config:
            min_temp = config.getint(section, "min_temp")
            max_temp = config.getint(section, "max_temp")
            return {
            'min_temp': min_temp,
            'max_temp': max_temp,
            }
        else:
            if num > 50 or num <= 0:
                self.gcode.respond_raw("filament num error.")
            else:
                self.gcode.respond_raw("officiall_filas_list file error.")
            return None  
        
    def get_temp_by_slot(self, slot):
        list_path="/home/mks/printer_data/config/officiall_filas_list.cfg"
        filament_id = self.get_value_by_key(f"filament_{slot}",1)
        section = f"fila{filament_id}"
        config = configparser.ConfigParser()
        config.read(list_path)
        if section in config:
            min_temp = config.getint(section, "min_temp")
            max_temp = config.getint(section, "max_temp")
            return {
            'min_temp': min_temp,
            'max_temp': max_temp,
            }
        else:
            if filament_id > 50 or filament_id < -1:
                self.gcode.respond_raw("filament num error.")
            else:
                self.gcode.respond_raw("officiall_filas_list file error.")
            return None
        
    def get_box_temp_by_slot(self, slot):
        list_path="/home/mks/printer_data/config/officiall_filas_list.cfg"
        filament_id = self.get_value_by_key(f"filament_{slot}",1)
        section = f"fila{filament_id}"
        config = configparser.ConfigParser()
        config.read(list_path)
        if section in config:
            min_temp = config.getint(section, "box_min_temp")
            max_temp = config.getint(section, "box_max_temp")
            return {
            'min_temp': min_temp,
            'max_temp': max_temp,
            }
        else:
            if filament_id > 50 or filament_id < -1:
                self.gcode.respond_raw("filament num error.")
            else:
                self.gcode.respond_raw("officiall_filas_list file error.")
            return None  
        
    def print_sensor_state_to_log(self,eventtime=None):
        b_state = 0
        if self.b_endstop_state:
            b_state = 0
        else:
            b_state = 1
        e_state = 0
        if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
            e_state = 1
        else:
            e_state = 0

        first_tips = self.sensor_str_tips.format(b_endstop_state = b_state,e_endstop_state = e_state)
        second_tips = ""
        
        for i in range(self.get_value_by_key('box_count', 0) * 4):
            stepper = self.printer.lookup_object('box_stepper slot' + str(i))
            r_state = 0
            if not stepper.r_endstop_state:
                r_state = 1
            else:
                r_state = 0
            second_tips = second_tips + self.box_sensor_str_tips.format(slot_num = i, state = r_state)
        All_tips = first_tips + second_tips
        logging.info(f"last sensor state: \n{All_tips}")

def load_config(config):
    return BoxExtras(config)
