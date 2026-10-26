import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'


// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    proxy: {
      // mọi request tới /api/* sẽ bị vite chuyển tiếp sang backend
      // Port 8020: 8000 đang bị project My-Workspace chiếm (server.py) — xem Project-Plan.md mục 7
      '/api': {
        target:  'http://localhost:8020',  // địa chỉ backend (uvicorn)
         changeOrigin: true,               // giả lập request từ chính domain backend
      },
      // ảnh camera lưu local (fallback MinIO) — cùng backend với /api
      '/storage': {
        target: 'http://localhost:8020',
        changeOrigin: true,
      }
    }
  }
})


 
