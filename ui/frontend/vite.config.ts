import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // FastAPI backend — see ui/backend/main.py
      "/api": "http://localhost:8571",
    },
  },
});
