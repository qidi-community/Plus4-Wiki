# -*- coding: utf-8 -*-
import os, time, logging
import configparser
import shutil
import pyudev
import filecmp
import re

class BoxDetect:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object("gcode")
        self.serial_monitor_timer = reactor.register_timer(self.monitor_serial_by_id)
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.print_stats = self.printer.lookup_object('print_stats')

        self.previous_tty_count = 0
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='tty')
        self.config_mcu_serial = {}

        self.dst_box_cfg = '/home/mks/printer_data/config/box.cfg'
        self.src_box_cfg_with_0 = '/home/mks/cfg_with_0'
        self.src_box_cfg_with_1 = '/home/mks/cfg_with_1'
        self.src_box_cfg_with_2 = '/home/mks/cfg_with_2'
        self.src_box_cfg_with_3 = '/home/mks/cfg_with_3'
        self.src_box_cfg_with_4 = '/home/mks/cfg_with_4'

    def _handle_ready(self):
        self.get_config_mcu_serials()
        self.klippy_state = 'ready'
        if self.printer.get_start_args().get('debugoutput') is None:
            reactor = self.printer.get_reactor()
            reactor.update_timer(self.serial_monitor_timer, reactor.NOW)

    def get_config_mcu_serials(self):
        config = configparser.ConfigParser(delimiters=':')
        config_files = ["/home/mks/printer_data/config/box1.cfg", "/home/mks/printer_data/config/box2.cfg"]
        for config_file in config_files:
            if os.path.exists(config_file):
                config.read(config_file)
            box_name = os.path.basename(config_file).split('.')[0]
            section_name = f"mcu {box_name}"
            if config.has_section(section_name):
                serial = config.get(section_name, 'serial')
                self.config_mcu_serial[box_name] = serial

    def monitor_serial_by_id(self, eventtime):
        if not self.printer.lookup_object('idle_timeout').get_status(eventtime)['state'] == "Ready":
            return eventtime + 5.
        if self.print_stats.state == "printing":
            return eventtime + 5.
        current_devices = {}
        for device in reversed(list(self.context.list_devices(subsystem='tty'))):
            device_node = device.device_node
            devlinks = device.get('DEVLINKS', '').split()
            serial_by_id = [link for link in devlinks if '/dev/serial/by-id/' in link and 'QIDI_BOX_V1' in link]
            other_id = [link for link in devlinks if '/dev/serial/by-id/' in link and 'QIDI_BOX_V2' in link]
            if other_id:
                match = re.search(r"V2_(\d+\.\d+\.\d+)", other_id[0])
                mcu_version = int(match.group(1).replace('.', ''))  
                
                bin_files = [f for f in os.listdir('/home/mks/') if f.startswith('mcu_box_to_v1')]
                if bin_files:
                    logging.info("Start updated box mcu")
                    script = '/home/mks/mcu_update_BOX_to_v1.sh /home/mks/' + bin_files[0] + ' ' + other_id[0] 
                    os.system(script)
                    return eventtime + 30.
            if serial_by_id:
                match = re.search(r"V1_(\d+\.\d+\.\d+)", serial_by_id[0])
                mcu_version = int(match.group(1).replace('.', ''))
                
                bin_files = [f for f in os.listdir('/home/mks/') if f.startswith('mcu_box_to_v1')]
                if bin_files:
                    bin_name = bin_files[0]
                    file_version_str = bin_name.split('v1_')[1].split('.bin')[0]
                    file_version = int(file_version_str.replace('.', ''))

                    if file_version > mcu_version:
                        script = '/home/mks/mcu_update_BOX_to_v1.sh /home/mks/' + bin_name + ' ' + serial_by_id[0] 
                        os.system(script)
                        return eventtime + 30.
                current_devices[device_node] = serial_by_id[0]
        device_count = len(current_devices)


        if device_count == 1:
            condition_1 = self.count_box_includes(f"/home/mks/printer_data/config/box.cfg") == device_count
            config_serial = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",1)
            condition_2 = config_serial == list(current_devices.values())[0]
            if not condition_1 or not condition_2:
                if not condition_1:
                    shutil.copy(self.src_box_cfg_with_1, self.dst_box_cfg)
                    self._update_config_file(current_devices, 1)
                    self.gcode.run_script("SAVE_VARIABLE VARIABLE=box_count VALUE=%d"% (device_count))
                else:
                    self._update_config_file(current_devices, 1)
                self._request_restart()
        elif device_count == 2:
            config_serial_1 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",1)
            config_serial_2 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",2)
            condition_1 = self.count_box_includes(f"/home/mks/printer_data/config/box.cfg") == device_count
            condition_2 = (config_serial_1 == list(current_devices.values())[0]) and (config_serial_2 == list(current_devices.values())[1])
            if not condition_1 or not condition_2:
                if not condition_1:
                    shutil.copy(self.src_box_cfg_with_2, self.dst_box_cfg)
                    for i in range(1, device_count + 1):
                        self._update_config_file(current_devices, i)
                    self.gcode.run_script("SAVE_VARIABLE VARIABLE=box_count VALUE=%d"% (device_count))
                else:
                    for i in range(1, device_count + 1):
                        self._update_config_file(current_devices, i)
                self._request_restart()
        elif device_count == 3:
            config_serial_1 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",1)
            config_serial_2 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",2)
            config_serial_3 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",3)
            condition_1 = self.count_box_includes(f"/home/mks/printer_data/config/box.cfg") == device_count
            condition_2 = (config_serial_1 == list(current_devices.values())[0]) and (config_serial_2 == list(current_devices.values())[1]) and (config_serial_3 == list(current_devices.values())[2])
            if not condition_1 or not condition_2:
                if not condition_1:
                    shutil.copy(self.src_box_cfg_with_3, self.dst_box_cfg)
                    for i in range(1, device_count + 1):
                        self._update_config_file(current_devices, i)
                    self.gcode.run_script("SAVE_VARIABLE VARIABLE=box_count VALUE=%d"% (device_count))
                else:
                    for i in range(1, device_count + 1):
                        self._update_config_file(current_devices, i)
                self._request_restart()
        elif device_count == 4:
            config_serial_1 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",1)
            config_serial_2 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",2)
            config_serial_3 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",3)
            config_serial_4 = self.get_check_serials_id(f"/home/mks/printer_data/config/box.cfg",4)
            condition_1 = self.count_box_includes(f"/home/mks/printer_data/config/box.cfg") == device_count
            condition_2 = (config_serial_1 == list(current_devices.values())[0]) and (config_serial_2 == list(current_devices.values())[1]) and (config_serial_3 == list(current_devices.values())[2]) and (config_serial_4 == list(current_devices.values())[3])
            if not condition_1 or not condition_2:
                if not condition_1:
                    shutil.copy(self.src_box_cfg_with_4, self.dst_box_cfg)
                    for i in range(1, device_count + 1):
                        self._update_config_file(current_devices, i)
                    self.gcode.run_script("SAVE_VARIABLE VARIABLE=box_count VALUE=%d"% (device_count))
                else:
                    for i in range(1, device_count + 1):
                        self._update_config_file(current_devices, i)
                self._request_restart()
        elif device_count == 0:
            if not filecmp.cmp(self.src_box_cfg_with_0, self.dst_box_cfg, shallow=False):
                self.gcode.run_script("SAVE_VARIABLE VARIABLE=box_count VALUE=0")
                shutil.copy(self.src_box_cfg_with_0, self.dst_box_cfg)
                self._request_restart()
        try:
            if self.printer.lookup_object('box_extras'):
                if not self.printer.lookup_object('box_extras').get_value_by_key('box_count') == device_count:
                    self.printer.lookup_object('box_extras').save_variable('box_count',device_count)
        except Exception:
            pass
        return eventtime + 5. 

    def _update_config_file(self, current_devices, box_index=1):
        config_path = f"/home/mks/printer_data/config/box.cfg"
        box_name = f"mcu_box{box_index}"
        current_device_path = list(current_devices.values())[box_index-1]
        config = configparser.ConfigParser(delimiters=':')
        config.read(config_path)
        section_name = f"mcu {box_name}"
        config.set(section_name, 'serial', current_device_path)
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        logging.info(f"Updated new device path: {current_device_path}")
        self.get_config_mcu_serials()

    def _request_restart(self):
        toolhead = self.printer.lookup_object('toolhead')
        print_time = toolhead.get_last_move_time()
        self.printer.send_event("gcode:request_restart", print_time)
        toolhead.dwell(0.500)
        toolhead.wait_moves()
        self.printer.request_exit('error_exit')

    def get_check_serials_id(self,config_path,box_index):
        config = configparser.ConfigParser(delimiters=':')
        if os.path.exists(config_path):
            config.read(f"/home/mks/printer_data/config/box.cfg")
        section_name = f"mcu mcu_box{box_index}"
        serial = ""
        if config.has_section(section_name):
            serial = config.get(section_name, 'serial')
            return serial
    
    def count_box_includes(self,file_path):
        with open(file_path, 'r') as file:
            config_content = file.read()
        pattern = r'\[include box(\d+)\.cfg\]'
        matches = re.findall(pattern, config_content)
        count = len(matches)
        return count

