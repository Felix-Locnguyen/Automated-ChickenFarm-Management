from ultralytics import YOLO
import os
import pandas as pd
import matplotlib.pyplot as plt

# Thiết lập đường dẫn 
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)
relative_path = os.path.join("runs", "train", "chicken_detection", "weights", "best.pt")

# model nhận diện gà
model_chicken_detection_path = os.path.join(parent_dir, "02_models", "yolo", relative_path)
# model nhận diện bệnh gà 
model_yolo_disease_path = os.path.join(parent_dir, "02_models", "yolo_disease", relative_path)
# Load model đã train
# model = YOLO(model_chicken_detection_path)

# # Đánh giá trên tập validation/test
# metrics = model.val()

# # In ra các metric chính
# print("Precision:", metrics.box.p)
# print("Recall:", metrics.box.r)
# print("mAP@0.5:", metrics.box.map50)
# print("mAP@0.5:0.95:", metrics.box.map)



# Đọc file kết quả
relative_path = os.path.join("runs", "train", "chicken_detection", "results.csv")
res_path_model_1 = os.path.join(parent_dir,"02_models",'yolo', relative_path)  # đường dẫn model nhận diện gà
res_path_model_2 = os.path.join(parent_dir,"02_models",'yolo_disease', relative_path) # đường dẫn nhận diện model  bệnh gà

for path in [res_path_model_1,res_path_model_2]:
    df = pd.read_csv(path)

    # Tạo figure với grid 2x2
    fig, axs = plt.subplots(2, 2, figsize=(12, 8))

    # Box loss
    axs[0, 0].plot(df["epoch"], df["train/box_loss"], label="Train Box Loss")
    axs[0, 0].plot(df["epoch"], df["val/box_loss"], label="Val Box Loss")
    axs[0, 0].set_title("Box Loss")
    axs[0, 0].legend()

    # Class loss
    axs[0, 1].plot(df["epoch"], df["train/cls_loss"], label="Train Cls Loss")
    axs[0, 1].plot(df["epoch"], df["val/cls_loss"], label="Val Cls Loss")
    axs[0, 1].set_title("Class Loss")
    axs[0, 1].legend()

    # DFL loss
    axs[1, 0].plot(df["epoch"], df["train/dfl_loss"], label="Train DFL Loss")
    axs[1, 0].plot(df["epoch"], df["val/dfl_loss"], label="Val DFL Loss")
    axs[1, 0].set_title("DFL Loss")
    axs[1, 0].legend()

    # Precision/Recall hoặc mAP
    axs[1, 1].plot(df["epoch"], df["metrics/precision(B)"], label="Precision")
    axs[1, 1].plot(df["epoch"], df["metrics/recall(B)"], label="Recall")
    axs[1, 1].plot(df["epoch"], df["metrics/mAP50(B)"], label="mAP@0.5")
    axs[1, 1].set_title("Metrics")
    axs[1, 1].legend()

    plt.tight_layout()
    plt.show()

