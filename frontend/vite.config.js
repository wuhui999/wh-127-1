import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true
      }
    }
  },
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'axios',
      'element-plus',
      '@element-plus/icons-vue',
      'dayjs',
      'dayjs/locale/zh-cn',
      'dayjs/plugin/customParseFormat'
    ]
  }
})
