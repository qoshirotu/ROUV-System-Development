import asyncio
import websockets
import cv2
import base64
import json
import time
import serial
import threading

LAPTOP_IP = "192.168.1.6"
LAPTOP_PORT = 8765
CAMERA_SOURCE = "/dev/video0"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS_TARGET = 20
JPEG_QUALITY = 90

# Serial ke ESP
ESP_SERIAL_PORT = "/dev/ttyUSB0"   # sesuaikan jika perlu
ESP_BAUD_RATE = 115200

esp_serial = None
serial_lock = threading.Lock() # Mengamankan perpindahan status serial antar-thread

def connect_esp():
    global esp_serial
    with serial_lock:
        try:
            # Jika sebelumnya ada koneksi rusak, tutup dulu
            if esp_serial and esp_serial.is_open:
                esp_serial.close()
        except:
            pass
        
        try:
            print(f"[RPI] Mencoba konek serial ke ESP di {ESP_SERIAL_PORT} @ {ESP_BAUD_RATE}")
            esp_serial = serial.Serial(ESP_SERIAL_PORT, ESP_BAUD_RATE, timeout=1)
            time.sleep(2)  # tunggu board reset setelah serial connect
            print(f"[RPI] Serial ke ESP terhubung di {ESP_SERIAL_PORT}")
        except Exception as e:
            esp_serial = None
            print(f"[RPI] WARNING: Gagal konek serial ke ESP: {e}")

def send_to_esp(payload: dict):
    global esp_serial
    
    # [AUTO-RECONNECT ESP] Jika serial kosong, coba hubungkan kembali
    if esp_serial is None or not esp_serial.is_open:
        print("[RPI] Serial ESP terputus, mencoba menghubungkan kembali...")
        connect_esp()
        if esp_serial is None or not esp_serial.is_open:
            return

    try:
        line = json.dumps(payload) + "\n"
        esp_serial.write(line.encode("utf-8"))
        print(f"[RPI] Kirim ke ESP: {line.strip()}")
    except Exception as e:
        print(f"[RPI] ERROR kirim serial: {e}")
        esp_serial = None # Set ke None agar loop berikutnya memicu reconnect

def read_from_esp():
    global esp_serial
    while True:
        try:
            if esp_serial and esp_serial.is_open:
                if esp_serial.in_waiting > 0:
                    line = esp_serial.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        print(f"[ESP] {line}")
            else:
                # Jika mati, tidur 2 detik sebelum thread ini mengecek lagi
                time.sleep(2)
                continue
        except Exception as e:
            print(f"[RPI] ERROR baca serial ESP (Kemungkinan kabel lepas): {e}")
            esp_serial = None
        time.sleep(0.05)

async def handle_commands(ws):
    async for message in ws:
        try:
            data = json.loads(message)

            if data.get("type") == "motor_command":
                print(f"[RPI] Terima perintah motor: {data}")

                ts_client = data.get("ts_client")            
                delay_to_server_ms = data.get("delay_to_server_ms")
                command = data.get("command")
                left = data.get("left")
                right = data.get("right")
                command_id = data.get("command_id")

                ts_serial = int(time.time() * 1000)

                esp_payload = dict(data)
                esp_payload["ts_serial"] = ts_serial
                send_to_esp(esp_payload)

                ack = {
                    "type": "motor_ack",
                    "message": f"Perintah diteruskan ke ESP: {command or ''}",
                    "command": command,
                    "ts_client": ts_client,
                    "delay_to_server_ms": delay_to_server_ms,
                    "ts_serial": ts_serial,
                    "left": left,
                    "right": right,
                    "command_id": command_id,  
                }
                print(f"[RPI] ACK to laptop: {ack}")
                await ws.send(json.dumps(ack))

        except json.JSONDecodeError:
            print(f"[RPI] Pesan tidak valid: {message}")
        except Exception as e:
            print(f"[RPI] ERROR handle_commands: {e}")

