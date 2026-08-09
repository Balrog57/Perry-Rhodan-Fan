import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, rmSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';
import * as cheerio from 'cheerio';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const CHAP = join(ROOT, 'src', 'content', 'chapitres');
const TMP = join(__dirname, '..', '.coverprobe');
if (existsSync(TMP)) rmSync(TMP, { recursive: true, force: true });
mkdirSync(TMP, { recursive: true });

const SEARCH = (n) => `https://perry-rhodan.net/shop/search?search=${n}`;

const CDN = 'https://cdn.perry-rhodan.net';

function fullVariants(u) {
  const stripped = u.replace(/\/thumbnails\//g, '/');
  const out = [];
  let cur = stripped;
  for (let i = 0; i < 2 && cur; i++) {
    out.push(cur);
    const next = cur.includes('/bildzentrale/')
      ? cur.replace('/bildzentrale/', '/bildzentrale_original/')
      : null;
    if (!next || out.includes(next)) next = null;
    cur = next;
  }
  if (stripped.includes('/S999000/')) out.push(stripped.replace('/S999000/', '/999000/'));
  return [...new Set(out)];
}

function getDims(file) {
  try {
    const out = execFileSync('python', [
      '-c', 'from PIL import Image; import sys; im=Image.open(sys.argv[1]); print(im.size[0], im.size[1])', file,
    ]).toString().trim();
    const [w, h] = out.split(/\s+/).map(Number);
    return [w, h];
  } catch {
    return null;
  }
}

function localInfo(issue) {
  const stem = `de-${String(issue).padStart(4, '0')}`;
  for (const ext of ['webp', 'jpg', 'jpeg', 'png']) {
    const p = join(ROOT, 'public', 'images', 'covers', `${stem}.${ext}`);
    if (existsSync(p)) return { path: p, dims: getDims(p), ext };
  }
  return null;
}

const area = (d) => (d ? d[0] * d[1] : 0);

async function headLen(url) {
  try {
    const res = await fetch(url, { method: 'HEAD', headers: { 'user-agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(20000) });
    return res.ok ? parseInt(res.headers.get('content-length') || '0', 10) || 0 : 0;
  } catch {
    return 0;
  }
}

async function download(url, dest) {
  try {
    const res = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(60000) });
    if (!res.ok) return false;
    writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
    return true;
  } catch {
    return false;
  }
}

async function searchCandidates(issue) {
  try {
    const res = await fetch(SEARCH(issue), { headers: { 'user-agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(40000) });
    if (!res.ok) return [];
    const html = await res.text();
    const $ = cheerio.load(html);
    const urls = new Set();
    // only images whose alt explicitly names this exact issue
$('img[alt]').each((_i, el) => {
      const alt = ($(el).attr('alt') || '').trim();
      const m = alt.match(/^Perry Rhodan\s+(\d{3,4})\s*:/i);
      if (!m) return;
      if (parseInt(m[1], 10) !== issue) return;
      const src = $(el).attr('data-src') || $(el).attr('src') || '';
      if (!src || src.includes('placeholder')) return;
      const abs = src.startsWith('http') ? src : new URL(src, SEARCH(issue)).href;
      for (const v of fullVariants(abs)) urls.add(v);
    });
    return [...urls];
  } catch {
    return [];
  }
}

async function bestCandidate(issue, candidates) {
  const ranked = [];
  for (const u of candidates) {
    const len = await headLen(u);
    if (len > 0) ranked.push({ url: u, len });
  }
  ranked.sort((a, b) => b.len - a.len);
  const top = ranked.slice(0, 6);
  let best = null;
  let i = 0;
  for (const c of top) {
    const dest = join(TMP, `p-${issue}-${i++}.img`);
    if (!(await download(c.url, dest))) continue;
    const dims = getDims(dest);
    if (dims && (!best || area(dims) > area(best.dims))) best = { url: c.url, dims, len: c.len };
  }
  return best;
}

// direct CDN probe patterns (deterministic for recent + milestone issues)
function directCandidates(issue) {
  const n4 = String(issue).padStart(4, '0');
  const pats = [
    `${CDN}/999000/PR_I_${n4}_Cover_komplett_Web.jpg`,
    `${CDN}/S999000/PR_I_${n4}_Cover_komplett_Web.jpg`,
    `${CDN}/999000/PR_I_${n4}_Cover_EPUB.jpg`,
    `${CDN}/S999000/PR_I_${n4}_Cover_EPUB.jpg`,
    `${CDN}/S999000/PR${n4}.jpg`,
    `${CDN}/S999000/PR${n4}cover.jpg`,
    `${CDN}/S999000/PR_${n4}.jpg`,
    `${CDN}/S999000/PR_${n4}_cover.jpg`,
    `${CDN}/S999000/PR${issue}.jpg`,
    `${CDN}/S999000/${n4}cover.jpg`,
  ];
  return [...new Set(pats)];
}

const issues = [];
for (const f of readdirSync(CHAP)) {
  if (!/^de-\d{4}\.md$/.test(f)) continue;
  const txt = readFileSync(join(CHAP, f), 'utf8');
  const m = txt.match(/^cover: "([^"]+)"$/m);
  if (!m) continue;
  const issue = parseInt(f.slice(3, 7), 10);
  issues.push({ issue, coverRef: m[1] });
}
console.log(`issues with cover: ${issues.length}`);

const plan = [];
let done = 0;
const CONC = 10;

async function worker(idx) {
  for (let k = idx; k < issues.length; k += CONC) {
    const it = issues[k];
    const local = localInfo(it.issue);
    let best = null;
    const direct = directCandidates(it.issue);
    const directHits = [];
    for (const u of direct) {
      const len = await headLen(u);
      if (len > 0) directHits.push({ url: u, len });
    }
    if (directHits.length > 0) {
      best = await bestCandidate(it.issue, directHits.map((h) => h.url));
    } else {
      const cands = await searchCandidates(it.issue);
      if (cands.length) best = await bestCandidate(it.issue, cands);
    }
    plan.push({
      issue: it.issue,
      local: local ? local.dims : null,
      best: best ? { url: best.url, dims: best.dims, len: best.len } : null,
    });
    done++;
    if (done % 100 === 0) console.log(`  ${done}/${issues.length}`);
  }
}
await Promise.all(Array.from({ length: CONC }, (_, i) => worker(i)));

writeFileSync(join(__dirname, '_coverplan.json'), JSON.stringify(plan, null, 1));
const better = plan.filter(
  (p) => p.best && area(p.best.dims) > area(p.local) * 1.05,
);
console.log(`probed ${plan.length}; better: ${better.length}`);
for (const b of better.slice(0, 40)) {
  console.log(`  ${b.issue} local=${b.local ? b.local.join('x') : '?'} best=${b.best.dims.join('x')} ${b.best.url}`);
}