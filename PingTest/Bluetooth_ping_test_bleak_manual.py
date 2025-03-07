import asyncio
from bleak import BleakClient

ESP32_MAC = "10:97:BD:E6:F2:D2"  # Adresse MAC de l'ESP32
CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

async def main():
    async with BleakClient(ESP32_MAC) as client:
        print(f"Connecté à {ESP32_MAC}")

        # Envoyer un message à l'ESP32
        await client.write_gatt_char(CHARACTERISTIC_UUID_RX, b"Hello ESP32!")

        # Lire la réponse
        while True:
            response = await client.read_gatt_char(CHARACTERISTIC_UUID_TX)
            print(f"Réponse de l'ESP32: {response}")

            # Si réponse, répondre:
            if response:
                await client.write_gatt_char(CHARACTERISTIC_UUID_RX, b"Hello ESP32!")

asyncio.run(main())