async def stream_video():
    uri = f"ws://{LAPTOP_IP}:{LAPTOP_PORT}/stream"
    print(f"[RPI] Menghubungkan ke Websocket Laptop: {uri}")

    cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG')) # Set MJPEG agar USB ringan
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS_TARGET)

    if not cap.isOpened():
        print("[RPI] ERROR: Kamera USB tidak bisa dibuka! Mencoba ulang nanti...")
        await asyncio.sleep(5)
        return

    try:
        async with websockets.connect(uri, max_size=10_000_000) as ws:
            print("[RPI] Terhubung ke Laptop! Mulai streaming...")
            frame_interval = 1.0 / FPS_TARGET

            while True:
                t0 = time.time()

                ret, frame = cap.read()
                
                # [AUTO-RECONNECT KAMERA USB]
                if not ret:
                    print("[RPI] ⚠️ Gagal baca frame! Me-restart driver kamera USB...")
                    cap.release()
                    await asyncio.sleep(2) # Beri jeda hardware beristirahat
                    
                    # Buka ulang internal kamera
                    cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_V4L2)
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                    continue

                ok, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
                )
                if not ok:
                    continue

                frame_b64 = base64.b64encode(buffer).decode("utf-8")
                payload = json.dumps({
                    "type": "frame",
                    "timestamp": time.time(),
                    "data": frame_b64
                })

                # Kirim frame ke laptop
                await ws.send(payload)

                # Jalankan fungsi pembaca perintah laptop secara non-blocking di dalam loop
                # Ini menggantikan asyncio.gather agar kontrol loop kamera dan websocket menyatu dengan aman
                try:
                    # Ambil perintah jika ada antrean pesan masuk dari laptop (timeout sangat kecil agar tidak macet)
                    message = await asyncio.wait_for(ws.recv(), timeout=0.001)
                    # Proses command secara background task agar tidak menghambat FPS kamera
                    asyncio.create_task(handle_commands_single(ws, message))
                except asyncio.TimeoutError:
                    pass # Tidak ada data masuk, tidak masalah

                elapsed = time.time() - t0
                sleep_time = frame_interval - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

    finally:
        cap.release()
        print("[RPI] Kamera dilepas dari memory")

# Fungsi pembantu untuk memproses satu perintah masuk dari laptop
async def handle_commands_single(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "motor_command":
            ts_serial = int(time.time() * 1000)
            esp_payload = dict(data)
            esp_payload["ts_serial"] = ts_serial
            send_to_esp(esp_payload)

            ack = {
                "type": "motor_ack",
                "message": f"Perintah diteruskan ke ESP",
                "command": data.get("command"),
                "ts_client": data.get("ts_client"),
                "delay_to_server_ms": data.get("delay_to_server_ms"),
                "ts_serial": ts_serial,
                "left": data.get("left"),
                "right": data.get("right"),
                "command_id": data.get("command_id"),
            }
            await ws.send(json.dumps(ack))
    except Exception as e:
        print(f"[RPI] Error single command: {e}")

if __name__ == "__main__":
    print("[RPI] USB Camera Streamer + Motor Controller dimulai")
    
    # [SOLUSI AUTOSTART] Beri jeda 10 detik di awal booting agar network & usb core stabil dulu
    print("[RPI] Memulai jeda amankan booting autostart (10 detik)...")
    time.sleep(10)

    # Jalankan koneksi awal ESP
    connect_esp()

    # Jalankan thread pembaca feedback dari ESP secara background permanen
    t = threading.Thread(target=read_from_esp, daemon=True)
    t.start()
    print("[RPI] Thread reader serial ESP aktif")

    # Loop utama penjaga koneksi Websocket Laptop
    while True:
        try:
            asyncio.run(stream_video())
        except KeyboardInterrupt:
            print("[RPI] Dihentikan user via Keyboard")
            break
        except Exception as e:
            print(f"[RPI] Koneksi ke laptop terputus ({e}). Mencoba ulang dalam 3 detik...")
            time.sleep(3)