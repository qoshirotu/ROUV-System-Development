import asyncio
import base64
import json
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from http.server import SimpleHTTPRequestHandler
import socketserver
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import websockets
from ultralytics import YOLO

# =========================
# PATH & KONFIGURASI GLOBAL
# =========================
BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"

HTTP_HOST = "127.0.0.1"
# HTTP_HOST = "0.0.0.0"  # jika ingin bisa diakses di perangkat lain
HTTP_PORT = 8000         # serve index.html
WS_HOST = "0.0.0.0"
WS_PORT = 8765           # /ui dan /stream
AUTO_OPEN_BROWSER = True

# SETTINGS dari UI
SETTINGS = {
    "yolo_model_name": "best.pt",
    "yolo_conf": 0.5,
    "yolo_imgsz": 416,           # Turunkan dari 640 untuk performa
    "process_every_n_frame": 2,  # Naikkan dari 2 untuk performa
    "jpeg_quality": 90,          # Turunkan dari 70 untuk bandwidth
    "display_width": 1280,       # Resize output untuk WebSocket
}

ALLOWED_IMGSZ = {320, 416, 640}

# =========================
# GLOBAL STATE
# =========================
ui_clients = set()
latest_result = {
    "frame_b64": None,
    "detections": [],
    "yolo_fps": 0.0,
    "yolo_process_ms": 0.0,
    "frame_count": 0,
    "camera_connected": False,
}

# Websocket Raspi
rpi_ws = None

# YOLO Model
model = None
model_lock = threading.Lock()
tracker_initialized = False

# Async Queues untuk pipeline
frame_queue = Queue(maxsize=2)
result_queue = Queue(maxsize=2)

# Thread Pool untuk blocking operations
executor = ThreadPoolExecutor(max_workers=2)

# =========================
# UTIL PATH (DEV + PyInstaller)
# =========================
def resource_path(relative_path: str) -> str:
    """Get resource path untuk PyInstaller compatibility"""
    base_path = getattr(sys, "_MEIPASS", str(BASE_DIR))
    return os.path.join(base_path, relative_path)

def current_settings_payload() -> dict:
    """Return current settings sebagai payload"""
    return {
        "type": "settings_state",
        "settings": {
            "yolo_model_name": SETTINGS["yolo_model_name"],
            "yolo_conf": SETTINGS["yolo_conf"],
            "yolo_imgsz": SETTINGS["yolo_imgsz"],
            "process_every_n_frame": SETTINGS["process_every_n_frame"],
            "jpeg_quality": SETTINGS["jpeg_quality"],
            "display_width": SETTINGS["display_width"],
        },
    }

# =========================
# YOLO LOADING & WARMUP
# =========================
def load_yolo(model_name: str | None = None) -> None:
    """Load YOLO model dengan warmup untuk performa optimal"""
    global model, tracker_initialized

    model_name = model_name or SETTINGS["yolo_model_name"]
    model_path = resource_path(model_name)

    print(f"[INFO] Loading YOLO model: {model_path}")
    loaded = YOLO(model_path)

    # Warmup model dengan dummy inference
    print("[INFO] Warming up model...")
    dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
    _ = loaded(dummy_frame, verbose=False)

    with model_lock:
        model = loaded
        tracker_initialized = False

    SETTINGS["yolo_model_name"] = model_name
    print(f"[INFO] YOLO loaded & warmed up: {model_name}")

