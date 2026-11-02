import { defineConfig } from "vite"
import { gui } from "@opencode/plugin/gui/vite"

// Builds src/gui.tsx into dist/gui-experimental.cjs, the one CommonJS file Desktop loads.
export default defineConfig({ plugins: [gui()] })
