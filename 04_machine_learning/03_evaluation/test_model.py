import pandas as pd 
import numpy as np 
import os, cv2, time
from ultralytics import YOLO



# Truy vấn và đọc dữ liệu model

def test_model_func(
        model_path=None,
        test_img_path= None,
        test_video_path = None,
):
    print(f'test model 1: model nhận diện gà với đường dẫn {model_path}')
    model_path = model_path
    test_img_path = test_img_path
    test_video_path = test_video_path

    model = YOLO(model_path)

    # Kiểm tra model với dữ liệu ảnh 
    results = model(test_img_path)
    # hiển thị kết quả
    results[0].show()

    # Kiểm tra với dữ liệu dạng video (nếu có)
    cap = cv2.VideoCapture(test_video_path)

    while cap.isOpened():
        start_time = time.time()  # bắt đầu đo thời gian

        ret, frame = cap.read()
        if not ret:
            break

        # Dự đoán trên frame
        results = model(frame, conf=0.1)

        # Vẽ bounding box lên frame
        annotated_frame = results[0].plot()

        # Tính FPS
        end_time = time.time()
        fps = 1 / (end_time - start_time)

        # Hiển thị FPS trên frame
        cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("YOLO Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    # Thiết lập đường dẫn 
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    relative_path = os.path.join("runs", "train", "chicken_detection", "weights", "best.pt")

    # model nhận diện gà
    model_chicken_detection_path = os.path.join(parent_dir, "02_models", "yolo", relative_path)
    # model nhận diện bệnh gà 
    model_yolo_disease_path = os.path.join(parent_dir, "02_models", "yolo_disease", relative_path)

    test_img_path = r'D:\Share_Projects\AutomatedChickenFarmManagemen-v2\04_machine_learning\01_training\01.1_disease\detection\chicken-disease-detection\raw_data_1\test\images\dieu-tri-benh-dau-ga-nhanh-chong_webp.rf.13c9e21adc763e0568fca493631323df.jpg'
    test_video_path = r'D:\Share_Projects\AutomatedChickenFarmManagement\backend\Camera_AI\Data\Test_data\Videos\video_test.mp4'

test_model_func(
    model_path=model_yolo_disease_path,
    test_img_path= test_img_path,
    test_video_path= test_video_path,
    )