# =========================
# SETTINGS VALIDATION & UPDATE
# =========================
def validate_settings(new_settings: dict) -> dict:
    """Validate settings sebelum di-apply"""
    validated = {}

    if "yolo_model_name" in new_settings:
        model_name = str(new_settings["yolo_model_name"]).strip()
        if not model_name:
            raise ValueError("ylo_model_name wajib diisi")
        if not os.path.exists(resource_path(model_name)):
            raise ValueError(f"Model tidak ditemukan: {model_name}")
        validated["yolo_model_name"] = model_name

    if "yolo_conf" in new_settings:
        value = float(new_settings["yolo_conf"])
        if not 0.0 <= value <= 1.0:
            raise ValueError("yolo_conf harus di antara 0.0 sampai 1.0")
        validated["yolo_conf"] = value

    if "yolo_imgsz" in new_settings:
        value = int(new_settings["yolo_imgsz"])
        if value not in ALLOWED_IMGSZ:
            raise ValueError(f"yolo_imgsz harus salah satu dari {sorted(ALLOWED_IMGSZ)}")
        validated["yolo_imgsz"] = value

    if "process_every_n_frame" in new_settings:
        value = int(new_settings["process_every_n_frame"])
        if not 1 <= value <= 10:
            raise ValueError("process_every_n_frame harus 1 sampai 10")
        validated["process_every_n_frame"] = value

    if "jpeg_quality" in new_settings:
        value = int(new_settings["jpeg_quality"])
        if not 9 <= value <= 100:
            raise ValueError("jpeg_quality harus 10 sampai 100")
        validated["jpeg_quality"] = value

    if "display_width" in new_settings:
        value = int(new_settings["display_width"])
        if not 100 <= value <= 1920:
            raise ValueError("display_width harus 100 sampai 1920")
        validated["display_width"] = value

    return validated

def apply_settings(new_settings: dict) -> dict:
    """Apply validated settings"""
    validated = validate_settings(new_settings)
    reload_model = (
        "yolo_model_name" in validated
        and validated["yolo_model_name"] != SETTINGS["yolo_model_name"]
    )

    SETTINGS.update(validated)

    print(
        f"[INFO] Settings updated: "
        f"conf={SETTINGS['yolo_conf']} "
        f"imgsz={SETTINGS['yolo_imgsz']} "
        f"N={SETTINGS['process_every_n_frame']} "
        f"jpeg={SETTINGS['jpeg_quality']}"
    )

    if reload_model:
        load_yolo(SETTINGS["yolo_model_name"])

    return current_settings_payload()

# =========================
# YOLO PROCESSING (Blocking - dijalankan di thread pool)
# =========================
def process_yolo(frame):
    """Blocking YOLO processing dengan tracking"""
    global tracker_initialized

    t0 = time.time()

    with model_lock:
        if model is None:
            return frame, [], 0.0, 0.0

        if not tracker_initialized:
            tracker_initialized = True

        results = model.track(
            frame,
            conf=SETTINGS["yolo_conf"],
            imgsz=SETTINGS["yolo_imgsz"],
            verbose=False,
            persist=True,
        )

    processed_frame, detections = extract_detections(frame, results)

    elapsed = time.time() - t0
    yolo_fps = round(1.0 / max(elapsed, 1e-6), 2)
    yolo_process_ms = round(elapsed * 1000.0, 2)

    return processed_frame, detections, yolo_fps, yolo_process_ms

def extract_detections(frame, results):
    """Extract boxes dan draw annotations"""
    detections = []

    r0 = results[0]
    boxes = r0.boxes
    if boxes is None or len(boxes) == 0:
        return frame, detections

    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    cls_ids = boxes.cls.cpu().numpy().astype(int)

    track_ids = boxes.id
    if track_ids is not None:
        track_ids = track_ids.int().cpu().numpy().tolist()
    else:
        track_ids = [None] * len(xyxy)

    with model_lock:
        names = model.names

    for (x1, y1, x2, y2), conf, cls_id, tid in zip(xyxy, confs, cls_ids, track_ids):
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        label = names[int(cls_id)]

        detections.append({
            "id": tid,
            "label": label,
            "conf": round(float(conf), 3),
            "bbox": [x1, y1, x2, y2],
        })

        text = f"{label} {conf:.2f}"
        if tid is not None:
            text = f"ID {tid} {label} {conf:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame, text, (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )

    return frame, detections

def draw_detections(frame, detections):
    """Redraw existing detections tanpa inference ulang"""
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        label = det["label"]
        conf = det["conf"]
        tid = det.get("id")

        text = f"{label} {conf:.2f}"
        if tid is not None:
            text = f"ID {tid} {label} {conf:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame, text, (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )

    return frame

