import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // Source maps ship with the tracked bundle (M15b): a stack trace from the
  // ACFC browser console names the component and line, not "Rv at :130".
  build: { sourcemap: true },
  server: {
    port: 5173,
    proxy: {
      // FastAPI backend — see ui/backend/main.py
      "/api": "http://localhost:8571",
    },
  },
});
