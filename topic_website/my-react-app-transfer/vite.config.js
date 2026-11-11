import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // The standalone internal.html has no server-side employee authentication.
  server: { host: "127.0.0.1" },
  preview: { host: "127.0.0.1" },
  resolve: {
  dedupe: [
    "react",
    "react-dom",
    "react-router-dom",
  ],
},
})
