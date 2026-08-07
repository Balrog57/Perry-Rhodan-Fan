// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://balrog57.github.io',
  base: '/Perry-Rhodan-Fan',
  output: 'static',
  vite: {
    plugins: [tailwindcss()]
  }
});