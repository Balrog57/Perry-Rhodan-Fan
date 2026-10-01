// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://balrog57.github.io',
  base: '/Perry-Rhodan-Fan',
  output: 'static',
  // The full chapter texts no longer fit in one content module. Smaller
  // chunks stay under the bundler limit that rejects very large strings.
  experimental: {
    collectionStorage: { type: 'chunked', chunkSize: 2 * 1024 * 1024 },
  },
  vite: {
    plugins: [tailwindcss()]
  }
});