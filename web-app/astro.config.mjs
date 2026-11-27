import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://llm.godedi.net',
  output: 'static',
  integrations: [sitemap()],
  build: {
    format: 'directory'
  }
});
