from machine import ADC, Pin, SoftI2C, PWM
import time
import network
import urequests as requests
import ujson as json
import ubinascii
import socket

class Gyro:
    def __init__(self, roll: float, pitch: float, yaw: float):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw

    def multiplier(self, multiplier):
        self.roll *= multiplier
        self.pitch *= multiplier
        self.yaw *= multiplier


class Acceleration:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def multiplier(self, multiplier):
        self.x *= multiplier
        self.y *= multiplier
        self.z *= multiplier


class SensorOperator:
    def __init__(self):

        self.type_list = []
        self.is_type_active = {}

        self.signal_data = {}
        self.alpha_ratio = 1
        self.threshold = 0.2

        self.sensor_data_attributes = {
            Gyro: ['roll', 'pitch', 'yaw'],
            Acceleration: ['x', 'y', 'z'],
        }

    def setLowPassRatio(self, low_pass_ratio):
        if low_pass_ratio < 0 or low_pass_ratio > 1:
            raise ValueError("Low-pass ratio must be in the range of [0:1]")
        self.alpha_ratio = low_pass_ratio

    def setThreshold(self, threshold):
        self.threshold = threshold

    def signalUpdate(self, sensor_data):

        is_threshold_passed = False
        return_data = sensor_data
        sensor_data_type = type(sensor_data)

        if sensor_data_type not in self.type_list:
            self.is_type_active[sensor_data_type] = [False, 0]
            self.type_list.append(sensor_data_type)
            self.signal_data[type(sensor_data)] = {}
            for key in self.sensor_data_attributes[sensor_data_type]:
                self.signal_data[sensor_data_type][key] = getattr(sensor_data, key)
                setattr(return_data, key, getattr(sensor_data, key))

        else:
            if self.is_type_active[type(sensor_data)][1] < 50:
                self.is_type_active[type(sensor_data)][1] += 1
            elif self.is_type_active[type(sensor_data)][1] == 50:
                self.is_type_active[type(sensor_data)][0] = True

            for key in self.sensor_data_attributes[sensor_data_type]:
                low_pass_applied_key_value = self.alpha_ratio * getattr(sensor_data, key) + (
                            1 - self.alpha_ratio) * self.signal_data[sensor_data_type][key]
                self.signal_data[sensor_data_type][key] = low_pass_applied_key_value
                setattr(return_data, key, low_pass_applied_key_value)
                if key != 'z':
                    if self.is_type_active[sensor_data_type][0] and low_pass_applied_key_value > self.threshold:
                        is_threshold_passed = True

        return return_data, is_threshold_passed


class MPU6050:
    MPU6050_ADDR = 0x68
    PWR_MGMT_1 = 0x6b
    ACCEL_XOUT_H = 0x3b
    GYRO_XOUT_H = 0x43

    def __init__(self, i2c):
        self.i2c = i2c
        self.i2c.start()
        self.i2c.writeto(MPU6050.MPU6050_ADDR, bytearray([MPU6050.PWR_MGMT_1, 0x00]))
        self.i2c.stop()

    def read_raw_data(self, addr):
        self.i2c.start()
        high = self.i2c.readfrom_mem(MPU6050.MPU6050_ADDR, addr, 1)
        low = self.i2c.readfrom_mem(MPU6050.MPU6050_ADDR, addr + 1, 1)
        self.i2c.stop()

        # concatenate higher and lower part
        value = high[0] << 8 | low[0]

        # signed value
        if value > 32768:
            value = value - 65536
        return value

    def read_accel_data(self):
        accel = Acceleration(self.read_raw_data(MPU6050.ACCEL_XOUT_H) / 16384.0,
                             self.read_raw_data(MPU6050.ACCEL_XOUT_H + 2) / 16384.0,
                             self.read_raw_data(MPU6050.ACCEL_XOUT_H + 4) / 16384.0)

        return accel

    def read_gyro_data(self):
        gyro = Gyro(self.read_raw_data(MPU6050.GYRO_XOUT_H) / 250.0,
                    self.read_raw_data(MPU6050.GYRO_XOUT_H + 2) / 250.0,
                    self.read_raw_data(MPU6050.GYRO_XOUT_H + 4) / 250.0)
        return gyro

class Station:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def connect(self, ssid, password):
        if self.wlan.isconnected():
            print("Already connected to a network.")
            return

        self.wlan.connect(ssid, password)

        while not self.wlan.isconnected():
            pass

        print("Connected to", ssid)
        print("IP address:", self.wlan.ifconfig()[0])

    def disconnect(self):
        if not self.wlan.isconnected():
            print("Not connected to any network.")
            return

        self.wlan.disconnect()
        print("Disconnected from the network.")


