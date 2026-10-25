# cloud/yolo-service/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py model.py ./

# Weight KHÔNG COPY vào image (quá nặng) — mount volume ngoài,
# trỏ YOLO_MODEL_PATH tới best.pt (compose sẽ cấu hình)
ENV YOLO_MODEL_PATH=/models/best.pt \
    YOLO_MODEL=yolo26s \
    YOLO_CONF=0.25

EXPOSE 8030
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8030"]
