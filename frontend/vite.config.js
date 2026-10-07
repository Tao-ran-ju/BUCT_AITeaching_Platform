import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 线上由 nginx 同源反代 /api、/uploads 到 FastAPI（127.0.0.1:8000）；
// 本地开发时用 dev server 的 proxy 达到同样效果。
export default defineConfig({
  plugins: [vue()],
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/uploads': { target: 'http://127.0.0.1:8000', changeOrigin: true }
    }
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1500
  }
})
