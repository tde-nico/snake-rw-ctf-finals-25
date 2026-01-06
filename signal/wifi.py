import network
import time

ssid = "SnakeCTF"
password = "snakeCTF{pwd}"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

print("Connecting...")
for _ in range(20):
    if wlan.isconnected():
        break
    print(".", end="")
    time.sleep(0.5)

print("\nStatus:", wlan.isconnected())
print("IP:", wlan.ifconfig())
