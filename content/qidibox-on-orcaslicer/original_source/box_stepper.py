from kinematics import extruder
import chelper
from . import force_move
import math
from . import box_extras as be
from . import led

HOMING_START_DELAY = 0.001
ENDSTOP_SAMPLE_TIME = .000015
ENDSTOP_SAMPLE_COUNT = 4
DISABLE_DELAY = 0.05

class BoxExtruderStepper:
    def __init__(self, config):
        #ExtruderStepper
        self.printer = config.get_printer()
        self.extruder_stepper = extruder.ExtruderStepper(config)
        self.stepper = self.extruder_stepper.stepper

        self.stepper_name = config.get_name().split()[1]
        #RunOutButton
        runout_pin = config.get('runout_pin')
        runout_button = be.BoxButton(config, runout_pin, self.runout_button_callback)
        self.r_endstop_state = 0
        self.slot_not_unload = True
        # #RunOutEndstop
        self.r_endstop = be.BoxEndstop(config, self.stepper_name + "_runout", runout_pin, True)
        self.r_endstop.add_stepper(self.stepper)

        #ManualStepper
        self.reactor = self.printer.get_reactor()
        self.next_cmd_time = 0.
        ffi_main, ffi_lib = chelper.get_ffi()
        self.trapq = ffi_main.gc(ffi_lib.trapq_alloc(), ffi_lib.trapq_free)
        self.trapq_append = ffi_lib.trapq_append
        self.trapq_finalize_moves = ffi_lib.trapq_finalize_moves
        self.box_extras = self.printer.load_object(config, 'box_extras')
        self.b_endstop = self.box_extras.b_endstop
        self.e_endstop = self.box_extras.e_endstop
        self.b_endstop.add_stepper(self.stepper)
        self.e_endstop.add_stepper(self.stepper)
        self.b_motion = self.box_extras.b_motion
        stepper_enable = self.printer.lookup_object('stepper_enable')
        self.se = stepper_enable.lookup_enable(self.stepper.get_name())

        #Command
        self.print_stats = self.printer.lookup_object('print_stats')
        self.stepper_num = int(self.stepper_name.replace('slot', ''))
        label_map = {
            0: '1A', 1: '1B', 2: '1C', 3: '1D',
            4: '2A', 5: '2B', 6: '2C', 7: '2D',
            8: '3A', 9: '3B', 10: '3C', 11: '3D',
            12: '4A', 13: '4B', 14: '4C', 15: '4D'
        }
        self.stepper_label = label_map[self.stepper_num]

        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_mux_command('SLOT_UNLOAD', "SLOT", self.stepper_name, self.cmd_SLOT_UNLOAD)
        self.gcode.register_mux_command('EXTRUDER_LOAD', "SLOT", self.stepper_name, self.cmd_EXTRUDER_LOAD)
        self.gcode.register_mux_command('EXTRUDER_UNLOAD', "SLOT", self.stepper_name, self.cmd_EXTRUDER_UNLOAD)
        self.gcode.register_mux_command('SLOT_PROMPT_MOVE', "SLOT", self.stepper_name, self.cmd_SLOT_PROMPT_MOVE)
        self.gcode.register_mux_command('RFID_READ', "SLOT", self.stepper_name, self.cmd_SLOT_RFID_READ)

        #Led
        self.led = led.PrinterPWMLED(config)
        self.red_value = 0
        self.white_value = 0
        self.led_timer = self.reactor.register_timer(self.set_led)
        self.printer.register_event_handler("klippy:ready", self.led_handle_connect)

        #RFID_STATE
        self.rfid_state=0

        #BOX_DRYING_STATE
        self.is_drying = False

    #RunOutButton
    def runout_button_callback(self, eventtime, state):
        if self.is_drying:
            return
        self.r_endstop_state = state
        if self.print_stats.state == "printing" and state:
            runout_num = self.box_extras.get_value_by_key('runout_' + str(self.stepper_num), 0)
            self.box_extras.save_variable('runout_' + str(self.stepper_num), runout_num + 1)
        if state:
            self.box_extras.save_variable(self.stepper_name, 0)
            if self.print_stats.state == "printing" and self.stepper_name == self.box_extras.get_value_by_key("slot_sync", "slot-1"):
                self.gcode.run_script("SET_FILAMENT_SENSOR SENSOR=box_motion_sensor ENABLE=0")#
        else:
            self.box_extras.save_variable(self.stepper_name, 3)
            if self.box_extras.can_load_slot and self.slot_not_unload:
                self.gcode.run_script("RELOAD_ALL RFID=1 FIRST=" + str(self.stepper_num) + "\nM400\n")
    def get_status(self, eventtime=None):
        return {'runout_button': self.r_endstop_state,
                "rfid_state": self.rfid_state,}

    #ManualStepper
    def sync_print_time(self):
        toolhead = self.printer.lookup_object('toolhead')
        print_time = toolhead.get_last_move_time()
        if self.next_cmd_time > print_time:
            toolhead.dwell(self.next_cmd_time - print_time)
        else:
            self.next_cmd_time = print_time
    def do_move(self, movepos, speed, accel=50):
        self.sync_print_time()
        self.stepper.set_trapq(self.trapq)
        axis_r, accel_t, cruise_t, cruise_v = force_move.calc_move_time(movepos, speed, accel)
        self.trapq_append(self.trapq, self.next_cmd_time,
                          accel_t, cruise_t, accel_t,
                          0., 0., 0., 1., 0., 0.,
                          0. * axis_r, cruise_v * axis_r, accel * axis_r)
        self.next_cmd_time = self.next_cmd_time + accel_t + cruise_t + accel_t
        self.stepper.set_position((0., 0., 0.))
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.note_kinematic_activity(self.next_cmd_time)
    def dwell(self, delay):
        self.next_cmd_time += max(0., delay)
    def drip_move(self, newpos, speed, accel, drip_completion):
        self.do_move(newpos[0], speed, accel)
    def disable_stepper(self):
        self.dwell(DISABLE_DELAY)
        self.sync_print_time()
        self.se.motor_disable(self.next_cmd_time)
    def _calc_endstop_rate(self, mcu_endstop, movepos, speed):
        startpos = [0., 0., 0., 0.]
        axes_d = [mp - sp for mp, sp in zip(movepos, startpos)]
        move_d = math.sqrt(sum([d*d for d in axes_d[:3]]))
        move_t = move_d / speed
        max_steps = max([(abs(s.calc_position_from_coord(startpos)
                              - s.calc_position_from_coord(movepos))
                          / s.get_step_dist())
                         for s in mcu_endstop.get_steppers()])
        if max_steps <= 0.:
            return .001
        return move_t / max_steps
    def multi_complete(self, completions):
        if len(completions) == 1:
            return completions[0]
        # Build completion that waits for all completions
        cp = self.reactor.register_callback(lambda e: [c.wait() for c in completions])
        # If any completion indicates an error, then exit main completion early
        for c in completions:
            self.reactor.register_callback(
                lambda e, c=c: cp.complete(1) if c.wait() else 0)
        return cp
    def do_home(self, endstops, movepos, speed, accel, triggered, motion=False):
        self.dwell(DISABLE_DELAY)
        self.sync_print_time()
        pos = [movepos, 0., 0., 0.]
        home_success = False
        endstop_triggers = []
        for mcu_endstop, name in endstops:
            rest_time = self._calc_endstop_rate(mcu_endstop, pos, speed)
            wait = mcu_endstop.home_start(self.next_cmd_time, ENDSTOP_SAMPLE_TIME,
                                          ENDSTOP_SAMPLE_COUNT, rest_time,
                                          triggered=triggered)
            endstop_triggers.append(wait)
        all_endstop_trigger = self.multi_complete(endstop_triggers)
        self.dwell(HOMING_START_DELAY)
        error = None
        try:
            self.drip_move(pos, speed, accel, all_endstop_trigger)
        except self.printer.command_error as e:
            error = "Error during homing move: %s" % (str(e),)
        if motion:
            axis_r, accel_t, cruise_t, cruise_v = force_move.calc_move_time(movepos, speed, accel)
            self.b_motion.init_box_motion(endstops[0][1], speed, accel_t, accel_t + cruise_t)
            self.reactor.update_timer(self.b_motion.box_motion_timer, self.reactor.NOW)
        for mcu_endstop, name in endstops:
            try:
                trigger_time = mcu_endstop.home_wait(self.next_cmd_time)
            except self.printer.command_error as e:
                if error is None:
                    error = "Error during homing %s: %s" % (name, str(e))
                continue
            if trigger_time > 0.:
                self.next_cmd_time = trigger_time + DISABLE_DELAY
                self.trapq_finalize_moves(self.trapq, self.next_cmd_time + 99999.9, self.next_cmd_time + 99999.9)#
                home_success = True
        if motion:
            self.b_motion.init_box_motion(endstops[0][1], 0, 0, 0)
            self.reactor.update_timer(self.b_motion.box_motion_timer, self.reactor.NEVER)
        if error is not None:
            raise self.printer.command_error(error)
        return home_success
    def get_mcu_endstops(self):
        return [es for es, name in self.stepper_endstops]
    def do_home_repeatedly(self, box_endstop, movepos, speed, accel, triggered):
        endstops = box_endstop.get_endstops()
        home_success = self.do_home(endstops, movepos, speed, accel, triggered, True)
        for i in range(3):#
            if box_endstop.scram:
                speed = max([speed / 2, 10])
                box_endstop.set_scram(False)
                self.dwell(1)#
                if movepos > 0:
                    self.do_move(-5, 10, 10)
                else:
                    self.do_move(5, 10, 10)
                home_success = self.do_home(endstops, movepos, speed, accel, triggered, True)
            else:
                break
        if box_endstop.scram:
            home_success = False
        return home_success

    #Command
    def slot_load(self):
        if self.print_stats.state != "printing":
            if self.box_extras.b_endstop_state:
                self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NOW)
                slot_load_length_1 = self.box_extras.get_value_by_key("slot_load_length_1", 3000)
                slot_load_length_1_speed = self.box_extras.get_value_by_key("slot_load_length_1_speed", 80)
                slot_load_length_1_accel = self.box_extras.get_value_by_key("slot_load_length_1_accel", 50)
                home_success = self.do_home(self.b_endstop.get_endstops(), slot_load_length_1, slot_load_length_1_speed, slot_load_length_1_accel, False)
                if home_success:
                    success_count = 0
                    for i in range(5):
                        slot_load_length_2 = self.box_extras.get_value_by_key("slot_load_length_2", -100)
                        slot_load_length_2_speed = self.box_extras.get_value_by_key("slot_load_length_2_speed", 80)
                        slot_load_length_2_accel = self.box_extras.get_value_by_key("slot_load_length_2_accel", 50)
                        self.do_move(slot_load_length_2, slot_load_length_2_speed, slot_load_length_2_accel)
                        slot_load_length_4 = self.box_extras.get_value_by_key("slot_load_length_4", 300)
                        slot_load_length_4_speed = self.box_extras.get_value_by_key("slot_load_length_4_speed", 80)
                        slot_load_length_4_accel = self.box_extras.get_value_by_key("slot_load_length_4_accel", 50)
                        home_success = self.do_home(self.b_endstop.get_endstops(), slot_load_length_4, slot_load_length_4_speed, slot_load_length_4_accel, False)
                        if home_success:
                            success_count += 1
                        else:
                            success_count = 0
                        if success_count > 1:
                            break
                        else:
                            home_success = False
                self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NEVER)
                slot_load_length_3 = self.box_extras.get_value_by_key("slot_load_length_3", -260)
                slot_load_length_3_speed = self.box_extras.get_value_by_key("slot_load_length_3_speed", 80)
                slot_load_length_3_accel = self.box_extras.get_value_by_key("slot_load_length_3_accel", 50)
                self.do_move(slot_load_length_3, slot_load_length_3_speed, slot_load_length_3_accel)
                if home_success:
                    self.box_extras.save_variable(self.stepper_name, 1)
                    self.box_extras.save_variable('last_load_slot', "slot-1")
                    self.disable_stepper()
                    return True
                else:
                    self.gcode.respond_raw("!!Code:QDE_004_001; Message:Slot loading failure, please check the trigger, please reload %s." % (self.stepper_label))
                    self.box_extras.save_variable('retry_step', 'QDE_004_001_' + str(self.stepper_num))
                    self.box_extras.print_sensor_state_to_log()
            else:
                self.gcode.respond_raw("!!Code:QDE_004_002; Message:Extruder has been loaded, cannot load %s." % (self.stepper_label))
                self.box_extras.save_variable('retry_step', 'QDE_004_002_' + str(self.stepper_num))
                self.box_extras.print_sensor_state_to_log()
            self.disable_stepper()
            self.box_extras.save_variable(self.stepper_name, -1)
        return False
    def cmd_SLOT_UNLOAD(self, gcmd):
        if self.print_stats.state != "printing":
            if not self.box_extras.b_endstop_state:
                if self.box_extras.get_value_by_key("last_load_slot", "slot-1") != self.stepper_name:
                    self.slot_not_unload = False
                    self.box_extras.save_variable(self.stepper_name, 3)
                    slot_unload_length_1 = self.box_extras.get_value_by_key("slot_unload_length_1", -3000)
                    slot_unload_length_1_speed = self.box_extras.get_value_by_key("slot_unload_length_1_speed", 100)
                    slot_unload_length_1_accel = self.box_extras.get_value_by_key("slot_unload_length_1_accel", 50)

                    home_success = self.do_home(self.r_endstop.get_endstops(), slot_unload_length_1, slot_unload_length_1_speed, slot_unload_length_1_accel, True)
                    if not home_success:
                        self.gcode.respond_raw("!Code:QDE_004_003; Message:Slot unloading failure, please unload %s again." % (self.stepper_label))
                        self.box_extras.save_variable('retry_step', 'QDE_004_003_' + str(self.stepper_num))
                        self.box_extras.save_variable(self.stepper_name, -1)
                        self.box_extras.print_sensor_state_to_log()
                    self.disable_stepper()
                    self.slot_not_unload = True
                else:
                    self.gcode.respond_raw("!!Code:QDE_004_004; Message:Please unload extruder first.")
                    self.box_extras.save_variable('retry_step', 'QDE_004_004_' + str(self.stepper_num))
                    self.box_extras.print_sensor_state_to_log()
            else:
                self.slot_not_unload = False
                self.box_extras.save_variable(self.stepper_name, 3)
                slot_unload_length_1 = self.box_extras.get_value_by_key("slot_unload_length_1", -3000)
                slot_unload_length_1_speed = self.box_extras.get_value_by_key("slot_unload_length_1_speed", 100)
                slot_unload_length_1_accel = self.box_extras.get_value_by_key("slot_unload_length_1_accel", 50)

                home_success = self.do_home(self.r_endstop.get_endstops(), slot_unload_length_1, slot_unload_length_1_speed, slot_unload_length_1_accel, True)
                if not home_success:
                    self.gcode.respond_raw("!Code:QDE_004_003; Message:Slot unloading failure, please unload %s again." % (self.stepper_label))
                    self.box_extras.save_variable('retry_step', 'QDE_004_003_' + str(self.stepper_num))
                    self.box_extras.save_variable(self.stepper_name, -1)
                    self.box_extras.print_sensor_state_to_log()
                self.disable_stepper()
                self.slot_not_unload = True
    def cmd_EXTRUDER_LOAD(self, gcmd):
        if self.box_extras.tool_change.exclude_tool:
            return
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.wait_moves()
        if self.r_endstop_state:
            self.gcode.respond_info("Code:QDE_004_005; Message:Please load the filament to %s first.\n" % (self.stepper_label))
            self.box_extras.save_variable('retry_step', 'QDE_004_005_' + str(self.stepper_num))
            self.box_extras.print_sensor_state_to_log()
            self.gcode.run_script_from_command("PAUSE")
            return
        elif self.box_extras.get_value_by_key("last_load_slot", "slot-1") == self.stepper_name and self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5 and self.box_extras.get_value_by_key("slot_sync", "slot-1") == self.stepper_name:
            self.gcode.respond_info("%s has been sync with Extruder." % (self.stepper_label))
            return
        home_success = False
        if self.box_extras.b_endstop_state:
            self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NOW)
            self.box_extras.save_variable(self.stepper_name, 3)
            extruder_load_length_1 = self.box_extras.get_value_by_key("extruder_load_length_1", 3000)
            extruder_load_length_1_speed = self.box_extras.get_value_by_key("extruder_load_length_1_speed", 80)
            extruder_load_length_1_accel = self.box_extras.get_value_by_key("extruder_load_length_1_accel", 50)
            home_success = self.do_home(self.b_endstop.get_endstops(), extruder_load_length_1, extruder_load_length_1_speed, extruder_load_length_1_accel, False)
            self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NEVER)
        if (not self.box_extras.b_endstop_state) and self.box_extras.get_value_by_key('last_load_slot','slot-1') == self.stepper_name:
            home_success = True
        if home_success:
            self.box_extras.save_variable('last_load_slot', self.stepper_name)
            self.reactor.update_timer(self.box_extras.e_endstop_timer, self.reactor.NOW)
            extruder_load_length_2 = self.box_extras.get_value_by_key("extruder_load_length_2", 1060)
            extruder_load_length_2_speed = self.box_extras.get_value_by_key("extruder_load_length_2_speed", 100)
            extruder_load_length_2_accel = self.box_extras.get_value_by_key("extruder_load_length_2_accel", 300)
            home_success = self.do_home_repeatedly(self.e_endstop, extruder_load_length_2, extruder_load_length_2_speed, extruder_load_length_2_accel, False)
            if home_success:
                if self.e_endstop.scram:
                    home_success = False
                    self.e_endstop.set_scram(False)
            else:
                extruder_load_length_3 = self.box_extras.get_value_by_key("extruder_load_length_3", 200)
                extruder_load_length_3_speed = self.box_extras.get_value_by_key("extruder_load_length_3_speed", 10)
                extruder_load_length_3_accel = self.box_extras.get_value_by_key("extruder_load_length_3_accel", 50)
                home_success = self.do_home_repeatedly(self.e_endstop, extruder_load_length_3, extruder_load_length_3_speed, extruder_load_length_3_accel, False)
                if not home_success:
                    self.gcode.run_script_from_command("CLEAR_OOZE")
                loop_num = 0
                while not home_success:
                    if loop_num == 0:
                        retry_num = self.box_extras.get_value_by_key("load_retry_num", 0) + 1
                        self.box_extras.save_variable('load_retry_num', retry_num)
                    # self.dwell(1)
                    # self.do_move(-50, 100, 300)
                    # self.dwell(1)
                    if loop_num == 0:
                        self.gcode.run_script_from_command("G1 Y300 F9000\nG1 X0 F9000\nG1 X0 Y0 F15000\nM400")
                        self.gcode.run_script_from_command("G4 P2000\nM400")
                        if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
                            self.gcode.run_script_from_command("MOVE_TO_TRASH\n")
                            home_success = True
                            break    
                        self.dwell(1)
                        self.do_move(-50, 100, 300)
                        self.dwell(1)
                    elif loop_num == 1:
                        self.gcode.run_script_from_command("G1 X0 Y300 F15000\nG1 X35 F15000\nG1 Y305 F15000\nG1 X305 Y305 F15000\nM400")
                        self.gcode.run_script_from_command("G4 P2000\nM400")
                        if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
                            self.gcode.run_script_from_command("MOVE_TO_TRASH\n")
                            home_success = True
                            break    
                        self.dwell(1)
                        self.do_move(-50, 100, 300)
                        self.dwell(1)
                    loop_num = loop_num + 1
                    home_success = self.do_home(self.e_endstop.get_endstops(), 100, 100, 100, False, False)
                    #home_success = self.do_home_repeatedly(self.e_endstop, extruder_load_length_3, extruder_load_length_3_speed, extruder_load_length_3_accel, False)
                    if home_success:
                        self.gcode.run_script_from_command("MOVE_TO_TRASH\n")
                        break
                    else:
                        self.gcode.run_script_from_command("G4 P2000\nM400")
                        if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
                            self.gcode.run_script_from_command("MOVE_TO_TRASH\n")
                            home_success = True
                            break    
                    if loop_num == 2:
                        self.gcode.run_script_from_command("MOVE_TO_TRASH\n")
                        break
            self.reactor.update_timer(self.box_extras.e_endstop_timer, self.reactor.NEVER)
        if home_success:
            self.box_extras.save_variable(self.stepper_name, 2)
            self.slot_sync(True)
        else:
            slot_sync = self.box_extras.get_value_by_key("slot_sync", "slot-1")
            if slot_sync == "slot-1":
                slot_loaded = self.stepper_name
                self.box_extras.save_variable(self.stepper_name, -2)
            else:
                slot_loaded = slot_sync
            self.gcode.respond_info("Code:QDE_004_006; Message:Extruder loading failure.")
            self.box_extras.save_variable('retry_step', 'QDE_004_006_' + str(self.stepper_num))
            self.box_extras.print_sensor_state_to_log()
            if self.print_stats.state == "printing":
                self.gcode.run_script_from_command("PAUSE")
        self.disable_stepper()
        self.dwell(DISABLE_DELAY)
        self.sync_print_time()
    def cmd_EXTRUDER_UNLOAD(self, gcmd, can_cut = True):
        if self.box_extras.tool_change.exclude_tool:
            return
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.wait_moves()
        if self.print_stats.state != "printing":
            if can_cut:
                if self.printer.lookup_object('hall_filament_width_sensor').diameter > 0.5:
                    self.gcode.run_script_from_command("CUT_FILAMENT\nMOVE_TO_TRASH\n")
            else:
                pass
        elif self.r_endstop_state:
            if self.box_extras.get_value_by_key("auto_reload_detect", 0) == 1:
                self.flush_all_filament()
                self.switch_next_slot()
            else:
                self.gcode.respond_info("Code:QDE_004_016; Message:The filament has been exhausted, please load the filament to %s." % (self.stepper_label))
                self.box_extras.save_variable('retry_step', 'QDE_004_016_00')
                self.gcode.run_script_from_command("PAUSE")
            return
        self.slot_sync(False)
        if self.box_extras.b_endstop_state:
            self.box_extras.save_variable(self.stepper_name, -1)
            self.gcode.respond_info("Code:QDE_004_007; Message:Extruder not loaded.")
            self.box_extras.save_variable('retry_step', 'QDE_004_007_' + str(self.stepper_num))
            self.box_extras.print_sensor_state_to_log()
            if self.print_stats.state == "printing":
                self.gcode.run_script_from_command("PAUSE")
        else:
            self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NOW)
            self.box_extras.save_variable(self.stepper_name, 3)
            extruder_unload_length_1 = self.box_extras.get_value_by_key("extruder_unload_length_1", -1320)
            extruder_unload_length_1_speed = self.box_extras.get_value_by_key("extruder_unload_length_1_speed", 100)
            extruder_unload_length_1_accel = self.box_extras.get_value_by_key("extruder_unload_length_1_accel", 50)

            # box_index_num = self.stepper_num // 4 + 1
            # heaters = self.printer.lookup_object("heaters")
            # heater = heaters.lookup_heater("heater_box" + str(box_index_num))
            # if heater.target_temp > 45.:
            #     if extruder_unload_length_1_speed == 100:
            #         extruder_unload_length_1_speed = 80
                
            home_success = self.do_home_repeatedly(self.b_endstop, extruder_unload_length_1, extruder_unload_length_1_speed, extruder_unload_length_1_accel, True)
            self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NEVER)
            if home_success:
                self.box_extras.save_variable('last_load_slot', "slot-1")
                if self.b_endstop.scram:
                    home_success = False
                    self.b_endstop.set_scram(False)
            if home_success:
                extruder_unload_length_2 = self.box_extras.get_value_by_key("extruder_unload_length_2", -260)
                extruder_unload_length_2_speed = self.box_extras.get_value_by_key("extruder_unload_length_2_speed", 80)
                extruder_unload_length_2_accel = self.box_extras.get_value_by_key("extruder_unload_length_2_accel", 50)
                self.do_move(extruder_unload_length_2, extruder_unload_length_2_speed, extruder_unload_length_2_accel)
                self.box_extras.save_variable(self.stepper_name, 1)
                #self.slot_sync(False)
                self.disable_stepper()
                return True
            else:
                self.gcode.respond_info("Code:QDE_004_009; Message:Extruder unloading failure.")
                self.box_extras.save_variable('retry_step', 'QDE_004_009_' + str(self.stepper_num))
                self.box_extras.save_variable(self.stepper_name, -2)
                self.box_extras.print_sensor_state_to_log()
                if self.print_stats.state == "printing":
                    self.gcode.run_script_from_command("PAUSE")
            self.disable_stepper()
    def cmd_SLOT_PROMPT_MOVE(self, gcmd):
        slot_state = self.box_extras.get_value_by_key(self.stepper_name, 0)
        if slot_state == 1:
            self.do_move(20, 50, 50)
            self.dwell(0.5)
            self.do_move(-20, 50, 50)
            self.disable_stepper()
    def slot_sync(self, value):
        if value:
            box_count = self.box_extras.get_value_by_key("box_count", 0)
            if box_count > 0:
                for i in range(0,box_count * 4):
                        loop_stepper = self.printer.lookup_object('box_stepper slot' + str(i))
                        loop_stepper.slot_sync(False)
            self.extruder_stepper.sync_to_extruder('extruder')
            self.box_extras.save_variable("slot_sync", self.stepper_name)
        else:
            self.extruder_stepper.sync_to_extruder('')
            self.box_extras.save_variable("slot_sync", "slot-1")
    def flush_all_filament(self):
        hall = self.printer.lookup_object('hall_filament_width_sensor')
        flush_success = False
        for i in range(50):
            if hall.diameter > 0.5:
                self.gcode.run_script_from_command("G1 E100 F300\nG1 E-1 F1800\nM106 S255\nM400\nG4 P5000\nCLEAR_FLUSH\nM106 S0")
            else:
                flush_success = True
                self.gcode.run_script_from_command("G1 E25 F300")
                break
        self.slot_sync(False)
        self.disable_stepper()
        if not flush_success:
            self.gcode.respond_info("Code:QDE_004_017; Message:Filament flush failed, please clean and then load the filament in %s." % (self.stepper_label))
            self.box_extras.save_variable('retry_step', 'QDE_004_017_00')
            self.gcode.run_script_from_command("PAUSE")
    def switch_next_slot(self):
        auto_reload = self.box_extras.get_value_by_key("auto_reload_detect", False)
        next_slot = -1
        if auto_reload:
            vendor_slot = self.box_extras.get_value_by_key("vendor_" + self.stepper_name, None)
            color_slot = self.box_extras.get_value_by_key("color_" + self.stepper_name, None)
            filament_slot = self.box_extras.get_value_by_key("filament_" + self.stepper_name, None)
            if vendor_slot is None or color_slot is None or filament_slot is None:
                self.gcode.respond_info("Code:QDE_004_018; Message:No filament specified, %s cannot be automatically replaced." % (self.stepper_label))
                self.box_extras.save_variable('retry_step', 'QDE_004_018_00')
                return next_slot
            box_count = 4 * self.box_extras.get_value_by_key("box_count", 1)#
            for i in range(self.stepper_num + 1, self.stepper_num + box_count):
                if i >= box_count:
                    i = i - box_count
                next_vendor_slot = self.box_extras.get_value_by_key("vendor_slot" + str(i), None)
                next_color_slot = self.box_extras.get_value_by_key("color_slot" + str(i), None)
                next_filament_slot = self.box_extras.get_value_by_key("filament_slot" + str(i), None)
                if vendor_slot == next_vendor_slot and color_slot == next_color_slot and filament_slot == next_filament_slot:
                    slot_state = self.box_extras.get_value_by_key("slot" + str(i), 0)
                    if slot_state == 1:
                        next_slot = i
                        break
            if next_slot >= 0:
                value_t = self.box_extras.get_key_by_value(self.stepper_name, "value_t" + str(self.stepper_num), 'value_t')
                self.box_extras.save_variable(value_t, "slot" + str(next_slot))
            else:
                self.gcode.respond_info("Code:QDE_004_022; Message:No replaceable slot found.")
                self.box_extras.save_variable('retry_step', 'QDE_004_022_00')
        return next_slot
    
    def cmd_SLOT_RFID_READ(self,gcmd):
        if not self.rfid_state == 0:
            return True
        if not self.box_extras.b_endstop_state:
            self.gcode.respond_info("Code:QDE_004_011; Message:Detected that filament have been loaded, please unload filament first" )
            self.box_extras.save_variable('retry_step', 'QDE_004_011_00')
            self.rfid_state = 0
            return True
        self.rfid_state = 1
        self.box_extras.box_button_state = 1
        rfid_device = f"card_reader_{(self.stepper_num // 2) + 1}"
        box_rfid = self.printer.lookup_object('box_rfid ' + rfid_device)
        box_rfid.start_rfid_read(self)
        #stepper_move
        home_success = False
        self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NOW)
        home_success = self.do_home(self.b_endstop.get_endstops(), 2000, 80, 50, False)
        if home_success:
            self.dwell(0.5)
            self.do_move(-700, 90, 50)
            self.dwell(0.5)
        home_success = False
        home_success = self.do_home(self.b_endstop.get_endstops(), 2000, 80, 50, False)
        if home_success:
            self.reactor.update_timer(self.box_extras.b_endstop_timer, self.reactor.NEVER)
            slot_load_length_3 = self.box_extras.get_value_by_key("slot_load_length_3", -260)
            slot_load_length_3_speed = self.box_extras.get_value_by_key("slot_load_length_3_speed", 80)
            slot_load_length_3_accel = self.box_extras.get_value_by_key("slot_load_length_3_accel", 50)
            self.do_move(slot_load_length_3, slot_load_length_3_speed, slot_load_length_3_accel)
            self.dwell(0.5)
            self.box_extras.save_variable(self.stepper_name, 1)
        else:
            if not self.r_endstop_state:
                self.gcode.respond_raw("!!Code:QDE_004_019; Message:Please check if your PTFE Tube is bent")
                self.box_extras.save_variable('retry_step', 'QDE_004_019_00')
            else:
                self.gcode.respond_raw("!!Code:QDE_004_020; Message:Detected that the filament has been unloaded, please reload.")
                self.box_extras.save_variable('retry_step', 'QDE_004_019_00')
        self.disable_stepper()
        self.rfid_state = 0
        self.box_extras.box_button_state = 0
        box_rfid.stop_read()
        if not home_success:
            return False
        return True

    #Led
    def set_led(self, eventtime):
        led_state = self.box_extras.get_value_by_key(self.stepper_name, 0)
        update_time = 1
        if led_state == 0:
            self.red_value = 0
            if self.white_value == 0:
                self.white_value = 1
                update_time = 0.5
            else:
                self.white_value = 0
                update_time = 1.5
        elif led_state == 1:
            self.red_value = 0
            self.white_value = 1
        elif led_state == 2 or led_state == 3:
            update_time = 0.1
            self.red_value = 0
            if int(eventtime) % 2 == 0:
                self.white_value = int(eventtime * 10) % 10 / 10
            else:
                self.white_value = 1 - (int(eventtime * 10) % 10 / 10)
        elif led_state == -1:
            self.red_value = 1
            self.white_value = 0
        elif led_state == -2:
            update_time = 0.1
            if int(eventtime) % 2 == 0:
                self.red_value = int(eventtime * 10) % 10 / 10
            else:
                self.red_value = 1 - (int(eventtime * 10) % 10 / 10)
            self.white_value = 0
        elif led_state == -3:
            if self.red_value == 0:
                self.red_value = 1
                update_time = 0.5
            else:
                self.red_value = 0
                update_time = 1.5
            self.white_value = 0
        else:
            self.red_value = 0
            self.white_value = 0
        self.led.update_leds([(self.red_value, 0, 0, self.white_value)], None)
        return eventtime + update_time

    def led_handle_connect(self):
        self.reactor.update_timer(self.led_timer, self.reactor.NOW)

def load_config_prefix(config):
    return BoxExtruderStepper(config)