def encode_frame(frame):
    """Blocking JPEG encode dengan optimasi"""
    display_width = SETTINGS["display_width"]
    h, w = frame.shape[:2]
    if w > display_width:
        scale = display_width / w
        new_h = int(h * scale)
        frame = cv2.resize(
            frame,
            (display_width, new_h),
            interpolation=cv2.INTER_LINEAR
        )

    ok, encoded = cv2.imencode(
        ".jpg",
        frame,
        [
            cv2.IMWRITE_JPEG_QUALITY, SETTINGS["jpeg_quality"],
            cv2.IMWRITE_JPEG_PROGRESSIVE, 1,
            cv2.IMWRITE_JPEG_OPTIMIZE, 1
        ],
    )

    if not ok:
        return None

    return base64.b64encode(encoded.tobytes()).decode("utf-8")

# =========================
# BROADCAST KE UI (Async Optimized)
# =========================
async def safe_send(client, message):
    """Helper untuk send dengan error handling"""
    try:
        await client.send(message)
    except Exception as e:
        raise e

async def broadcast_to_ui(payload: dict) -> None:
    """Broadcast concurrent ke semua UI clients"""
    if not ui_clients:
        return

    message = json.dumps(payload)
    tasks = [safe_send(client, message) for client in ui_clients.copy()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for client, result in zip(list(ui_clients.copy()), results):
        if isinstance(result, Exception):
            ui_clients.discard(client)

# =========================
# KIRIM PERINTAH KE RASPI
# =========================
async def send_to_rpi(payload: dict) -> None:
    """Send motor command ke Raspberry Pi"""
    global rpi_ws

    if rpi_ws is None:
        print("[WARN] Raspi belum terhubung. Perintah motor tidak dikirim.")
        await broadcast_to_ui({
            "type": "motor_error",
            "message": "Raspberry Pi belum terhubung",
        })
        return

    try:
        await rpi_ws.send(json.dumps(payload))
        print(f"[INFO] Sent to RPi: {payload}")
    except Exception as e:
        print(f"[ERROR] Gagal kirim ke Raspi: {e}")
        await broadcast_to_ui({
            "type": "motor_error",
            "message": str(e),
        })

# =========================
# ASYNC PIPELINE: Receiver, Processor, Broadcaster
# =========================
async def frame_receiver(websocket):
    """Receive frames & motor ack dari Raspi dan push ke queue"""
    async for message in websocket:
        try:
            data = json.loads(message)

            # Motor ACK dari Raspi
            if data.get("type") == "motor_ack":
                ts_client = data.get("ts_client")
                ts_serial = data.get("ts_serial")
                delay_to_server_ms = data.get("delay_to_server_ms")
                command = data.get("command")
                left = data.get("left")
                right = data.get("right")
                command_id = data.get("command_id")

                delay_to_serial_ms = None
                if ts_client is not None and ts_serial is not None:
                    try:
                        ts_client_f = float(ts_client)
                        ts_serial_f = float(ts_serial)
                        delay_to_serial_ms = ts_serial_f - ts_client_f
                    except Exception:
                        delay_to_serial_ms = None

                if delay_to_serial_ms is not None:
                    data["delay_to_serial_ms"] = delay_to_serial_ms

                # Pastikan field penting tidak hilang
                if ts_client is not None:
                    data["ts_client"] = ts_client
                if delay_to_server_ms is not None:
                    data["delay_to_server_ms"] = delay_to_server_ms
                if command is not None:
                    data["command"] = command
                if left is not None:
                    data["left"] = left
                if right is not None:
                    data["right"] = right
                if command_id is not None:
                    data["command_id"] = command_id

                await broadcast_to_ui(data)
                continue

            if data.get("type") != "frame":
                continue

            frame_b64 = data.get("data")
            if not frame_b64:
                continue

            try:
                frame_queue.put_nowait((frame_b64, data.get("timestamp")))
            except asyncio.QueueFull:
                try:
                    frame_queue.get_nowait()
                    frame_queue.put_nowait((frame_b64, data.get("timestamp")))
                except Exception:
                    pass

        except Exception as e:
            print(f"[ERROR] frame_receiver: {e}")

async def frame_processor():
    """Process YOLO detection di background dengan thread pool"""
    frame_counter = 0
    loop = asyncio.get_running_loop()

    while True:
        frame_b64, timestamp = await frame_queue.get()

        try:
            raw = base64.b64decode(frame_b64)
            nparr = np.frombuffer(raw, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            frame_counter += 1

            if frame_counter % SETTINGS["process_every_n_frame"] == 0:
                processed_frame, detections, yolo_fps, yolo_process_ms = await loop.run_in_executor(
                    executor, process_yolo, frame
                )
                latest_result["detections"] = detections
                latest_result["yolo_fps"] = yolo_fps
                latest_result["yolo_process_ms"] = yolo_process_ms
            else:
                processed_frame = await loop.run_in_executor(
                    executor, draw_detections, frame, latest_result["detections"]
                )

            encoded_b64 = await loop.run_in_executor(
                executor, encode_frame, processed_frame
            )

            if encoded_b64 is None:
                continue

            await result_queue.put({
                "frame_b64": encoded_b64,
                "detections": latest_result["detections"],
                "yolo_fps": latest_result["yolo_fps"],
                "yolo_process_ms": latest_result["yolo_process_ms"],
                "frame_count": frame_counter,
                "timestamp": timestamp,
            })

        except Exception as e:
            print(f"[ERROR] frame_processor: {e}")

async def frame_broadcaster():
    """Broadcast hasil processing ke UI clients"""
    while True:
        result = await result_queue.get()

        latest_result.update(result)

        payload = {
            "type": "frame",
            "data": result["frame_b64"],
            "detections": result["detections"],
            "yolo_fps": result["yolo_fps"],
            "yolo_process_ms": result["yolo_process_ms"],
            "frame_count": result["frame_count"],
            "camera_connected": True,
            "ts": result["timestamp"],
            "settings": SETTINGS,
        }

        await broadcast_to_ui(payload)

# =========================
# HANDLER RPI STREAM (Async Pipeline)
# =========================
async def handle_rpi_stream(websocket):
    """Handle koneksi dari Raspberry Pi dengan async pipeline"""
    global rpi_ws

    rpi_ws = websocket
    print("[INFO] Raspberry Pi connected")
    latest_result["camera_connected"] = True

    await broadcast_to_ui({
        "type": "camera_status",
        "camera_connected": True
    })

    receiver_task = asyncio.create_task(frame_receiver(websocket))
    processor_task = asyncio.create_task(frame_processor())
    broadcaster_task = asyncio.create_task(frame_broadcaster())

    try:
        await receiver_task
    except websockets.exceptions.ConnectionClosed:
        print("[WARN] Raspberry Pi disconnected")
    except Exception as e:
        print(f"[ERROR] handle_rpi_stream: {e}")
    finally:
        processor_task.cancel()
        broadcaster_task.cancel()

        rpi_ws = None
        latest_result["camera_connected"] = False
        await broadcast_to_ui({
            "type": "camera_status",
            "camera_connected": False
        })

# =========================
# HANDLER UI DASHBOARD
# =========================
async def handle_ui(websocket):
    """Handle koneksi dari UI dashboard"""
    ui_clients.add(websocket)
    print("[INFO] UI connected")

    try:
        # Kirim settings awal
        await websocket.send(json.dumps(current_settings_payload()))
        # Kirim status kamera awal
        await websocket.send(json.dumps({
            "type": "camera_status",
            "camera_connected": latest_result["camera_connected"],
        }))

        # Kirim frame terakhir jika ada
        if latest_result["frame_b64"]:
            await websocket.send(json.dumps({
                "type": "frame",
                "data": latest_result["frame_b64"],
                "detections": latest_result["detections"],
                "yolo_fps": latest_result["yolo_fps"],
                "frame_count": latest_result["frame_count"],
                "camera_connected": latest_result["camera_connected"],
                "settings": SETTINGS,
            }))

        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                # Ambil timestamp & command_id dari UI kalau ada
                ts_client = data.get("ts_client")
                command_id = data.get("command_id")
                delay_to_server_ms = None
                if ts_client is not None:
                    try:
                        ts_client_f = float(ts_client)
                        ts_server = time.time() * 1000.0
                        delay_to_server_ms = ts_server - ts_client_f
                    except Exception:
                        delay_to_server_ms = None

                # Motor control commands
                if msg_type == "control":
                    left = int(data.get("left", 1500))
                    right = int(data.get("right", 1500))
                    payload = {
                        "type": "motor_command",
                        "command": "MOVE",
                        "left": left,
                        "right": right,
                    }
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi(payload)

                elif msg_type == "stop":
                    payload = {
                        "type": "motor_command",
                        "command": "STOP",
                    }
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi(payload)

                elif msg_type == "forward":
                    speed = int(data.get("speed", 200))
                    payload = {
                        "type": "motor_command",
                        "command": "FORWARD",
                        "speed": speed,
                    }
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi(payload)

                elif msg_type == "backward":
                    speed = int(data.get("speed", 200))
                    payload = {
                        "type": "motor_command",
                        "command": "BACKWARD",
                        "speed": speed,
                    }
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi(payload)

                elif msg_type == "turn_left":
                    speed = int(data.get("speed", 200))
                    payload = {
                        "type": "motor_command",
                        "command": "TURN_LEFT",
                        "speed": speed,
                    }
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi(payload)

                elif msg_type == "turn_right":
                    speed = int(data.get("speed", 200))
                    payload = {
                        "type": "motor_command",
                        "command": "TURN_RIGHT",
                        "speed": speed,
                    }
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi(payload)

                elif msg_type == "status":
                    payload = {
                        "type": "motor_command",
                        "command": "STATUS",
                    }
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi(payload)

                elif msg_type == "motor_command":
                    # untuk ballast / stepper dsb
                    payload = dict(data)
                    payload.pop("type", None)
                    if ts_client is not None:
                        payload["ts_client"] = ts_client
                    if delay_to_server_ms is not None:
                        payload["delay_to_server_ms"] = delay_to_server_ms
                    if command_id is not None:
                        payload["command_id"] = command_id
                    await send_to_rpi({
                        "type": "motor_command",
                        **payload
                    })

                elif msg_type == "get_settings":
                    await websocket.send(json.dumps(current_settings_payload()))

                elif msg_type == "settings_update":
                    payload = data.get("settings", {})
                    state = apply_settings(payload)
                    await broadcast_to_ui(state)
                    await websocket.send(json.dumps({
                        "type": "ack",
                        "action": "settings_update",
                        "ok": True,
                    }))

            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": str(e),
                }))
                print(f"[ERROR] handle_ui message: {e}")

    except websockets.exceptions.ConnectionClosed:
        print("[WARN] UI disconnected")
    finally:
        ui_clients.discard(websocket)

