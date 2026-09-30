# 🐔 Ứng Dụng Quản Lý Trang Trại Gà

Hệ thống quản lý trang trại gà thông minh với giao diện phong cách nông nghiệp Việt.

## 📋 Cấu Trúc Dự Án

```
project/
├── src/
│   ├── main.jsx          # Entry point của React
│   ├── App.jsx           # Component chính
│   ├── app.css           # Styles của App component
│   └── index.css         # Global styles
├── index.html            # HTML template
├── package.json          # Dependencies
├── vite.config.js        # Vite configuration
└── README.md             # Tài liệu này
```

## 🚀 Cài Đặt & Chạy

### 1. Cài Đặt Dependencies
```bash
npm install
```

### 2. Chạy Development Server
```bash
npm run dev
```

Ứng dụng sẽ tự động mở trên: `http://localhost:5173`

### 3. Build Cho Production
```bash
npm run build
```

## 📱 Tính Năng Chính

- ✅ **Dashboard** - Tổng quan trang trại (tổng số gà, cảnh báo, nhiệt độ, độ ẩm)
- ✅ **Quản lý Chuồng** - Xem chi tiết từng chuồng gà
- ✅ **Điều khiển Thiết bị** - Bật/tắt quạt, đèn, camera, máy cho ăn
- ✅ **Cảnh báo Hệ Thống** - Thông báo khi có vấn đề
- ✅ **Danh sách Thiết bị** - Quản lý các thiết bị IoT
- ✅ **Responsive Design** - Hoạt động trên tất cả thiết bị

## 🎨 Thiết Kế

- **Phong cách**: Nông nghiệp Việt
- **Màu chủ đạo**: Xanh lá (#16a34a), Nâu đất (#654321), Vàng nắng (#fbbf24)
- **Font**: Hệ thống font (Apple System, Segoe UI)
- **Responsive**: Mobile-first design

## 📊 Cấu Trúc Dữ Liệu

### Farm Data
```javascript
{
  name: string,                    // Tên trang trại
  totalChickens: number,           // Tổng số gà
  activeAlertsCount: number,       // Số cảnh báo
  avgTemperature: number,          // Nhiệt độ trung bình
  avgHumidity: number,             // Độ ẩm trung bình
  coops: Coop[],                   // Danh sách chuồng
  alerts: Alert[],                 // Danh sách cảnh báo
  devicesList: Device[]            // Danh sách thiết bị
}
```

### Coop (Chuồng Gà)
```javascript
{
  id: string,
  name: string,
  chickens: number,
  temperature: number,
  humidity: number,
  foodLevel: number,
  waterLevel: number,
  status: 'normal' | 'warning' | 'error',
  devices: {
    fan: boolean,
    light: boolean,
    camera: boolean,
    feeder: boolean
  },
  stats: object,
  logs: Log[]
}
```

### Device (Thiết Bị)
```javascript
{
  id: string,
  name: string,
  type: 'Camera' | 'Sensor' | 'Feeder' | 'Fan',
  coop: string,
  status: 'online' | 'warning' | 'offline'
}
```

### Alert (Cảnh Báo)
```javascript
{
  id: number,
  coopName: string,
  message: string,
  time: string
}
```

## 🔧 Phát Triển Thêm

### Kết Nối API
```javascript
// Trong App.jsx
useEffect(() => {
  const fetchData = async () => {
    const response = await fetch('/api/farm-data');
    const data = await response.json();
    setFarmData(data);
  };
  fetchData();
}, []);
```

### Thêm Chuồng Gà Mới
```javascript
const addCoop = (newCoop) => {
  setFarmData(prev => ({
    ...prev,
    coops: [...prev.coops, newCoop]
  }));
};
```

### Cập Nhật Dữ Liệu Real-time
```javascript
useEffect(() => {
  const interval = setInterval(() => {
    // Fetch data từ server
    updateFarmData();
  }, 5000); // Update mỗi 5 giây
  
  return () => clearInterval(interval);
}, []);
```

## 📝 Thêm Dữ Liệu

Để thêm dữ liệu vào ứng dụng, bạn có thể:

1. **Từ API Server** - Kết nối endpoint và lấy dữ liệu
2. **Từ Database** - Tích hợp với MongoDB, PostgreSQL, etc.
3. **Từ IoT Devices** - Nhận dữ liệu từ cảm biến thực

Hiện tại ứng dụng để trống/0 cho tất cả chỉ số để bạn có thể dễ dàng tích hợp dữ liệu của riêng mình.

## 🛠️ Công Nghệ Sử Dụng

- **React 18** - UI Framework
- **Vite** - Build tool
- **CSS3** - Styling
- **JavaScript ES6+** - Programming language

## 📄 License

MIT

## 👨‍💻 Author

Built for Vietnamese farmers with ❤️
