import { defineConfig } from 'vite';
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import viteReact from '@vitejs/plugin-react';
import { nitro } from 'nitro/vite';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';


export default defineConfig({
  plugins: [tailwindcss(), tanstackStart(), viteReact(), nitro()],
  // Add this block if it's missing:
  environments: {
    ssr: {
      build: {
        rollupOptions: {
          input: "./src/server.ts" 
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});