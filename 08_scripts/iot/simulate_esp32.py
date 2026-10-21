"""Test bench: giả lập ESP32 bằng Python — test toàn hệ thống IoT KHÔNG cần phần cứng.

Cách chạy (từ gốc repo, dùng venv của dự án):
    .venv/bin/python 08_scripts/iot/simulate_esp32.py --device-id 13
    .venv/bin/python 08_scripts/iot/simulate_esp32.py --device-id 13 --interval 3

Script đóng vai 1 ESP32 trong chuồng:
- PUBLISH readings JSON lên farm/sensor/{id} mỗi --interval giây
  (xoay vòng kịch bản: bình thường → nóng → lạnh → ẩm cao → hết thức ăn...)
- SUBSCRIBE farm/device/{id}/command:
    ON/OFF → in trạng thái relay giả lập
    FEED   → mô phỏng motor + load-cell chạy trong thread RIÊNG
             (callback của paho KHÔNG được chặn network loop — giống uplink backend)
"""

import argparse
import json
import logging
import threading
import time

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")


SCENARIOS = [
    ("Bình thường",             {"temperature": 28.0, "humidity": 55, "food_level": 75, "water_level": 80}),
    ("Nóng lên",                {"temperature": 38.0, "humidity": 50, "food_level": 74, "water_level": 79}),
    ("Nóng gay gắt",            {"temperature": 42.0, "humidity": 48, "food_level": 73, "water_level": 78}),
    ("Lạnh bất thường",         {"temperature": 17.0, "humidity": 55, "food_level": 72, "water_level": 77}),
    ("Ẩm cao — nguy cơ bệnh",   {"temperature": 30.0, "humidity": 85, "food_level": 71, "water_level": 76}),
    ("Sắp hết thức ăn",         {"temperature": 28.0, "humidity": 60, "food_level": 20, "water_level": 70}),
    ("Sắp hết nước",            {"temperature": 28.0, "humidity": 60, "food_level": 68, "water_level": 15}),
]


SCENARIO_EVERY_N_PUBLISHES = 12  # mỗi 12 lần publish → đổi kịch bản tiếp theo

def simulate_feed_motor(amount_kg: float):
    """Mô phỏng motor rải thức ăn + load-cell (HX711) cân realtime.

    Chạy trong THREAD RIÊNG — nếu chạy thẳng trong callback sẽ chặn
    mất toàn bộ luồng nhận dữ liệu MQTT (bài học thread-safety cũ).
    """
    print(f"  🌾 Motor BẬT — rải tới khi cân xác nhận đủ {amount_kg}kg...")
    steps = max(int(amount_kg * 10), 5)          # mỗi bước 0.1kg, tối thiểu 5 bước
    for i in range(1, steps + 1):
        time.sleep(0.4)
        print(f"     ⚖️  đang rải {i / 10:.1f}/{amount_kg} kg")
    print(f"  ✅ Cân xác nhận đủ {amount_kg}kg — motor DỪNG")


def on_message(client, userdata, msg):
    """Nhận lệnh từ backend — chạy trong network thread của paho."""
    try:
        data = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, AttributeError):
        logging.warning("Payload không phải JSON hợp lệ: %r", msg.payload)
        return


    command = data.get("command", "?")
    print(f"\n📥 LỆNH từ backend: {command}  params={data.get('params')}  "
          f"(device_type={data.get('device_type')})")

    if command == "ON":
        print("  🔌 Relay ON — thiết bị đang chạy (giả lập)")
    elif command == "OFF":
        print("  ⭕ Relay OFF — thiết bị đã tắt")
    elif command == "FEED":
        amount = float(data.get("params", {}).get("amount_kg", 1.0))
        threading.Thread(target=simulate_feed_motor, args=(amount,),
                         daemon=True).start()
    elif command == "SET_SPEED":
        print(f"  🌀 Quạt chạy mức {data.get('params', {}).get('speed')}%")
    else:
        print("  ❓ Lệnh không nhận diện được — bỏ qua")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Đã kết nối broker farm/device/{DEVICE_ID}/command")
        client.subscribe(f"farm/device/{DEVICE_ID}/command")
    else:
        logging.error("Kết nối broker thất bại rc=%s", rc)


def main():
    global DEVICE_ID
    parser = argparse.ArgumentParser(description="Giả lập ESP32 farm")
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--device-id", type=int, default=13,
                        help="device_id trong DB — topic sensor/command sẽ dùng id này")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="giây giữa 2 lần publish readings")
    args = parser.parse_args()
    DEVICE_ID = args.device_id

    client = mqtt.Client()
    
    global CLIENT
    CLIENT = client

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.broker, 1883, 60)
    client.loop_start()

    print(f"🚀 Giả lập ESP32 — sensor id={DEVICE_ID}, "
          f"mỗi {args.interval:.0f}s 1 lần. Ctrl+C để dừng.\n")

    cycle = 0
    try:
        while True:
            scenario_name, reading = SCENARIOS[
                (cycle // SCENARIO_EVERY_N_PUBLISHES) % len(SCENARIOS)
            ]
            payload = dict(reading, device_id=DEVICE_ID)
            client.publish(f"farm/sensor/{DEVICE_ID}", json.dumps(payload))
            print(f"📤 [{scenario_name}] temp={reading['temperature']}°C "
                  f"hum={reading['humidity']}% food={reading['food_level']}% "
                  f"water={reading['water_level']}%")
            cycle += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Dừng giả lập ESP32")
    finally:
        client.loop_stop()
        client.disconnect()


DEVICE_ID = 1  # sẽ được gán lại từ args trong main()

if __name__ == "__main__":
    main(CLIENT = None )