# =========================
# WEBSOCKET ROUTER
# =========================
async def ws_router(websocket):
    """Route WebSocket connections berdasarkan path"""
    path = websocket.request.path

    if path == "/stream":
        await handle_rpi_stream(websocket)
    elif path == "/ui":
        await handle_ui(websocket)
    else:
        print(f"[WARN] Unknown path: {path}")
        await websocket.close()

# =========================
# HTTP STATIC SERVER
# =========================
def run_http_server():
    """Serve static HTML/CSS/JS files"""
    os.chdir(UI_DIR)
    handler = SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None

    with socketserver.TCPServer((HTTP_HOST, HTTP_PORT), handler) as httpd:
        print(f"[INFO] HTTP UI  : http://{HTTP_HOST}:{HTTP_PORT}")
        httpd.serve_forever()

async def open_browser_later():
    """Open browser setelah server ready"""
    await asyncio.sleep(1.5)
    url = f"http://{HTTP_HOST}:{HTTP_PORT}/index copy 4.html"
    print(f"[INFO] Opening browser: {url}")
    webbrowser.open(url)

# =========================
# MAIN ENTRY POINT
# =========================
async def main():
    """Main async entry point"""
    load_yolo()

    print("[INFO] Mode koneksi: Laptop <-> Raspi <-> ESP")
    print(f"[INFO] WS UI    : ws://localhost:{WS_PORT}/ui")
    print(f"[INFO] WS Stream: ws://IP_LAPTOP:{WS_PORT}/stream")

    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    async with websockets.serve(
        ws_router,
        WS_HOST,
        WS_PORT,
        max_size=10_000_000,
        ping_interval=None,
        max_queue=100,
        write_limit=2**20,
        compression=None
    ):
        if AUTO_OPEN_BROWSER:
            asyncio.create_task(open_browser_later())

        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        executor.shutdown(wait=False)