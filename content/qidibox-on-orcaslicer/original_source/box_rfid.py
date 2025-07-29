from . import bus

class BoxRFID:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[1]
        self.spi = bus.MCU_SPI_from_config(config, 0, default_speed=5000000, share_type="spi_cs")
        self.mcu = self.spi.get_mcu()
        self.oid = self.mcu.create_oid()

        self.fm17550_read_card = None
        self.mcu.add_config_cmd("query_fm17550 oid=%d rest_ticks=0" % (self.oid), on_restart=True)
        self.mcu.add_config_cmd("config_fm17550 oid=%d spi_oid=%d" % (self.oid, self.spi.get_oid()))
        self.mcu.register_config_callback(self._build_config)

        self.gcode = self.printer.lookup_object('gcode')

        self.read_rfid_timer = None
        self.rfid_read_attempts = 0
        self.rfid_read_start_time = 0
        self.max_read_time = 30.0
        self.get_message_count = 1
        self.temp_message_1 = None
        self.temp_message_2 = None
        self.stepper = None
        self.had_get_value = False

    def _build_config(self):
        cmdqueue = self.spi.get_command_queue()
        self.fm17550_read_card = self.mcu.lookup_query_command(
            "fm17550_read_card_cb oid=%c",
            "fm17550_read_card_return oid=%c status=%c data=%*s",
            oid=self.oid, cq=cmdqueue
        )

    def read_card(self):
        params = self.fm17550_read_card.send([self.oid])
        return params

    def read_card_from_slot(self):
        params = self.read_card()
        return params
    def _schedule_rfid_read(self, eventtime):
        if eventtime - self.rfid_read_start_time > self.max_read_time:
            self.read_rfid_timer = None
            self.rfid_read_attempts = 0
            if not self.had_get_value:
                self.gcode.respond_info("%s did not recognize the filament" % (self.stepper.stepper_label))
            self.stop_read()
            return self.stepper.reactor.NEVER
        
        params = self.read_card_from_slot()
        if params['status'] == 1:
            if self.get_message_count % 2 == 0:
                self.temp_message_1 = params
                self.get_message_count += 1
            elif not self.get_message_count % 2 ==0 :
                self.temp_message_2 = params
                self.get_message_count += 1
            if self.get_message_count == 3:
                if self.temp_message_1['data'] == self.temp_message_2['data']:
                    self.read_rfid_timer = None
                    self.rfid_read_attempts = 0
                    data = params['data']
                    filament = data[0]
                    color = data[1]
                    if filament < 1 or filament > 99 or color < 1 or color > 24 :
                        self.read_rfid_timer = None
                        self.rfid_read_attempts = 0
                        self.gcode.respond_info("Unrecognized label read in %s" % (self.stepper.stepper_label))
                        self.stop_read()
                        return self.stepper.reactor.NEVER
                    self.stepper.box_extras.save_variable("filament_" + self.stepper.stepper_name, filament)
                    self.stepper.box_extras.save_variable("color_" + self.stepper.stepper_name, color)
                    self.stepper.box_extras.save_variable("vendor_" + self.stepper.stepper_name, 1)
                    self.had_get_value = True
                self.read_rfid_timer = None
                self.rfid_read_attempts = 0
                self.stop_read()
                return self.stepper.reactor.NEVER
        self.rfid_read_attempts += 1
        return eventtime + 0.1

    def start_rfid_read(self,stepper):
        self.stepper = stepper
        self.read_card()
        self.get_message_count = 1
        self.temp_message_1 = None
        self.temp_message_2 = None
        self.rfid_read_attempts = 0
        self.had_get_value = False
        self.rfid_read_start_time = stepper.reactor.monotonic()
        if self.read_rfid_timer is not None:
            self.stop_read()
        self.read_rfid_timer = stepper.reactor.register_timer(
            self._schedule_rfid_read, stepper.reactor.NOW)

    def stop_read(self):
        if self.read_rfid_timer is not None:
            if not self.had_get_value:
                self.gcode.respond_info("%s did not recognize the filament" % (self.stepper.stepper_label))
            self.stepper.reactor.unregister_timer(self.read_rfid_timer)
            self.read_rfid_timer = None
            self.rfid_read_attempts = 0

def load_config_prefix(config):
    return BoxRFID(config)
