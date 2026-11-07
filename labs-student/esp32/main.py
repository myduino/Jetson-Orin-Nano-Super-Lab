"""Myduino AIoT device: an ESP32-S3 with MicroPython.

The Jetson does the AI (it sees, hears and thinks). This board does the IoT: it switches an LED, a buzzer and a servo
and it reads a sensor. The two talk with MQTT through the broker on the Jetson.

Topics:  esp/cmd/led      on | off | blink          esp/status     online | offline (retained, the last will)
         esp/cmd/buzzer   milliseconds              esp/telemetry  JSON every 5 seconds
         esp/cmd/servo    angle 0 to 180            esp/sensor/light  the light level every 2 seconds
         esp/cmd/alert    on | off                  esp/ack        "<command>=<value>" after every command
         jetson/hb        the heartbeat of the Jetson (every 5 seconds)    esp/event  messages of the board
Fail-safe: if the alert is on and the heartbeat of the Jetson stops for 15 seconds, the board switches the alert off.
"""
import json
import time

import network
from machine import ADC, PWM, Pin
from umqtt.simple import MQTTClient

import config

led = Pin(config.PIN_LED, Pin.OUT)
buzzer = Pin(config.PIN_BUZZER, Pin.OUT)
servo = PWM(Pin(config.PIN_SERVO), freq=50)
light = ADC(Pin(config.PIN_LIGHT))
light.atten(ADC.ATTN_11DB)                      # read the full range 0 to 3.3 V

state = {"led": "off", "alert": False, "buzzer_until": 0, "servo": 90, "hb": time.ticks_ms()}
client = None


def set_servo(angle):
    angle = max(0, min(180, angle))
    state["servo"] = angle
    servo.duty_u16(int((0.5 + angle / 180 * 2.0) / 20 * 65535))      # a pulse of 0.5 to 2.5 ms every 20 ms


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(40):
            if wlan.isconnected():
                break
            time.sleep(0.5)
    if not wlan.isconnected():
        raise OSError("no Wi-Fi")
    return wlan


def say(topic, text, retain=False):
    client.publish(topic, str(text), retain)


def on_message(topic, payload):
    topic, text = topic.decode(), payload.decode().strip()
    name = topic.split("/")[-1]
    if topic.startswith("esp/cmd/"):
        try:
            if name == "led":
                state["led"] = text
            elif name == "buzzer":
                state["buzzer_until"] = time.ticks_add(time.ticks_ms(), int(text))
            elif name == "servo":
                set_servo(int(text))
            elif name == "alert":
                state["alert"] = text == "on"
                state["hb"] = time.ticks_ms()
            else:
                return
            say("esp/ack", name + "=" + text)
        except ValueError:
            say("esp/event", "bad value for " + name + ": " + text)
    elif topic == "jetson/hb":
        state["hb"] = time.ticks_ms()


def update_outputs(now):
    if state["alert"] and time.ticks_diff(now, state["hb"]) > 15000:
        state["alert"] = False                                        # fail-safe: the Jetson is gone
        say("esp/event", "failsafe: no heartbeat from the Jetson, alert off")
    if state["alert"]:
        led.value((now // 150) % 2)                                   # fast blink
    elif state["led"] == "blink":
        led.value((now // 500) % 2)
    else:
        led.value(1 if state["led"] == "on" else 0)
    beeping = time.ticks_diff(state["buzzer_until"], now) > 0
    buzzer.value(1 if beeping or (state["alert"] and (now // 300) % 2 == 0) else 0)


def connect_mqtt():
    global client
    client = MQTTClient("esp32-" + config.MQTT_USER, config.MQTT_HOST, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD, keepalive=30)
    client.set_last_will(b"esp/status", b"offline", retain=True)      # the broker says offline if the board disappears
    client.set_callback(on_message)
    client.connect()
    client.subscribe(b"esp/cmd/#")
    client.subscribe(b"jetson/hb")
    say("esp/status", "online", retain=True)


def run():
    wlan = connect_wifi()
    connect_mqtt()
    started = last_sensor = last_telemetry = time.ticks_ms()
    set_servo(state["servo"])
    while True:
        client.check_msg()
        now = time.ticks_ms()
        update_outputs(now)
        if time.ticks_diff(now, last_sensor) > 2000:
            last_sensor = now
            say("esp/sensor/light", light.read())
        if time.ticks_diff(now, last_telemetry) > 5000:
            last_telemetry = now
            say("esp/telemetry", json.dumps({"uptime_s": time.ticks_diff(now, started) // 1000, "rssi": wlan.status("rssi"),
                                             "led": state["led"], "alert": state["alert"], "servo": state["servo"]}))
        time.sleep_ms(20)


while True:
    try:
        run()
    except OSError as error:                                          # Wi-Fi or broker lost: try again
        print("Connection lost:", error)
        time.sleep(3)
