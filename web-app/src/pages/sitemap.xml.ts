import type { APIRoute } from 'astro';
import catalog from '../data/llm_catalog.json';

export const GET: APIRoute = () => {
  const base = 'https://llm.godedi.net';
  const today = new Date().toISOString().split('T')[0];
  const staticUrls = ['/', '/methodology/'];
  const urls = [
    ...staticUrls.map((p) => `<url><loc>${base}${p}</loc><lastmod>${today}</lastmod><priority>1.0</priority></url>`),
    ...catalog.map((e) => `<url><loc>${base}/${e.slug}/</loc><lastmod>${today}</lastmod><priority>0.8</priority></url>`)
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.join('\n')}\n</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};