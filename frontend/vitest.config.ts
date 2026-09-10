import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  // No @vitejs/plugin-react: it pulls in Babel, which collides with the
  // codegen plugin's transitive relay-compiler. esbuild handles the JSX, and
  // Fast Refresh is meaningless in a test run.
  esbuild: { jsx: "automatic" },
  resolve: {
    alias: { "~": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
    passWithNoTests: true,
  },
});
