import asyncio
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from bleak import BleakScanner, BleakClient
import threading
import pyrebase
import time
import json

# ==================== FIREBASE CONFIG ====================
firebaseConfig = {
  "apiKey": "AIzaSyD6AqEhpn-DUZGevr23n0IuVIMF4DOrWxs",
  "authDomain": "xiaoledcontrol.firebaseapp.com",
  "databaseURL": "https://xiaoledcontrol-default-rtdb.firebaseio.com",
  "projectId": "xiaoledcontrol",
  "storageBucket": "xiaoledcontrol.firebasestorage.app",
  "messagingSenderId": "670562686186",
  "appId": "1:670562686186:web:ef0e580bb7d95021f1b393"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# ==================== BLE UUID ====================
TARGET_NAME_CONTAINS = "XIAO"
SERVICE_UUID        = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
MODE_UUID           = "6E400005-B5A3-F393-E0A9-E50E24DCCA9E"
BRIGHT_UUID         = "6E400006-B5A3-F393-E0A9-E50E24DCCA9E"
DEVICE_INFO_UUID = "6E400010-B5A3-F393-E0A9-E50E24DCCA9E"   # Characteristic chứa Device Info

client = None
connected = False

# ==================== TKINTER UI ====================
root = tk.Tk()
root.title("XIAO BLE LED Controller")
root.geometry("800x720")
root.configure(bg="#1e1e2f")  # Darker background for modern look
root.resizable(False, False)  # Prevent resizing for consistent layout

# Use ttk style for modern widgets
style = ttk.Style()
style.theme_use('clam')  # Modern theme
style.configure('TButton', font=('Arial', 12, 'bold'), padding=10, relief='flat')
style.configure('TLabel', font=('Arial', 14), background='#1e1e2f', foreground='white')
style.configure('TScale', background='#1e1e2f', troughcolor='#3a3a5a')
style.configure('Horizontal.TScale', gripcount=0)  # Cleaner slider

# Title
title_label = ttk.Label(root, text="XIAO BLE LED Control", font=("Arial", 24, "bold"), foreground="#ffffff")
title_label.pack(pady=20)

# Connection Frame
conn_frame = tk.Frame(root, bg="#1e1e2f", bd=2, relief="groove")
conn_frame.pack(pady=10, padx=20, fill='x')

# Use grid to center buttons evenly
conn_frame.columnconfigure(0, weight=1)
conn_frame.columnconfigure(1, weight=1)
conn_frame.columnconfigure(2, weight=1)

btn_connect = ttk.Button(conn_frame, text="Kết nối BLE", style='TButton', command=lambda: thread_connect())
btn_connect.config(width=20)
btn_connect.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

btn_disconnect = ttk.Button(conn_frame, text="Ngắt kết nối", style='TButton', command=lambda: thread_disconnect(), state="disabled")
btn_disconnect.config(width=20)
btn_disconnect.grid(row=0, column=1, padx=10, pady=10, sticky='ew')

btn_clear_log = ttk.Button(conn_frame, text="Clear Log", style='TButton', command=lambda: clear_log())
btn_clear_log.config(width=20)
btn_clear_log.grid(row=0, column=2, padx=10, pady=10, sticky='ew')

# Modes Frame
modes_frame = tk.Frame(root, bg="#1e1e2f", bd=2, relief="groove")
modes_frame.pack(pady=10, padx=20, fill='x')

ttk.Label(modes_frame, text="Chọn Mode:", style='TLabel').pack(side=tk.LEFT, padx=10)

def on_mode_click(mode):
    asyncio.run_coroutine_threadsafe(send_mode(mode), loop)
    db.child("device_setting").update({"effect_mode": mode})
    log(f"Gửi {mode}")

for m in ["MODE1", "MODE2", "MODE3", "OFF"]:
    mode_btn = ttk.Button(modes_frame, text=m, style='TButton', command=lambda m=m: on_mode_click(m))
    mode_btn.config(width=10)
    mode_btn.pack(side=tk.LEFT, padx=5, pady=10)

# Brightness Frame
bright_frame = tk.Frame(root, bg="#1e1e2f", bd=2, relief="groove")
bright_frame.pack(pady=10, padx=20, fill='x')

ttk.Label(bright_frame, text="Brightness (0–255):", style='TLabel').pack(side=tk.LEFT, padx=10, pady=10)

brightness_var = tk.IntVar(value=80)  # Sử dụng IntVar để đảm bảo giá trị là integer

brightness_slider = ttk.Scale(bright_frame, from_=0, to=255, orient=tk.HORIZONTAL, length=400, style='Horizontal.TScale',
                              variable=brightness_var,
                              command=lambda _: on_brightness_change(brightness_var.get()))
brightness_slider.pack(side=tk.LEFT, padx=10, pady=10, fill='x', expand=True)

# Status Label
status = ttk.Label(root, text="Chưa kết nối BLE", foreground="#ffcc00", style='TLabel')  # Yellow for status
status.pack(pady=10)

# Log Box
log_frame = tk.Frame(root, bg="#1e1e2f", bd=2, relief="groove")
log_frame.pack(pady=10, padx=20, fill='both', expand=True)

text_box = scrolledtext.ScrolledText(log_frame, width=90, height=20, bg="#2a2a4a", fg="#ffffff",
                                     font=("Consolas", 10), insertbackground='white', borderwidth=0)
text_box.pack(fill='both', expand=True, padx=5, pady=5)

# ==================== LOG ====================
def log(msg):
    text_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    text_box.see(tk.END)

def clear_log():
    text_box.delete(1.0, tk.END)

# ==================== BLE ====================
async def read_device_info():
    if not connected:
        return

    try:
        raw = await client.read_gatt_char(DEVICE_INFO_UUID)
        if not raw:
            return
        text = raw.decode(errors="ignore").strip()
        info = {}
        for line in text.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                info[key.strip()] = value.strip().strip('"') 
                
        log("======== DEVICE INFO ========")
        log(f"Battery Level     : {info.get('Battery Level')}%")
        log(f"Device Name       : {info.get('Device Name')}")
        log(f"Device Picture    : {info.get('Device Picture')}")
        log(f"Firmware Version  : {info.get('Firmware Version')}")
        log(f"Model ID          : {info.get('Model ID')}")
        log("=============================")

        # ĐẨY LÊN FIREBASE THEO ĐÚNG YÊU CẦU
        sync_device_info_to_firebase(info)

    except Exception as e:
        log(f"Lỗi đọc Device Info: {e}")

async def connect_ble():
    global client, connected
    log("Đang quét XIAO...")
    devices = await BleakScanner.discover(timeout=3)
    target = None

    for d in devices:
        if d.name and TARGET_NAME_CONTAINS in d.name:
            target = d
            break

    if not target:
        messagebox.showerror("Lỗi", "Không tìm thấy XIAO!")
        return

    client = BleakClient(target.address)
    try:
        await client.connect()
        connected = True
        status.config(text=f"Đã kết nối: {target.name}", foreground="#00ff00")  # Green for connected
        btn_connect.config(state="disabled")
        btn_disconnect.config(state="normal")
        log("Kết nối BLE thành công!")

        #ĐỌC THÔNG TIN THIẾT BỊ
        await read_device_info()
        # Đồng bộ từ Firebase
        await sync_from_firebase()

    except Exception as e:
        log(f"Lỗi kết nối: {e}")

async def disconnect_ble():
    global connected, client
    if client and connected:
        try:
            await client.disconnect()
            log("BLE đã ngắt kết nối")
        except Exception as e:
            log(f"Lỗi khi ngắt BLE: {e}")
    else:
        log("Chưa kết nối BLE")
    connected = False
    btn_connect.config(state="normal")
    btn_disconnect.config(state="disabled")
    status.config(text="BLE ngắt kết nối • Firebase vẫn hoạt động", foreground="#ffcc00")

# ==================== SEND BLE ====================
MODE_MAP = {
    "OFF":   0,
    "MODE1": 1,
    "MODE2": 2,
    "MODE3": 3
}

async def send_mode(mode):
    if not connected: return
    value = MODE_MAP.get(mode, 0)
    await client.write_gatt_char(MODE_UUID, bytearray([value]))

async def send_brightness(val):
    if not connected: return
    await client.write_gatt_char(BRIGHT_UUID, bytearray([val]))
    log(f"Gửi BRIGHTNESS: {val}")

def on_brightness_change(val):
    asyncio.run_coroutine_threadsafe(send_brightness(val), loop)
    db.child("device_setting").update({"brightness": val})

# ==================== FIREBASE ====================

def sync_device_info_to_firebase(info_dict):
    """Đẩy thông tin thiết bị lên Firebase theo đúng cấu trúc bạn yêu cầu"""
    try:
        data = {
            "Battery Level": info_dict.get("Battery Level", ""),
            "Device Name": info_dict.get("Device Name", ""),
            "Device Picture": info_dict.get("Device Picture", ""), 
            "Firmware Version": info_dict.get("Firmware Version", ""),
            "Model ID": info_dict.get("Model ID", "")
        }
        
        db.child("device_info").set(data)
        
    except Exception as e:
        log(f"Lỗi đẩy device_info lên Firebase: {e}")

def firebase_listener(event):
    path = event["path"]
    data = event["data"]
    if path == "/effect_mode":
        asyncio.run_coroutine_threadsafe(send_mode(str(data).upper()), loop)
    elif path == "/brightness":
        brightness_var.set(int(data))
        asyncio.run_coroutine_threadsafe(send_brightness(int(data)), loop)

async def sync_from_firebase():
    """Đọc dữ liệu device_setting từ Firebase lúc app khởi động và gửi lệnh BLE"""
    global connected
    try:
        setting = db.child("device_setting").get().val()
        if not setting:
            log("Firebase chưa có dữ liệu device_setting, dùng mặc định")
            setting = {"effect_mode":"OFF", "brightness":80}

        mode = setting.get("effect_mode", "OFF").upper()
        brightness = int(setting.get("brightness", 80))
        brightness_var.set(brightness)
        log(f"Firebase yêu cầu lúc khởi tạo → Mode: {mode}, Brightness: {brightness}")

        if connected:
            await send_mode(mode)
            await send_brightness(brightness)
        else:
            log("Chưa kết nối BLE → lệnh sẽ gửi khi connect")
    except Exception as e:
        log(f"Lỗi đồng bộ từ Firebase: {e}")

# ==================== THREAD ====================
def start_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

def thread_connect():
    asyncio.run_coroutine_threadsafe(connect_ble(), loop)

def thread_disconnect():
    asyncio.run_coroutine_threadsafe(disconnect_ble(), loop)

threading.Thread(target=start_loop, daemon=True).start()

# ==================== FIREBASE STREAM ====================
stream = db.child("device_setting").stream(firebase_listener)

# ==================== START ====================
log("App sẵn sàng...")
root.mainloop()
stream.close()