def get_time():
    r_url = 'http://worldtimeapi.org/api/timezone/Europe/Istanbul'
    response = requests.get(r_url, timeout=10)
    json_data = response.json()
    print(json_data)
    datetime_str = json_data['datetime']
    return datetime_str

def warning_song():
    buzzer.duty(512)  # Buzzer'ı aç
    time.sleep(0.25)
    buzzer.duty(215)  # Buzzer'ı aç
    time.sleep(0.25)
    buzzer.duty(512)  # Buzzer'ı aç
    time.sleep(0.25)
    buzzer.duty(215)  # Buzzer'ı aç


ldrPin1 = 35
ldrPin2 = 33
ldrPin3 = 25
ldrPin4 = 26


ledPin1 = 0
ledPin2 = 16
ledPin3 = 17
ledPin4 = 5

adc1 = ADC(Pin(ldrPin1))
adc2 = ADC(Pin(ldrPin2))
adc3 = ADC(Pin(ldrPin3))
adc4 = ADC(Pin(ldrPin4))

threshold = 200  # Eşik değeri, bu değerin üzerinde ise ışık açık kabul edilir

led1 = Pin(ledPin1, Pin.OUT)
led2 = Pin(ledPin2, Pin.OUT)
led3 = Pin(ledPin3, Pin.OUT)
led4 = Pin(ledPin4, Pin.OUT)

i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)  # adjust this based on your board's pinout
devices = i2c.scan()

print(devices)

mpu = MPU6050(i2c)

sensorOperator = SensorOperator()
sensorOperator.setLowPassRatio(0.05)
sensorOperator.setThreshold(2)


# Buzzer pini ve frekansı
buzzerPin = 23

buzzer = PWM(Pin(buzzerPin))

deprem_count = 0

station = Station()
try:
    station.connect("SSID", "PASS")
except OSError as e:
    print("Error:", e)
    station.disconnect()
    
while True:
    ldrValue1 = adc1.read()  # 1. LDR değerini oku
    ldrValue2 = adc2.read()  # 2. LDR değerini oku
    ldrValue3 = adc3.read()  # 3. LDR değerini oku
    ldrValue4 = adc4.read()  # 4. LDR değerini oku

    print("LDR1:", ldrValue1, "   LDR2:", ldrValue2, "   LDR3:", ldrValue3, "   LDR4:", ldrValue4)

    if ldrValue1 > threshold:
        led1.on()  
        print("Işık 1 açık")
        
    else:
        led1.off()  
        print("Işık 1 kapalı")

    if ldrValue2 > threshold:
        led2.on() 
        print("Işık 2 açık")
    else:
        led2.off() 
        print("Işık 2 kapalı")

    if ldrValue3 > threshold:
        led3.on()  
        print("Işık 3 açık")
    else:
        led3.off()
        print("Işık 3 kapalı")

    if ldrValue4 > threshold:
        led4.on() 
        print("Işık 4 açık")
    else:
        led4.off() 
        print("Işık 4 kapalı")

    gyro_data = mpu.read_gyro_data()
    
    if gyro_data.pitch > 5 or gyro_data.pitch < -5 or gyro_data.roll > 5 or gyro_data.roll < -5:
        print('Deprem oluyor')
        if deprem_count > 5:
            warning_song()
        deprem_count = deprem_count + 1
    else:
        print('Her şey yolunda')
        buzzer.duty(0)  # Buzzer'ı kapat
        deprem_count = 0

    time.sleep(0.5)  # 0.5 saniye bekle
    
    if station.isconnected():
        try:
            datetime_ = get_time()
            
            data = {
                "earthquake_status": True,
                "created_date": datetime_,
                "lines": {
                    "line1": {
                        "header": "Valilik",
                        "current": 4600,
                        "main_line": "public",
                        "status": led1.value(),
                        "warn": True
                    },
                    "line2": {
                        "header": "Valilik",
                        "current": 4600,
                        "main_line": "city",
                        "status": led2.value(),
                        "warn": False
                    },
                    "line3": {
                        "header": "Valilik",
                        "current": 4600,
                        "main_line": "city",
                        "status": led3.value(),
                        "warn": False
                    },
                    "line4": {
                        "header": "Valilik",
                        "current": 4600,
                        "main_line": "city",
                        "status": led4.value(),
                        "warn": False
                    }
                }
            }
            
            json_data = json.dumps(data)
            response = requests.put(firebase_write_url, data=json_data)
            time.sleep(3)

            # Buton pinine kesme (interrupt) atanıyor
            button.irq(trigger=machine.Pin.IRQ_FALLING, handler=check_button)
            
            if response.status_code == 200:
                print('Başarılı')
            else:
                print('Hata: Status kodu', response.status_code)
            response.close()
        except Exception as ex:
            print(ex)