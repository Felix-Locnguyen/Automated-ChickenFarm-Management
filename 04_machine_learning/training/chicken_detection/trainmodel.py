from ultralytics import YOLO


def train_yolov8s(data_path: str, epochs: int = 100, imgsz: int = 320):
  # Tải mô hình YOLOv8s pre-trained
  model = YOLO("yolov8s.pt")

  # Bắt đầu train mô hình
  results = model.train(data=data_path, epochs=epochs, imgsz=imgsz,device=0, batch= 16)

  return results
import cv2

def test_video_cv2(model_path: str, video_path: str):
  # Tải mô hình
  model = YOLO(model_path)

  # Mở video bằng OpenCV
  cap = cv2.VideoCapture(video_path)

  while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
      break

    # Dự đoán trên từng frame
    results = model(frame, conf=0.3)

    # Lấy frame đã được vẽ sẵn bounding box từ ultralytics
    annotated_frame = results[0].plot()

    # Hiển thị frame bằng cv2
    cv2.imshow("YOLOv8 Video Test", annotated_frame)

    # Nhấn phím 'q' để thoát cửa sổ hiển thị
    if cv2.waitKey(1) & 0xFF == ord("q"):
      break

  # Giải phóng tài nguyên
  cap.release()

if __name__ == "__main__":
#   path = "/home/loc-nguyen/PROJECT/AI/Automated-ChickenFarm-Management/04_machine_learning/datasets/chicken_counting_v18_yolo/data.yaml"
#   train_yolov8s(path)


    #   test
    model_path = r"/home/loc-nguyen/PROJECT/AI/Automated-ChickenFarm-Management/runs/detect/train-5/weights/best.pt"
    video_path = r"/home/loc-nguyen/PROJECT/AI/Automated-ChickenFarm-Management/04_machine_learning/testing/video_test.mp4"
    test_video_cv2(model_path, video_path)