import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const COVERS = join(ROOT, 'public', 'images', 'covers');

// only issues that were replaced (git diff on webp would list them; snapshot here = all de-* whose
// size was upgraded). We instead rely on _replaced.json from the last run plus wave-1 list captured
// in _coverplan.json 'better' entries.
const plan = JSON.parse(readFileSync(join(__dirname, '_coverplan.json'), 'utf8'));
const best = (d) => (d ? d[0] * d[1] : 0);
const better = plan.filter((p) => p.best && p.local && best(p.best.dims) > best(p.local) * 1.05);
let issues = better.map((p) => p.issue);
// also include any file modified on disk per git status
try {
  const git = execFileSync('git', ['status', '--porcelain', '--', 'public/images/covers'], { encoding: 'utf8' });
  for (const line of git.split('\n')) {
    const m = line.match(/de-(\d{4})\.webp/);
    if (m) issues.push(parseInt(m[1], 10));
  }
} catch {}
issues = [...new Set(issues)];
console.log(`verifying ${issues.length} replaced files`);

function sim(a, b) {
  try {
    const out = execFileSync('python', [
      '-c',
      'from PIL import Image; import sys; a=Image.open(sys.argv[1]).convert("L").resize((64,92)); b=Image.open(sys.argv[2]).convert("L").resize((64,92)); pa=list(a.getdata()); pb=list(b.getdata()); ma=sum(pa)/len(pa); mb=sum(pb)/len(pb); num=sum((x-ma)*(y-mb) for x,y in zip(pa,pb)); den=(sum((x-ma)**2 for x in pa)**0.5)*(sum((y-mb)**2 for y in pb)**0.5); print(num/den if den else 0)',
      a, b,
    ], { encoding: 'utf8' });
    return parseFloat(out.trim());
  } catch {
    return null;
  }
}

async function refThumb(issue) {
  try {
    const res = await fetch(`https://perry-rhodan.net/shop/search?search=${issue}`, { headers: { 'user-agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(40000) });
    if (!res.ok) return null;
    const html = await res.text();
    const re = /<img[^>]*alt="([^"]*)"[^>]*\bsrc="([^"]+)"[^>]*>/g;
    let m; const out = [];
    while ((m = re.exec(html))) {
      const alt = (m[1] || '').trim();
      const num = alt.match(/^Perry-Rhodan\s+(\d{3,4})\s*:/i) || alt.match(/^Perry Rhodan\s{1,}(\d{3,4})\s*:/i);
      if (num && parseInt(num[1], 10) === issue) {
        out.push({ alt, src: m[2].replace(/&amp;/g, '&') });
      }
    }
    // prefer CDN heft image, else first
    const cdn = out.find((o) => o.src.includes('cdn.perry-rhodan.net') && o.src.includes('cover'));
    const any = out[0];
    return cdn ? cdn.src : any ? any.src.replace(/\/bildzentrale\//, '/bildzentrale_original/') : null;
  } catch {
    return null;
  }
}

const TMPV = join(__dirname, '..', '.verify');
try { execSync(`if exist "${TMPV}" rmdir /s /q "${TMPV}"`); } catch {}
import { mkdirSync } from 'fs';
mkdirSync(TMPV, { recursive: true });

const results = [];
const CONC = 8;
const seen = new Set();
let processed = 0;

async function worker(i) {
  for (let k = i; k < issues.length; k += CONC) {
    const issue = issues[k];
    if (seen.has(issue)) continue;
    seen.add(issue);
    const local = join(COVERS, `de-${String(issue).padStart(4, '0')}.webp`);
    const ref = await refThumb(issue);
    let s = null;
    if (ref) {
      const rf = join(TMPV, `r-${issue}`);
      try {
        const res = await fetch(ref, { headers: { 'user-agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(60000) });
        if (res.ok) {
          writeFileSync(rf, Buffer.from(await res.arrayBuffer()));
          s = sim(local, rf);
        }
      } catch {}
    }
    results.push({ issue, sim: s, ref });
    processed++;
    if (processed % 20 === 0) console.log(`  ${processed}/${issues.length}`);
  }
}
await Promise.all(Array.from({ length: CONC }, (_, i) => worker(i)));
writeFileSync(join(__dirname, '_verify.json'), JSON.stringify(results, null, 1));
const flags = results.filter((r) => r.sim !== null && r.sim < 0.55);
console.log(`done; low-similarity: ${flags.length}`);
for (const f of flags.slice(0, 20)) console.log('  FLAG', f.issue, f.sim, f.ref);