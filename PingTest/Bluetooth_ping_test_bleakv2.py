import asyncio
import time
from bleak import BleakScanner, BleakClient

def detection_callback(device, data):
    print(device, data)

async def main():
    global connected
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    while True:
        await asyncio.sleep(1)

asyncio.run(main())