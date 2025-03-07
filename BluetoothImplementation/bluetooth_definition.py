import bluetooth
import asyncio
from bleak import BleakClient, BleakError, BleakGATTCharacteristic
import time
import threading
from uuid import uuid4
import array
import struct
from typing import Callable, Optional

background_tasks = set()
class BluetoothDeviceFinder:
    """Class to find the bluetooth device"""

    def __init__(self):
        pass

    def browse_devices(self):
        return bluetooth.discover_devices(
            duration=8, lookup_names=True, flush_cache=True, lookup_class=False)

    def search_for(self, device_name: str) -> str:
        """Search for the bluetooth device with the given name.
        
        Args:
            device_name (str): The name of the device to search for.
        Return:
            str: The address of the device.
        """
        nearby_devices = self.browse_devices()
        
        for addr, name in nearby_devices:
            print(f"Found: {addr} - {name}")

        for addr, name in nearby_devices:
            if name == device_name:
                return addr
        return None

class BluetoothClient:
    def __init__(self, device_mac_address: str, DEBUG: bool = True):
        self.device_mac_address = device_mac_address
        self.client = None
        self.CHARACTERISTIC_UUID_RX = "19B10001-E8F2-537E-4F6C-D104768A1214" # TX of ESP32
        self.CHARACTERISTIC_UUID_TX = "19B10002-E8F2-537E-4F6C-D104768A1214" # RX of ESP32
        self.DEBUG = DEBUG
        self.recv_message_callback: Optional[Callable[[bytearray], None]] = None # Callback function to receive data

        # Background task handling
        self.loop = None # Separate event loop for Bluetooth
        self.thread = None

    async def connect(self):
        self.client = BleakClient(self.device_mac_address)
        # Set the callback function to receive data*
        while True:
            try:
                if self.DEBUG:
                    print(f"Connecting to {self.device_mac_address}...")
                await self.client.connect()
                break
            except Exception as e:
                print(f"failed to connect ! {e}")            
    
        if self.DEBUG:
            print(f"Connected to {self.device_mac_address}")
        await self.client.start_notify(self.CHARACTERISTIC_UUID_RX, self._recv_message_callback)
        try:
            while self.client.is_connected:
                await asyncio.sleep(1)  # Check every second
            print("Device disconnected. Attempting to reconnect...")
        except BleakError as e:
            print(f"Error while monitoring connection: {e}")
        finally:
            await self.connect()  # Start reconnection attempts

    # async def send_message_str(self, message: str):
    #     """Send a message (str) to the device."""
    #     THIS_UUID = self.CHARACTERISTIC_UUID_TX
    #     await self.client.write_gatt_char(THIS_UUID, message)
    #     print(f"Sent {message}")

    async def async_send_message_bytes(self, message: bytearray):
        """Send a message (bytearray) to the device. Ex: b'\x00\x01\x02\x03' """
        # THIS_UUID = uuid4()
        THIS_UUID = self.CHARACTERISTIC_UUID_TX
        await self.client.write_gatt_char(THIS_UUID, message, response=True)
        print(f"Sent {message}")
            
    def send_message_bytes(self, message: bytearray):
        """Non-blocking wrapper to call send_message_bytes() from a non-async function."""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.async_send_message_bytes(message), self.loop)

    async def _recv_message_callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        print(f"Received message from {sender}: {data}")
        if self.recv_message_callback:
            self.recv_message_callback(data)
        # encoded = bytearray()
        # encoded.extend(struct.pack("i", 99))  # First byte as integer 99
        # for value in [1.0,1.2, -9, float("inf")]:
        #     encoded.extend(struct.pack('f', value))  # Convert float to bytes
        # await self.async_send_message_bytes(encoded)

    async def _run(self):
        # Run the connection process asynchronously
        await self.connect()

    def _start_loop(self):
        """Runs an asyncio event loop in a separate thread."""
        # Create and set the new event loop for the thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # Run the _run coroutine inside the event loop
        self.loop.run_until_complete(self._run())

    def connect_in_background(self):
        """Starts the Bluetooth client in a background thread."""
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()

def setup_bluetooth(*ESP32_BT_NAMES: str, use_mac_addresses: bool = False, DEBUG: bool = True) -> list[BluetoothClient]:
    """Setup the bluetooth clients and returns them.
    
    If use_mac_addresses = True: """
    if DEBUG:
        print(f"Setting up bluetooth connections for {ESP32_BT_NAMES}")
    mac_addresses: list[str] = []
    clients: list[BluetoothClient] = []

    if use_mac_addresses:
        mac_addresses = ESP32_BT_NAMES
    else:
        # Browse nearby Bluetooth clients
        device_finder = BluetoothDeviceFinder()
        nearby_devices = device_finder.browse_devices()
        for addr, name in nearby_devices:
            print(f"Found: {addr} - {name}")

        # Find Bluetooth devices by given names
        for esp32_bt_name in ESP32_BT_NAMES:
            for addr, name in nearby_devices:
                if name == esp32_bt_name:
                    mac_addresses.append(addr)

    # Setup Bluetooth connections
    for mac_address in mac_addresses:
        client = BluetoothClient(mac_address)
        clients.append(client)
        client.connect_in_background()  # This will run _start_loop in a background thread

    # Wait for Bluetooth connections to be established
    waiting = True
    while waiting:
        waiting = False
        for client in clients:
            if client.client and not client.client.is_connected:
                waiting = True
        time.sleep(1)
    
    return clients
