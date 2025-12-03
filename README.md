# XIAO BLE CONTROL LED RGB:
### NeoPixel LED Control for Seeed XIAO nRF52840 via BLE + Firebase Realtime Sync

## Introduction
This project allows you to control a **WS2812B (NeoPixel) LED strip** connected to a **Seeed Studio XIAO nRF52840 (or XIAO BLE Sense)** using **Bluetooth Low Energy (BLE)** from either a **Windows/macOS/Linux desktop** or an **Android phone**.

The system consists of two independent control apps that stay perfectly in sync thanks to **Firebase Realtime Database**:

1. **Firmware** – Runs on the XIAO nRF52840 (Seeed XIAO BLE + Bluefruit nRF52)
2. **Control Apps**:
   - **Desktop**: Python + Tkinter + Bleak + Pyrebase (the full-screen app in the first image)
   - **Mobile**: Built with MIT App Inventor (the simple phone UI in the second image)

Change the mode or brightness from any device → all other devices (and the LED strip) update instantly.

- **Goal**: Learn BLE GATT services, NeoPixel animations, real-time cloud sync, and cross-platform control.
- **Languages**: C++ (Seeed XIAO BLE), Python 3, MIT App Inventor (Blocks)
- **Tools**: Seeed XIAO BLE IDE 2, Python, MIT App Inventor, Firebase Console.

---
## Features

| Feature                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **3 LED Effects + OFF**     | MODE1 (all blink), MODE2 (running light), MODE3 (fill gradually)           |
| **Brightness Control**     | 0–255 via slider (1-byte BLE write)                                         |
| **Stable BLE Connection**   | Custom GATT service (Nordic UART-style UUIDs)                               |
| **Device Info Broadcast**   | Battery, name, firmware version, model ID sent on connect (Notify)         |
| **Two-way Firebase Sync**   | PC ↔ Phone ↔ XIAO — all changes reflected in real time                      |
| **Beautiful Desktop UI**    | Dark theme, detailed log, auto-reconnect                                    |
| **Simple Mobile App**       | MIT App Inventor – clean buttons + slider                                  |

---
## Hardware Requirements

| Component                   | Quantity | Notes                                      |
|-----------------------------|----------|--------------------------------------------|
| Seeed XIAO nRF52840         | 1        | Or XIAO BLE Sense                          |
| WS2812B LED strip / ring    | 10 LEDs  | Data pin → D2 (change `LED_PIN` if needed) |
| Power supply                | –        | USB or 3.7V LiPo                           |

**Wiring**  
- NeoPixel DIN → Pin 2 on XIAO  
- 5V → 5V (or 3.3V if strip supports it)  
- GND → GND  

---
## Firmware (N)

### Required Libraries
- Adafruit Bluefruit nRF52 Libraries
- Adafruit NeoPixel

### Fixed UUIDs
- Service: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- Mode Write: `6E400005-B5A3-F393-E0A9-E50E24DCCA9E`
- Brightness Write: `6E400006-B5A3-F393-E0A9-E50E24DCCA9E`
- Device Info Notify: `6E400010-B5A3-F393-E0A9-E50E24DCCA9E`

Upload the provided Seeed XIAO BLE sketch → the board advertises as **XIAO_BLE**.

---
## Desktop Application (Python + Tkinter)

### Python Dependencies
```
pip install bleak pyrebase4

(Tkinter is included with standard Python)

Firebase Realtime Database Structure
xiaoledcontrol-default-rtdb
├── device_info
│   ├── Battery Level
│   ├── Device Name
│   ├── Device Picture
│   ├── Firmware Version
│   └── Model ID
└── device_setting
    ├── effect_mode      ← "OFF" | "MODE1" | "MODE2" | "MODE3"
    └── brightness       ← 0-255 (integer)
```
### Mobile Application (MIT App Inventor)
- A separate .aia project (interface shown in the second screenshot) uses:
- BluetoothLE extension
- FirebaseDB component
- Identical mode buttons + brightness slider
- Both apps are fully interchangeable.

### How It Works

1. XIAO starts → creates custom BLE service → advertises as XIAO_BLE
2. Any app connects → receives device info via Notify → pushes it to Firebase (device_info)
3. User changes mode/brightness:
  - Value is written directly to BLE characteristics
  - Same value is updated in Firebase /device_setting
4. All other connected apps listen to Firebase stream → receive change → write to BLE (if connected)
5. XIAO instantly updates NeoPixel effect and brightness
Result: seamless multi-platform real-time control without a dedicated server.

### Build & Run
**Firmware**:

Open Arduino IDE → install "Seeed XIAO nRF52840" board
Paste the provided Arduino code
Upload to the XIAO

**Desktop App**:
Bashpython xiao_led_control.py

**Mobile App**:
Go to https://ai2.appinventor.mit.edu
Import the provided .aia file
Build APK or test with AI Companion