def monitor_serial_devices(self):
        DST_BOX_CFG = '/home/mks/printer_data/config/box.cfg'
        SRC_BOX_CFG_WITH_0 = '/home/mks/cfg_with_0'
        SRC_BOX_CFG_WITH_1 = '/home/mks/cfg_with_1'
        SRC_BOX_CFG_WITH_2 = '/home/mks/cfg_with_2'
        SRC_BOX_CFG_WITH_3 = '/home/mks/cfg_with_3'
        SRC_BOX_CFG_WITH_4 = '/home/mks/cfg_with_4'
        context = pyudev.Context()
        current_devices = {}
        try:
            for device in context.list_devices(subsystem='tty'):
                device_node = device.device_node
                devlinks = device.get('DEVLINKS', '').split()
                serial_by_id = next(
                    (link for link in devlinks if '/dev/serial/by-id/' in link and 'QIDI_BOX_V1' in link),
                    None
                )
                bootloader1_by_id = next(
                    (link for link in devlinks if '/dev/serial/by-id/' in link and 'MKS_COLOR0_BOOT' in link),
                    None
                )
                bootloader2_by_id = next(
                    (link for link in devlinks if '/dev/serial/by-id/' in link and 'MKS_COLOR_BOOT' in link),
                    None
                )
                if bootloader1_by_id:
                    return
                if bootloader2_by_id:
                    return
                if serial_by_id:
                    current_devices[device_node] = serial_by_id
            current_devices = dict(reversed(list(current_devices.items())))
            device_count = len(current_devices)
            logging.info(f"Detected {device_count} devices: {current_devices}")

            if device_count == 0:
                shutil.copy(SRC_BOX_CFG_WITH_0, DST_BOX_CFG)
                update_monitor_config_file(self,current_devices, 0)
            elif device_count == 1:
                shutil.copy(SRC_BOX_CFG_WITH_1, DST_BOX_CFG)
                for i in range(1, device_count + 1):
                    update_monitor_config_file(self,current_devices, i)
            elif device_count == 2:
                shutil.copy(SRC_BOX_CFG_WITH_2, DST_BOX_CFG)
                for i in range(1, device_count + 1):
                    update_monitor_config_file(self,current_devices, i)
            elif device_count == 3:
                shutil.copy(SRC_BOX_CFG_WITH_3, DST_BOX_CFG)
                for i in range(1, device_count + 1):
                    update_monitor_config_file(self,current_devices, i)
            elif device_count == 4:
                shutil.copy(SRC_BOX_CFG_WITH_4, DST_BOX_CFG)
                for i in range(1, device_count + 1):
                    update_monitor_config_file(self,current_devices, i)
            else:
                logging.warning("Unexpected device count or mismatch detected.")
            #shutil.copy('/home/mks/cfg_with_0', '/home/mks/printer_data/config/box.cfg')
        except Exception as e:
            logging.error(f"Error monitoring serial devices: {e}")

