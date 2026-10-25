# 🐔 yolo-service — Nhận diện gà broiler (YOLO26)

FastAPI micro-service: nhận ảnh → trả JSON bbox + confidence.

## Chạy local (dùng `.venv` của repo, có GPU)

```bash
cd cloud/yolo-service
../../.venv/bin/uvicorn main:app --port 8030
```

## Test

```bash
# Sức khỏe service (lazy-load: loaded=false là bình thường, chưa có request nào)
curl http://127.0.0.1:8030/health

# Nhận diện 1 ảnh
curl -F "file=@../../04_machine_learning/datasets/chicken_v2_yolo/test/images/<tên ảnh>.jpg" \
     http://127.0.0.1:8030/detect
```

Kết quả ví dụ:

```json
{
  "model": "yolo26s",
  "count": 3,
  "detections": [
    {"bbox": [412.5, 201.0, 735.2, 588.4], "conf": 0.912, "cls": 0, "cls_name": "broiler"}
  ]
}
```

## Biến môi trường

| Env | Mặc định | Ý nghĩa |
|---|---|---|
| `YOLO_MODEL` | `yolo26s` | Tên model (`yolo26s` / `yolo26n`) |
| `YOLO_MODEL_PATH` | `04_machine_learning/models/chicken_detection/runs/<tên>/weights/best.pt` | Weight tuyệt đối (Docker dùng cái này) |
| `YOLO_CONF` | `0.25` | Ngưỡng confidence |

## Docker

```bash
docker build -t yolo-service cloud/yolo-service
docker run -p 8030:8030 \
  -v <đường dẫn best.pt>:/models/best.pt:ro \
  yolo-service
```
