# 📂 Cấu Trúc Thư Mục Dự Án

## Hướng Dẫn Tổ Chức Files

```
trang-trai-ga-app/
│
├── public/                    # Static files (optional)
│   └── favicon.ico
│
├── src/                       # Source code
│   ├── components/            # React components (optional)
│   │   ├── Header.jsx
│   │   ├── Dashboard.jsx
│   │   ├── CoopsList.jsx
│   │   ├── CoopDetail.jsx
│   │   ├── DevicesList.jsx
│   │   └── AlertsModal.jsx
│   │
│   ├── styles/                # CSS files
│   │   ├── index.css          # Global styles
│   │   └── app.css            # App component styles
│   │
│   ├── App.jsx                # Main App component
│   ├── main.jsx               # React entry point
│   └── constants.js           # Constants & config (optional)
│
├── index.html                 # HTML template
├── package.json               # NPM dependencies
├── vite.config.js             # Vite configuration
├── .gitignore                 # Git ignore rules
├── README.md                  # Documentation
├── STRUCTURE.md               # This file
└── CONTRIBUTING.md            # Contribution guidelines

```

## 📝 Chi Tiết Từng File

### `index.html`
- HTML entry point
- Định nghĩa root element cho React
- Link đến main.jsx

### `src/main.jsx`
- Render React app vào DOM
- Import global styles
- Import App component

### `src/App.jsx`
- Component chính của ứng dụng
- Quản lý state toàn ứng dụng
- Định tuyến giữa các tabs
- Chứa tất cả sub-components

### `src/app.css`
- Styles cho tất cả components
- Layout, cards, modals, navigation
- Colors, animations, responsive design

### `src/index.css`
- Global reset styles
- Font definitions
- CSS animations
- Common utilities

### `package.json`
- NPM dependencies
- Scripts (dev, build, preview)
- Project metadata

### `vite.config.js`
- Vite configuration
- Development server settings
- Build options

## 🔄 Tổ Chức Code Tốt Hơn (Tuỳ chọn)

Nếu dự án phát triển lớn, bạn có thể tách files như sau:

```
src/
├── components/
│   ├── Header/
│   │   ├── Header.jsx
│   │   └── Header.css
│   ├── Dashboard/
│   │   ├── Dashboard.jsx
│   │   └── Dashboard.css
│   ├── CoopDetail/
│   │   ├── CoopDetail.jsx
│   │   └── CoopDetail.css
│   └── Common/
│       ├── Modal.jsx
│       ├── Card.jsx
│       └── Toast.jsx
│
├── hooks/
│   ├── useFarmData.js
│   └── useLocalStorage.js
│
├── utils/
│   ├── api.js
│   └── helpers.js
│
├── context/
│   └── FarmContext.js
│
├── App.jsx
├── main.jsx
├── index.css
└── app.css
```

## 🎯 Quy Ước Đặt Tên

### Components
- PascalCase: `Header.jsx`, `CoopsList.jsx`, `AlertsModal.jsx`
- 1 component per file
- CSS cùng tên: `Header.jsx` → `Header.css`

### Variables & Functions
- camelCase: `handleToggleDevice`, `showToast`, `farmData`
- Descriptive names
- Avoid abbreviations

### Classes & Constants
- UPPERCASE: `FARM_STATUS_NORMAL`, `MAX_COOPS`
- Constants in separate file (optional)

### CSS Classes
- lowercase with hyphens: `.device-card`, `.coop-header`, `.btn-primary`
- BEM naming (optional): `.card__header`, `.card__title`

## 🔐 State Management

Hiện tại sử dụng React Hooks:
- `useState` - Local state
- `useEffect` - Side effects
- `useCallback` - Memoized functions

Nếu cần advanced state management:
- **Context API** - Props drilling solution
- **Redux** - Large scale apps
- **Zustand** - Lightweight alternative

## 📦 Dependencies

### Hiện tại
- react (^18.2.0)
- react-dom (^18.2.0)

### Có thể thêm
- axios - HTTP client
- React Query - Data fetching
- React Router - Routing
- Chart.js - Data visualization
- date-fns - Date utilities
- Form validation - Yup, Zod

## 🚀 Deployment

### Static Hosting (Recommended)
- Vercel
- Netlify
- GitHub Pages

### Steps
```bash
npm run build
# Upload 'dist' folder to hosting
```

### Server Hosting
- AWS EC2
- DigitalOcean
- Heroku
- Railway

## 📚 Tài Liệu Liên Quan

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [MDN Web Docs](https://developer.mozilla.org)

## 💡 Best Practices

1. **Keep components small** - Một component làm một việc
2. **Use meaningful names** - Tên rõ ràng, dễ hiểu
3. **Avoid nested ternary** - Dùng early returns
4. **Comment complex logic** - Viết comments cho code phức tạp
5. **Test components** - Viết tests cho logic quan trọng
6. **Optimize re-renders** - Dùng React.memo, useMemo khi cần

---

Chúc bạn code vui vẻ! 🎉
