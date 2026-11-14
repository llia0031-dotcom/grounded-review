import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { resolve } from 'node:path'

// A static site: the data is the stored evaluation output in src/data, so there is no server and no API key.
// Four pages: the demo and its about page in Chinese (index.html, about.html) and in English (en.html, about-en.html).
export default defineConfig({
  base: process.env.VITE_BASE ?? './',
  plugins: [react()],
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1500,
    rollupOptions: { input: { main: resolve(__dirname, 'index.html'), about: resolve(__dirname, 'about.html'), en: resolve(__dirname, 'en.html'), aboutEn: resolve(__dirname, 'about-en.html') } },
  },
})
