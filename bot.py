import machine
import network
import urequests
import time
import dht
import bmp280
from machine import Pin, I2C
import gc  # Import the garbage collector

# =============================================================================
# Configuration
# =============================================================================
DHT_PIN = 23              # GPIO pin for DHT11
BMP280_I2C_ADDR = 0x76    # I2C address for BMP280
RAIN_SENSOR_PIN = 34      # GPIO pin for Rain Sensor
LDR_PIN = 35              # GPIO pin for LDR
MQ135_PIN = 32            # GPIO pin for MQ-135

WIFI_SSID = 'lokimux'
WIFI_PASSWORD = '11072004'
TELEGRAM_TOKEN = '7447852497:AAFaefX8uXIA9drenumOLAblUlpR7xDStAg'  # Replace with your actual token
CHAT_ID = '1706011784'  # Replace with your actual chat ID

# =============================================================================
# Hardware Initialization
# =============================================================================
# Initialize I2C for BMP280
i2c = I2C(1, scl=Pin(22), sda=Pin(21))  # Adjust pins accordingly

# Initialize sensors
dht_sensor = dht.DHT11(Pin(DHT_PIN))
bmp_sensor = bmp280.BMP280(i2c)
rain_sensor = Pin(RAIN_SENSOR_PIN, Pin.IN)
ldr = Pin(LDR_PIN, Pin.IN)
mq135 = machine.ADC(Pin(MQ135_PIN))  # Initialize MQ-135 as ADC
# Optionally, set ADC attenuation if needed:
# mq135.atten(machine.ADC.ATTN_11DB)

# =============================================================================
# Functions
# =============================================================================
def connect_to_wifi():
    """
    Connect to WiFi using the provided SSID and password.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    while not wlan.isconnected():
        print("Connecting to WiFi...")
        time.sleep(1)

    print("Connected to WiFi")


def read_sensors():
    """
    Read sensor values from DHT11, BMP280, rain sensor, LDR, and MQ-135.
    
    Returns:
        tuple: Contains temperature, humidity, pressure, altitude,
               light status, rain detection, and air quality status.
    """
    # Read temperature and humidity from DHT11
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()

    # Read pressure and altitude from BMP280
    pressure = bmp_sensor.pressure
    altitude = bmp_sensor.altitude()  # Call the altitude method correctly

    # Read rain sensor (assuming 0 indicates rain detected)
    rain = "Yes" if rain_sensor.value() == 0 else "No"

    # Read light sensor (using LDR) to determine light status
    light_value = "🌙 Dark" if ldr.value() == 1 else "☀️ Light"

    # Read air quality from MQ-135 sensor (ADC value)
    air_quality_value = mq135.read()
    air_quality = "Good" if air_quality_value < 300000 else "Bad"

    return temperature, humidity, pressure, altitude, light_value, rain, air_quality


def check_memory():
    """
    Clean up memory using garbage collection and print free memory.
    """
    gc.collect()
    print('Free memory:', gc.mem_free(), 'bytes')


def send_telegram_message(message):
    """
    Send a message to Telegram using the Bot API.
    
    Args:
        message (str): The message text to be sent.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',  # Use HTML formatting
        'disable_web_page_preview': True
    }

    try:
        check_memory()
        response = urequests.post(url, json=data)
        print("Response code:", response.status_code)
        print("Response text:", response.text)
        if response.status_code == 200:
            print("Message sent successfully")
        else:
            print("Failed to send message")
    except Exception as e:
        print("An error occurred:", e)


def main():
    """
    Main loop: Connect to WiFi, read sensor data, send a Telegram message,
    and then wait for 60 seconds before repeating.
    """
    connect_to_wifi()

    while True:
        # Read sensor values
        temperature, humidity, pressure, altitude, light_value, rain, air_quality = read_sensors()

        # Format the message with emojis for a friendly appearance
        message = (
            "🌤 Weather Station\n"
            "------------------------------\n"
            f"🌡 Temperature: {temperature} °C\n"
            f"💧 Humidity: {humidity} %\n"
            f"📏 Pressure: {pressure:.2f} hPa\n"
            f"🏔 Altitude: {altitude:.2f} m\n"
            f"💡 Light Status: {light_value}\n"
            f"🌧 Rain Detected: {'☔️ Yes' if rain == 'Yes' else '🌞 No'}\n"
            f"🌱 Air Quality: {'😊 Good' if air_quality == 'Good' else '🚫 Bad'}\n"
            "------------------------------\n"
            "Have a great day! 😊"
        )

        send_telegram_message(message)
        time.sleep(60)  # Wait for 60 seconds before sending the next update


# =============================================================================
# Main Execution
# =============================================================================
if __name__ == "__main__":
    main()
