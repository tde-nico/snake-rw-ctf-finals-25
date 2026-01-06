# main.py - Pico W BLE client for SnakeCTF "signal" device
#
# Requires:
#   - Raspberry Pi Pico W (or Pico 2 W)
#   - MicroPython firmware with BLE support
#   - The 'aioble' library installed on the board

import uasyncio as asyncio
import aioble
import bluetooth

NET_NAME = "SnakeCTF - signal"

SERVICE_UUID   = bluetooth.UUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
HINT_CHAR_UUID = bluetooth.UUID("6e400002-b5a3-f393-e0a9-e50e24dcca9e")
REG_CHAR_UUID  = bluetooth.UUID("6e400003-b5a3-f393-e0a9-e50e24dcca9e")
FLAG_CHAR_UUID = bluetooth.UUID("6e400004-b5a3-f393-e0a9-e50e24dcca9e")


async def find_signal_device():
    print("Scanning for '{}'...".format(NET_NAME))
    async with aioble.scan(
        10000, interval_us=30000, window_us=30000, active=True
    ) as scanner:
        async for result in scanner:
            name = result.name() or ""
            if name == NET_NAME:
                print(">> Found target device:", name)
                return result.device
    print("!! Device not found in this scan window")
    return None


def compute_code_from_millis(millis: int) -> str:
    base = (0x5A5A5A5A + 1337)
    seconds_low16 = (millis // 1000) & 0xFFFF
    code = base ^ seconds_low16
    return "{:08X}".format(code)


async def attack_once(connection):
    print(">>> Discovering service and characteristics...")

    service = await connection.service(SERVICE_UUID)

    hint_char = await service.characteristic(HINT_CHAR_UUID)
    reg_char  = await service.characteristic(REG_CHAR_UUID)
    flag_char = await service.characteristic(FLAG_CHAR_UUID)

    hint_bytes = await hint_char.read()
    try:
        hint_str = hint_bytes.decode().strip()
        millis = int(hint_str)
    except Exception as e:
        print("!! Failed to parse hint:", hint_bytes, "error:", e)
        return False

    print("Hint millis:", millis)

    code_str = compute_code_from_millis(millis)
    print("Computed code:", code_str)

    await reg_char.write(code_str.encode("ascii"))
    print("Code written to regChar, waiting for ESP32 to check it...")

    await asyncio.sleep(9)

    await connection.exchange_mtu(517) 

    flag_bytes = await flag_char.read()
    flag = flag_bytes
    print("Raw bytes:", flag_bytes, "len:", len(flag_bytes))

    if flag != "Locked":
        print(">>> Got the flag! <<<")
        return True

    print("Still locked, will try again...")
    return False


async def main():
    device = await find_signal_device()
    if not device:
        print("Aborting: could not find '{}'".format(NET_NAME))
        return

    print("Connecting to device:", device)
    connection = await device.connect()
    print("Connected!")

    async with connection:
        for attempt in range(1, 6):
            print("\n===== Attempt {} =====".format(attempt))
            ok = await attack_once(connection)
            if ok:
                break
            await asyncio.sleep(2)

    print("Done. You can reset the Pico W to try again.")


asyncio.run(main())

# snakeCTF{r3g1st3r3d_4t_th3_r1ght_t1m3}
