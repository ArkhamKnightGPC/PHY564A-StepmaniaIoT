# PHY564A Group project

Stepmania based game project for PHY564A Open Electronics course at Ecole polytechnique.

## Overview

The project has two components: a pygame application running on a Raspberry Pi 3 Model B+, and a wireless controller based on a ESP32 microcontroller with LED buttons and a 3D case made with [Autodesk Fusion](https://www.autodesk.com/products/fusion-360/overview). Communication between the Raspberry Pi and the controller is done via Bluetooth Low Energy using [GATT notifications](https://www.bluetooth.com/bluetooth-resources/intro-to-bluetooth-gap-gatt/). The rapport also details attempts made to integrate a second player using the [ESP-NOW protocol](https://www.espressif.com/en/solutions/low-power-solutions/esp-now).

To see it in action, please check our [Youtube demo for the project!](https://youtu.be/aHGMkcp-9PM)

## ESP32 pinout for the controllers

| Sig1 Pins(LED inputs)    | Sig2 Pins(Button outputs) |
| ------------------------ | ------------------------- |
| 26 (D3)  | 25 (D2)   |
| 13 (D7)  | 14 (D6)   |
| 34 (A2)  | 15 (A4)   |
| 35 (A3)  | 21 (SDA)  |
