# Báo cáo và đánh giá model YOLO nhận diện gà và phát hiện bệnh gà
## I Báo cáo và đánh giá model YOLO nhận diện gà
![alt text](image.png)
Model đang bị overfiting với kết quả loss của val bị lệch so mới train

- TĂNG VÀ ĐA DẠNG HÓA DỮ LIỆU (Quan trọng nhất!)
    ```python
    # File training config
    augment_config = {
        'hsv_h': 0.015,      # Hue shift
        'hsv_s': 0.7,        # Saturation
        'hsv_v': 0.4,        # Value brightness
        'degrees': 10,       # Rotation
        'translate': 0.1,    # Shift image
        'scale': 0.5,        # Zoom in/out
        'flipud': 0.5,       # Flip vertical
        'fliplr': 0.5,       # Flip horizontal
        'mosaic': 1.0,       # Mosaic augmentation
        'mixup': 0.1,        # Mixup blending
        'erasing': 0.0       # Random erasing
    }
    ```
- ĐIỀU CHỈNH LEARNING RATE & TRAINING STRATEGY
    ```python
    # Giảm learning rate
    model_config = {
        'lr0': 0.001,        # Từ 0.01 xuống 0.001
        'lrf': 0.01,         # Final LR ratio
        'momentum': 0.937,
        'weight_decay': 0.0005,  # L2 regularization
    }

    # Early stopping (stop sớm khi val không cải thiện)
    training_config = {
        'epochs': 100,
        'patience': 15,      # Stop nếu val không tốt 15 epoch
        'imgsz': 416,        # Input image size (nhỏ hơn = ít memorize)
        'batch': 16,         # Batch size (nhỏ hơn = noise más tốt)
    }
    ```

## II Báo cáo và đánh giá model YOLO nhận diện bệnh gà

![alt text](image.png)

Model đang bị overfiting
| Chỉ số          | Giá trị | Đánh giá        |
|-----------------|---------|-----------------|
| Precision       | ~87%    | Tốt             |
| Recall          | ~88%    | Tốt             |
| mAP@0.5         | ~90%    | Khá tốt         |
| Box Loss Gap    | 0.75    | Overfitting cao |
| Class Loss Gap  | ~0      | Hoàn hảo        |
| DFL Loss Gap    | 0.75    | Overfitting cao |

1.Tăng & Đa Dạng Hóa Dataset
Lý do:

Dataset hiện tại quá nhỏ (dự đoán < 200 ảnh)
Model memorize train data thay vì học pattern chung
Localization (Box Loss) cần nhiều ví dụ đa dạng để học vị trí bệnh chính xác
Hành động:
- Mục tiêu:
    - Train: 300-500 ảnh (tối ưu 500+)
    - Val: 50-100 ảnh/loại bệnh
    - Test: 50-100 ảnh/loại bệnh
    - Balanced: mỗi loại bệnh ~250 ảnh (25%)

- Cách collect:
    1. Chụp ảnh từ nhiều chuồng khác nhau
    2. Khác góc chụp (trên, dưới, bên)
    3. Khác ánh sáng (sáng, tối, đèn)
    4. Khác con gà (size, màu lông, breed)

- Thêm Aggressive Data Augmentation
Lý do:

Augmentation giả tạo dữ liệu mới từ ảnh cũ
Giúp model học pattern chung thay vì memorize
Đặc biệt quan trọng khi dataset nhỏ

Hành động:
```python
# Config augmentation trong training
augment_config = {
    # Màu sắc
    'hsv_h': 0.025,      # Hue shift: khác màu bệnh
    'hsv_s': 0.9,        # Saturation: khác độ bão hòa
    'hsv_v': 0.6,        # Value brightness: khác độ sáng
    
    # Hình học
    'degrees': 25,       # Quay ảnh 25 độ
    'translate': 0.25,   # Dịch ảnh 25%
    'scale': 0.8,        # Zoom in/out 80-120%
    'flipud': 0.8,       # Lật dọc 80%
    'fliplr': 0.8,       # Lật ngang 80%
    
    # Kết hợp
    'mosaic': 1.0,       # Mix 4 ảnh lại
    'mixup': 0.25,       # Blend 2 ảnh
    'erasing': 0.15,     # Xóa random vùng
}
```
Giảm Learning Rate
Lý do:

Learning rate cao → model learn quá nhanh → memorize
Learning rate thấp → model learn chậm → generalize tốt
Đặc biệt quan trọng khi dataset nhỏ

Hành động:
```python
# Thay đổi config training
lr0: 0.0003          # Từ 0.01 xuống 0.0003 (33x nhỏ hơn)
lrf: 0.01            # Final learning rate ratio
momentum: 0.937

# Lý do: Learning rate nhỏ → step nhỏ → khó memorize
```

Tăng Weight Decay (L2 Regularization)
Lý do:

Regularization penalize large weights
Ngăn model học những weight lạ lùng (dấu hiệu memorizing)
Buộc model học simple pattern

Hành động:
```python
# Config training
patience: 25           # Nếu val không tốt 25 epoch liên tiếp → stop
epochs: 150           # Cố gắng tối đa 150 epoch

# Ví dụ:
Epoch 1-30:  val loss giảm ✓ (continue training)
Epoch 31-55: val loss tăng (patience -= 1)
Epoch 56:    val loss vẫn cao 25 lần → STOP 
```