def is_monitor_config_file_empty(self, file_path):
        config = configparser.ConfigParser(delimiters=':')
        if os.path.exists(file_path):
            config.read(file_path)
            return not config.sections()
        return True

def update_monitor_config_file(self, current_devices, box_index=1):
    if box_index != 0:
        config_path = f"/home/mks/printer_data/config/box.cfg"
        box_name = f"mcu_box{box_index}"
        current_device_path = list(current_devices.values())[box_index-1]
        config = configparser.ConfigParser(delimiters=':')
        config.read(config_path)
        section_name = f"mcu {box_name}"
        config.set(section_name, 'serial', current_device_path)
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        logging.info(f"Updated new device path: {current_device_path}")
        variables_path = "/home/mks/printer_data/config/saved_variables.cfg"
        v_config = configparser.ConfigParser()
        v_config.read(variables_path)
        v_config.set("Variables", "box_count", str(box_index))
        with open(variables_path, "w") as configfile:
            v_config.write(configfile)
    else:
        variables_path = "/home/mks/printer_data/config/saved_variables.cfg"
        v_config = configparser.ConfigParser()
        v_config.read(variables_path)
        v_config.set("Variables", "box_count", "0")
        with open(variables_path, "w") as configfile:
            v_config.write(configfile)

def add_printer_objects(config):
    config.get_printer().add_object('boxdetect', BoxDetect(config))
