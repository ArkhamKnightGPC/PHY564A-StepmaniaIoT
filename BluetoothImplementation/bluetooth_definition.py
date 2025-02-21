import bluetooth
import asyncio
from bleak import BleakClient, BleakError, BleakGATTCharacteristic

class BluetoothDeviceFinder:
    """Class to find the bluetooth device"""

    def __init__(self):
        pass

    def search_for(self, device_name: str) -> str:
        """Search for the bluetooth device with the given name.
        
        Args:
            device_name (str): The name of the device to search for.
        Return:
            str: The address of the device.
        """
        nearby_devices = bluetooth.discover_devices(
            duration=8, lookup_names=True, flush_cache=True, lookup_class=False)
        
        for addr, name in nearby_devices:
            print(f"Found: {addr} - {name}")

        for addr, name in nearby_devices:
            if name == device_name:
                return addr
        return None

class BluetoothClient:
    def __init__(self, device_mac_address: str):
        self.device_mac_address = device_mac_address
        self.client = None
        self.CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
        self.CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

    async def connect(self):
        self.client = BleakClient(self.device_mac_address)
        # Set the callback function to receive data
        self.client
        await self.client.connect()
        print(f"Connected to {self.device_mac_address}")
        await self.client.start_notify(self.CHARACTERISTIC_UUID_TX, self._recv_message_callback())
        try:
            while self.client.is_connected:
                await asyncio.sleep(1)  # Check every second
            print("Device disconnected. Attempting to reconnect...")
        except BleakError as e:
            print(f"Error while monitoring connection: {e}")
        finally:
            await self.connect()  # Start reconnection attempts

    async def send_message(self, message: str):
        """Send a message to the device."""
        await self.client.write_gatt_char(self.CHARACTERISTIC_UUID_RX, message)

    async def _recv_message_callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        print(f"Received message from {sender}: {data}")

    async def _run(self):
        await self.connect()
        

    def run(self):
        asyncio.run(self._run())

if __name__ == "__main__":
    device_name = "LG-EOLE"
    device_finder = BluetoothDeviceFinder()
    print(f"Finding device: {device_name}...")
    device_mac_address = device_finder.search_for(device_name)
    if device_mac_address is None:
        print(f"Device {device_name} not found.")
        exit(1)
    print(f"Device {device_name} MAC Address: {device_mac_address}")

    bt_client = BluetoothClient(device_mac_address)
    bt_client.run()