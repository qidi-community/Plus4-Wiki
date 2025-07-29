# AHT20-F I2c-based humiditure sensor support
#
# Copyright (C) 2023 Scott Mudge <mail@scottmudge.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
from . import bus


AHT20_F_I2C_ADDR= 0x38

AHT20_F_COMMANDS = {
    'RESET'             :[0xBA], #aht20_f   RESET    
    'AFE_CFG'           :[0xBB, 0x00, 0x00], #aht20_f use to init
    'CCP_CCN'           :[0xBC, 0x00, 0x00], #aht20_f use to init
    'SYS_CFG'           :[0xBE, 0x08, 0x00], #aht20_f use to init
    'OTP_CCP'           :[0x1C], #aht20_f
    'OTP_AFE'           :[0x1B], #aht20_f
    'MEASURE'           :[0xAC, 0x33, 0x00], #aht20_f
    #'RESET'             :[0xBA, 0x08, 0x00]
}

AHT20_F_MAX_BUSY_CYCLES= 5

class AHT20_F:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.reactor = self.printer.get_reactor()
        self.i2c = bus.MCU_I2C_from_config(
            config, default_addr=AHT20_F_I2C_ADDR, default_speed=100000)
        self.report_time = config.getfloat('aht20_f_report_time',0.1,minval=0.1)
        self.temp = self.min_temp = self.max_temp = self.humidity = 0.
        self.sample_timer = self.reactor.register_timer(self._sample_aht20_f)
        self.printer.add_object("aht20_f " + self.name, self)
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        self.gcode = gcode = self.printer.lookup_object('gcode')
        gcode.register_mux_command('BOX_TEMP_READ', "INDEX", 
                                    self.name, self.cmd_READ_TEMP_RH)
        self.is_calibrated  = False
        self.init_sent = False

    def handle_connect(self):
        self._init_aht20_f()
        self.reactor.update_timer(self.sample_timer, self.reactor.NOW)

    def setup_minmax(self, min_temp, max_temp):
        self.min_temp = min_temp
        self.max_temp = max_temp

    def setup_callback(self, cb):
        self._callback = cb

    def get_report_time_delta(self):
        return self.report_time

    def cmd_READ_TEMP_RH(self, gcmd):
        
        self.gcode.respond_raw("%s,temp:%f, humidity:%f" % (self.name, self.temp, self.humidity))

    
    def check_crc8(self, data, length):
        crc = 0xFF  # 初始 CRC 值
        for i in range(length):
            crc ^= data[i]  # 将当前字节与 CRC 当前值进行异或操作
            for j in range(8):  # 对每一位进行处理
                if crc & 0x80:  # 如果 CRC 的最高位是 1
                    crc = (crc << 1) ^ 0x31  # CRC 左移并与多项式 0x31 进行异或
                else:
                    crc <<= 1  # 如果 CRC 的最高位是 0，直接左移
                crc &= 0xFF  # 保证 CRC 始终保持 8 位
        return crc


    def _make_measurement(self):
        if not self.init_sent:
            return False

        data = None

        is_busy = True
        cycles = 0

        try:
            while is_busy:
                # Check if we're constantly busy. If so, send soft-reset
                # and issue warning.
                if is_busy and cycles > AHT20_F_MAX_BUSY_CYCLES:
                    logging.warning("aht20_f: device reported busy after " +
                        "%d cycles, resetting device"% AHT20_F_MAX_BUSY_CYCLES)
                    self._reset_device()
                    data = None
                    break

                cycles += 1
                # Write command for updating temperature+status bit
                self.i2c.i2c_write(AHT20_F_COMMANDS['MEASURE'])
                # Wait 600ms after first read, 75ms minimum
                self.reactor.pause(self.reactor.monotonic() + .600)

                # Read data
                read = self.i2c.i2c_read([], 7)
                if read is None:
                    logging.warning("aht20_f: received data from" +
                                    " i2c_read is None")
                    continue
                data = bytearray(read['response'])
                if len(data) < 7:
                    logging.warning("aht20_f: received bytes less than" +
                                    " expected 7 [%d]"%len(data))
                    continue

                #self.is_calibrated = True if (data[0] & 0b00000100) else False
                #is_busy = True if (data[0] & 0b10000000) else False
                  # 对前 6 个字节进行 CRC 校验, 并且第7bit是0
                if(((data[0] & 0b10000000) == 0) and (data[6] == self.check_crc8(data[:6], 6))):
                    is_busy = False
                else:
                    is_busy = True
                    

            if is_busy:
                return False
        except Exception as e:
            logging.exception("aht20_f: exception encountered" +
                              " reading data: %s"%str(e))
            self._reset_device()
            return False
        

        temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        self.temp = ((temp*200) / 1048576) - 50
        hum = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
        self.humidity = int(hum * 100 / 1048576)

        #logging.info("aht20_f update temp:" + str(self.temp) + ", humidity:" + str(self.humidity))

        # Clamp humidity
        if (self.humidity > 100):
            self.humidity = 100
        elif (self.humidity < 0):
            self.humidity = 0

        return True

    def _reset_device(self):
        if not self.init_sent:
            return

        # Reset device
        self.i2c.i2c_write(AHT20_F_COMMANDS['RESET'])
        # Wait 100ms after reset
        self.reactor.pause(self.reactor.monotonic() + .10)

        self.i2c.i2c_write(AHT20_F_COMMANDS['OTP_CCP']) 
        self.reactor.pause(self.reactor.monotonic() + .10)

        read = self.i2c.i2c_read([], 3) 
        data = bytearray(read['response'])

        AHT20_F_COMMANDS['CCP_CCN'][1] = data[1]
        AHT20_F_COMMANDS['CCP_CCN'][2] = data[2]        
        self.i2c.i2c_write(AHT20_F_COMMANDS['CCP_CCN']) 
        self.reactor.pause(self.reactor.monotonic() + .10)

        self.i2c.i2c_write(AHT20_F_COMMANDS['OTP_AFE']) 
        self.reactor.pause(self.reactor.monotonic() + .10)

        read = self.i2c.i2c_read([], 3) 
        data = bytearray(read['response'])

        AHT20_F_COMMANDS['AFE_CFG'][1] = data[1]
        AHT20_F_COMMANDS['AFE_CFG'][2] = data[2]        
        self.i2c.i2c_write(AHT20_F_COMMANDS['AFE_CFG']) 
        self.reactor.pause(self.reactor.monotonic() + .10)
      
        self.i2c.i2c_write(AHT20_F_COMMANDS['SYS_CFG']) 
        self.reactor.pause(self.reactor.monotonic() + .10)



    def _init_aht20_f(self):
        # Init device
        self.i2c.i2c_write(AHT20_F_COMMANDS['RESET']) 
        # Wait 10ms after init
        self.reactor.pause(self.reactor.monotonic() + .10)
        # self.i2c.i2c_write(AHT20_F_COMMANDS['MEASURE']) #aht20_f
        self.init_sent = True

        if self._make_measurement():
            logging.info("aht20_f: successfully initialized, initial temp: " +
                         "%.3f, humidity: %.3f"%(self.temp, self.humidity))

    def _sample_aht20_f(self, eventtime):
        #if not self._make_measurement():
            #self.temp = self.humidity = .0
            #return self.reactor.NEVER
            #return self.reactor.NEVER
        self._make_measurement()

        if self.temp < self.min_temp or self.temp > self.max_temp:
            #self.printer.invoke_shutdown(
            #    "AHT20_F temperature %0.1f outside range of %0.1f:%.01f"
            #    % (self.temp, self.min_temp, self.max_temp))
            logging.info("AHT20_F temperature outside range")

        measured_time = self.reactor.monotonic()
        print_time = self.i2c.get_mcu().estimated_print_time(measured_time)
        self._callback(print_time, self.temp)
        return measured_time + self.report_time

    def get_status(self, eventtime):
        return {
            'temperature': round(self.temp, 2),
            'humidity': self.humidity,
        }


def load_config(config):
    # Register sensor
    pheater = config.get_printer().lookup_object("heaters")
    pheater.add_sensor_factory("AHT20_F", AHT20_F)
