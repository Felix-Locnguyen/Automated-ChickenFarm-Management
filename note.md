# 1 Bài học quy trình Setup Backend

## 1. Chuẩn bị nguyên liệu
- Luôn có file `requirements.txt` để liệt kê các package cần thiết.
- Cài đặt đồng loạt bằng `pip install -r requirements.txt`.

## 2. Quản lý secrets
- Dùng file `.env` để lưu thông tin nhạy cảm (DB URL, secret key).
- Đảm bảo `.env` nằm trong `.gitignore` để không bị commit lên git.

## 3. Tách cấu hình
- Viết `config.py` để đọc `.env`.
- Giúp thay đổi môi trường (dev/prod) mà không cần sửa code.
- Bảo mật hơn vì secret key không hardcoded.

## 4. Kết nối database
- Tạo `engine` để kết nối DB.
- Tạo `SessionLocal` để quản lý phiên làm việc với DB.
- Tạo `Base` cho ORM models.
- Viết `get_db()` với `yield` để đảm bảo session luôn được đóng sau khi dùng.

## 5. Định nghĩa package
- Thêm file `__init__.py` để Python nhận diện thư mục là package.
- Có thể để trống nhưng bắt buộc phải có.

## 6. Khởi tạo ứng dụng
- Viết `main.py` làm entry point.
- Khởi tạo FastAPI app, thêm middleware (ví dụ: CORS).
- Mount các router con vào app chính.
- Tạo bảng từ models (chỉ dùng trong dev).
- Định nghĩa route gốc `/`.

---

# 🎯 Bài học rút ra
- **Tách biệt cấu hình và code** → dễ bảo trì, dễ triển khai nhiều môi trường.  
- **Quản lý session đúng cách** → tránh rò rỉ kết nối DB.  
- **Dùng `.env` cho secrets** → bảo mật, không lộ thông tin nhạy cảm.  
- **Khởi tạo app chuẩn** → có middleware, routes, và entry point rõ ràng.  


---
---
# 2 Bài học từ Models (SQLAlchemy ORM)

## Nguyên lý chung
- **Class Python ↔ Bảng Database**
- **Object ↔ Row (dòng dữ liệu)**
- **Attribute ↔ Column (cột dữ liệu)**
- **relationship() ↔ JOIN tables**

## Cấu trúc Model
- Kế thừa từ `Base`
- Khai báo `__tablename__`
- Định nghĩa các `Column` với tham số phù hợp

## Các tham số quan trọng của Column
- `primary_key=True` → Khóa chính, tự tăng
- `unique=True` → Không trùng lặp
- `index=True` → Tạo chỉ mục, truy vấn nhanh
- `nullable=False` → Không được để trống
- `default=...` → Giá trị mặc định khi insert
- `server_default=func.now()` → Giá trị mặc định từ DB server
- `onupdate=func.now()` → Tự cập nhật khi record thay đổi

## Relationship
- `ForeignKey("users.id")` → Khóa ngoại liên kết bảng
- `relationship("User", back_populates="flocks")` → Quan hệ hai chiều
- `back_populates` → Đồng bộ dữ liệu giữa 2 bảng

## Thiết kế dữ liệu
- `Float` → Dữ liệu thập phân (nhiệt độ, độ ẩm, lượng thức ăn)
- `Boolean` → Trạng thái (true/false)
- `String` → Tên, mô tả, loại
- `DateTime` → Thời điểm tạo/cập nhật

## Tư duy hệ thống
- **User** có nhiều **Flock**
- **Flock** có nhiều **Device**, **FeedingLog**, **HealthRecord**, **Alert**
- **Device** sinh ra **SensorReading**
- **Alert** liên kết cả **Flock** và **Device**

👉 ORM giúp bạn làm việc với DB bằng object Python, không cần viết SQL thủ công.
---
---
# 3 Bài học từ Schemas (Pydantic)

## Vì sao cần tách Schema?
- **Tránh lộ thông tin nhạy cảm**: Không trả về password hash hay các trường nội bộ.
- **An toàn hơn**: Chỉ nhận và trả về những field cần thiết cho request/response.
- **Rõ ràng**: Phân biệt giữa dữ liệu đầu vào (Create) và dữ liệu đầu ra (Response).
- **Tương thích ORM**: `orm_mode = True` giúp Pydantic đọc trực tiếp object SQLAlchemy.

## Nguyên tắc nhớ
- **Request schema (Create)**: chỉ chứa dữ liệu mà client gửi lên để tạo mới.
- **Response schema**: chỉ chứa dữ liệu mà client cần xem, không bao gồm thông tin nhạy cảm.
- **Không dùng trực tiếp SQLAlchemy model trong API** → dễ lộ dữ liệu, khó kiểm soát.
- **Luôn dùng Pydantic schema** để kiểm tra, xác thực và giới hạn dữ liệu.

