import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

const SITE = 'https://balrog57.github.io';
const BASE = '/Perry-Rhodan-Fan';

export const GET: APIRoute = async () => {
  const tomes = await getCollection('tomes');
  const cycles = await getCollection('cycles');
  const chapitres = await getCollection('chapitres');

  const urls = [
    { loc: `${SITE}${BASE}/`, priority: '1.0' },
    { loc: `${SITE}${BASE}/tomes`, priority: '0.9' },
    { loc: `${SITE}${BASE}/cycles`, priority: '0.9' },
    { loc: `${SITE}${BASE}/suite`, priority: '0.9' },
    { loc: `${SITE}${BASE}/traduire`, priority: '0.7' },
    ...cycles.map((c) => ({ loc: `${SITE}${BASE}/cycles/${c.data.cycleNumber}`, priority: '0.8' })),
    ...tomes.map((t) => ({ loc: `${SITE}${BASE}/tomes/${t.id}`, priority: '0.7' })),
    ...chapitres.map((ch) => ({ loc: `${SITE}${BASE}/chapter/chapitres/${ch.id}`, priority: '0.6' })),
  ];

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${urls
    .map(
      (u) => `  <url>
    <loc>${u.loc}</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>${u.priority}</priority>
  </url>`,
    )
    .join('\n')}
</urlset>`;

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml' },
  });
};