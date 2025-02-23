import machine
import network
import urequests
import time
import dht
import bmp280
from machine import Pin, I2C
import gc  # Garbage collector
from lcd_i2c import I2cLcd  # I2C LCD library

# ================================
#       Configuration
# ================================
DHT_PIN = 23               # GPIO pin for DHT11
BMP280_I2C_ADDR = 0x76
RAIN_SENSOR_PIN = 34       # GPIO pin for Rain Sensor
LDR_PIN = 35               # GPIO pin for LDR
MQ135_PIN = 14             # MQ-135 Digital Pin (adjust as needed)
WIFI_SSID = 'lokimux'
WIFI_PASSWORD = '11072004'
TELEGRAM_TOKEN = '7447852497:AAFaefX8uXIA9drenumOLAblUlpR7xDStAg'  # Replace with your token
CHAT_ID = '1706011784'     # Replace with your chat ID

# ================================
#      I2C Initialization
# ================================
# I2C for BMP280 (SDA=21, SCL=22)
i2c_bmp = I2C(1, scl=Pin(22), sda=Pin(21))
bmp_sensor = bmp280.BMP280(i2c_bmp)

# I2C for LCD (SDA=18, SCL=19)
i2c_lcd = I2C(0, scl=Pin(26), sda=Pin(27))
lcd_addr = 0x3F  # LCD I2C address (try 0x27 if 0x3F doesn't work)
lcd = I2cLcd(i2c_lcd, lcd_addr, 2, 16)  # 16x2 LCD

# ================================
#       Sensor Initialization
# ================================
dht_sensor = dht.DHT11(Pin(DHT_PIN))
rain_sensor = Pin(RAIN_SENSOR_PIN, Pin.IN)
ldr = Pin(LDR_PIN, Pin.IN)
mq135 = Pin(MQ135_PIN, Pin.IN)  # MQ-135 in digital mode

# ================================
#       Helper Functions
# ================================
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        time.sleep(1)
    print("Connected to WiFi")

def read_sensors():
    # Read DHT11
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    
    # Read BMP280
    pressure = bmp_sensor.pressure
    altitude = bmp_sensor.altitude()
    
    # Read rain sensor and LDR
    rain = "Yes" if rain_sensor.value() == 0 else "No"
    light_value = "🌙 Dark" if ldr.value() == 1 else "☀️ Light"
    
    # Determine air quality based on MQ-135 reading:
    air_quality = "Bad" if mq135.value() == 0 else "Good"
    
    # (Optional) Debug: print the raw MQ-135 value
    print("MQ-135 raw value:", mq135.value())
    
    return temperature, humidity, pressure, altitude, light_value, rain, air_quality

def update_lcd(temp, hum, pres, alt, light, rain, air_quality):
    # Display 1: Project Name
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("IoT Weather")
    lcd.set_cursor(0, 1)
    lcd.putstr("Monitoring Sys")
    time.sleep(2)
    
    # Display 2: Temperature
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("Temperature:")
    lcd.set_cursor(0, 1)
    lcd.putstr("{:.1f} C".format(temp))
    time.sleep(2)
    
    # Display 3: Humidity
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("Humidity:")
    lcd.set_cursor(0, 1)
    lcd.putstr("{:.1f} %".format(hum))
    time.sleep(2)
    
    # Display 4: Pressure
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("Pressure:")
    lcd.set_cursor(0, 1)
    lcd.putstr("{:.0f} hPa".format(pres))
    time.sleep(2)
    
    # Display 5: Altitude
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("Altitude:")
    lcd.set_cursor(0, 1)
    lcd.putstr("{:.1f} m".format(alt))
    time.sleep(2)
    
    # Display 6: Rain
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("Rain:")
    lcd.set_cursor(0, 1)
    lcd.putstr(rain)
    time.sleep(2)
    
    # Display 7: Light Status
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("Light Status:")
    lcd.set_cursor(0, 1)
    lcd.putstr(light)
    time.sleep(2)
    
    # Display 8: Air Quality
    lcd.clear()
    lcd.set_cursor(0, 0)
    lcd.putstr("Air Quality:")
    lcd.set_cursor(0, 1)
    lcd.putstr(air_quality)
    time.sleep(2)
    
    lcd.clear()

def check_memory():
    gc.collect()
    print('Free memory:', gc.mem_free(), 'bytes')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    try:
        check_memory()
        response = urequests.post(url, json=data)
        print("Response code:", response.status_code)
        print("Response text:", response.text)
    except Exception as e:
        print("An error occurred:", e)

# ================================
#              Main
# ================================
def main():
    connect_to_wifi()
    lcd.clear()
    lcd.putstr("Initializing...")
    time.sleep(2)
    
    last_telegram_time = time.time()
    
    while True:
        # Read all sensor values
        temperature, humidity, pressure, altitude, light_value, rain, air_quality = read_sensors()
        
        # Update the LCD with a sequential display of each sensor reading.
        # This cycle takes about 16 seconds (8 screens x 2 sec each) and repeats continuously.
        update_lcd(temperature, humidity, pressure, altitude, light_value, rain, air_quality)
        
        # Check if it's time to send a Telegram message (every 60 seconds)
        current_time = time.time()
        if current_time - last_telegram_time >= 60:
            message = (
                f"🌤Weather Station\n"
                f"------------------------------\n"
                f"🌡Temperature: {temperature} °C\n"
                f"💧Humidity: {humidity} %\n"
                f"📏Pressure: {pressure:.2f} hPa\n"
                f"🏔Altitude: {altitude:.2f} m\n"
                f"💡Light Status: {light_value}\n"
                f"🌧Rain Detected: {'☔️ Yes' if rain=='Yes' else '🌞 No'}\n"
                f"🌱Air Quality: {'😊 Good' if air_quality=='Good' else '🚫 Bad'}\n"
                f"------------------------------\n"
                f"Have a great day! 😊"
            )
            send_telegram_message(message)
            last_telegram_time = current_time

if __name__ == "__main__":
    main()