👉 Bài học cốt lõi: **Tách riêng schema giúp API an toàn, rõ ràng, và dễ bảo trì.**


---
---

# 4 Bài học từ Bước 4: API Routes

## REST API Pattern
- **GET** → Lấy dữ liệu (Read)
- **POST** → Tạo mới dữ liệu (Create)
- **PUT** → Cập nhật dữ liệu (Update)
- **DELETE** → Xóa dữ liệu (Delete)

## Các thao tác CRUD trong code
- `db.query(Model).filter().first()` → SELECT dữ liệu từ bảng
- `db.add(obj)` → Thêm object mới vào session
- `db.commit()` → Ghi thay đổi xuống database
- `db.refresh(obj)` → Làm mới object, lấy giá trị tự sinh (id, created_at)
- `raise HTTPException(...)` → Trả về lỗi HTTP nếu dữ liệu không tồn tại hoặc không hợp lệ

## Ví dụ: Flocks API
- `GET /flocks` → Lấy danh sách đàn gà
- `POST /flocks` → Tạo đàn gà mới
- `GET /flocks/{id}` → Lấy chi tiết đàn gà theo ID
- `PUT /flocks/{id}` → Cập nhật thông tin đàn gà
- `DELETE /flocks/{id}` → Xóa đàn gà

## Quy tắc chung
- Luôn dùng `response_model` để kiểm soát dữ liệu trả về.
- Luôn kiểm tra dữ liệu có tồn tại trước khi cập nhật/xóa.
- Sử dụng `Depends(get_db)` để inject session DB vào mỗi route.
- Dữ liệu từ client (Pydantic schema) → chuyển thành dict → tạo object SQLAlchemy → lưu vào DB.

---
---
# 5 Bài học từ Bước 5: Services

## Nguyên tắc chính
- **Route (API)**: chỉ nhận request từ client → gọi service → trả response.
- **Service**: chứa business logic (nghiệp vụ), ví dụ:
  - Kiểm tra ngưỡng sensor để tạo cảnh báo.
  - Lấy trạng thái thiết bị hoặc bật/tắt thiết bị.

## Lợi ích của việc tách Service
- Code **sạch**: routes không bị nhồi nhét logic.
- Code **dễ bảo trì**: thay đổi logic chỉ cần sửa trong service.
- Code **dễ test**: có thể test service độc lập mà không cần chạy API.
- Code **tái sử dụng**: cùng một service có thể được gọi từ nhiều routes.

## Ví dụ minh họa
### Alert Service
- `check_environment_alerts(db, reading)`:
  - Kiểm tra nhiệt độ, độ ẩm so với ngưỡng.
  - Tạo object `Alert` nếu vượt ngưỡng.
  - Lưu xuống DB và trả về danh sách cảnh báo.

### Device Service
- `get_device_status(db, device_id)`:
  - Truy vấn DB để lấy thông tin thiết bị theo ID.
- `toggle_device(db, device_id)`:
  - Đảo trạng thái `is_active`.
  - Cập nhật `status` thành `"online"` hoặc `"offline"`.
  - Commit thay đổi xuống DB.

## Bài học tổng quát
- **Routes = giao tiếp với client.**
- **Services = xử lý nghiệp vụ.**
- Tách biệt này giúp dự án có kiến trúc rõ ràng, dễ mở rộng và chuyên nghiệp.



---
---
# 6 Bài học từ Bước 6: Utils

## Ý nghĩa của Utils
- **Utils (utilities)** là nơi tập trung các hàm, constants, và công cụ nhỏ hỗ trợ toàn bộ hệ thống.
- Giúp code **tái sử dụng**, **dễ bảo trì**, và **dễ mở rộng**.

## File 25: thresholds.py
- Định nghĩa **constants** (ngưỡng nhiệt độ, độ ẩm, thức ăn, nước).
- **Bài học**: thay đổi giá trị ở một chỗ → áp dụng mọi nơi trong hệ thống.
- Constants đóng vai trò **mặc định** khi chưa có dữ liệu người dùng.

## File 26: validators.py
- Chứa các hàm kiểm tra dữ liệu đầu vào:
  - `validate_email` → kiểm tra email có chứa `@` và `.`.
  - `validate_temperature` → nhiệt độ nằm trong khoảng -10°C đến 60°C.
  - `validate_humidity` → độ ẩm nằm trong khoảng 0% đến 100%.
  - (có thể thêm validate cho mức thức ăn/nước).
- **Bài học**: luôn kiểm tra dữ liệu trước khi xử lý/lưu vào DB để tránh lỗi hoặc dữ liệu không hợp lệ.

## Tổng kết
- **Utils = hộp công cụ chung** cho toàn dự án.
- Constants giúp quản lý ngưỡng dễ dàng.
- Validators đảm bảo dữ liệu hợp lệ.
- Tách riêng utils giúp code **sạch**, **dễ đọc**, và **chuyên nghiệp**.
