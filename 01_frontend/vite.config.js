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
      '/api': {
        target:  'http://localhost:8000',  // địa chỉ backend (uvicorn)
         changeOrigin: true,               // giả lập request từ chính domain backend
      }
    }
  }
})


 
