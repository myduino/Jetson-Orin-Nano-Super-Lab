# Settings of your ESP32-S3 board. Fill in your own values. The notebook of Lab 22 writes the MQTT lines for you.

WIFI_SSID = "your-wifi-name"          # the Wi-Fi of the lab (2.4 GHz only, the ESP32 cannot use 5 GHz)
WIFI_PASSWORD = "your-wifi-password"

MQTT_HOST = "192.168.8.45"            # the IP address of your Jetson
MQTT_PORT = 1881                      # the MQTT port of your student card (Jupyter port minus 7000)
MQTT_USER = "aminah"                  # your student name
MQTT_PASSWORD = "123456"              # your PIN

# Pins. These are placeholders: change them to the pins you wired. Avoid the pins your board uses for the USB,
# the flash and the boot button (see the pinout of your board).
PIN_LED = 4                           # an LED with a 220 ohm resistor
PIN_BUZZER = 5                        # an active buzzer
PIN_SERVO = 6                         # the signal wire of a small servo (a door or a gate)
PIN_LIGHT = 1                         # an analog pin (ADC1) with a light sensor (LDR) and a 10 k resistor
