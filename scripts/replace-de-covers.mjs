import { readFileSync, writeFileSync, existsSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const COVERS = join(ROOT, 'public', 'images', 'covers');
const TMP = join(__dirname, '..', '.coverprobe');

const plan = JSON.parse(readFileSync(join(__dirname, '_coverplan.json'), 'utf8'));
const area = (d) => (d ? d[0] * d[1] : 0);

const toReplace = plan.filter(
  (p) => p.best && p.local && area(p.best.dims) > area(p.local) * 1.05,
);
console.log(`replacing ${toReplace.length} covers`);

const CONC = 8;
let done = 0;
let failures = 0;
const results = [];

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

function convertToWebp(src, dest) {
  try {
    execFileSync('python', [
      '-c',
      'from PIL import Image; import sys; im=Image.open(sys.argv[1]).convert("RGB"); im.save(sys.argv[2], "WEBP", quality=90, method=4)',
      src, dest,
    ], { stdio: 'ignore' });
    return existsSync(dest) && statSync(dest).size > 0;
  } catch {
    return false;
  }
}

async function workerRun(i) {
  for (let k = i; k < toReplace.length; k += CONC) {
    const p = toReplace[k];
    const outName = `de-${String(p.issue).padStart(4, '0')}.webp`;
    const destPath = join(COVERS, outName);
    const srcTmp = join(TMP, `dl-${p.issue}.img`);
    let ok = false;
    if (await download(p.best.url, srcTmp)) {
      ok = convertToWebp(srcTmp, destPath);
    }
    if (!ok) failures++;
    results.push({ issue: p.issue, ok, from: p.best.url, dims: p.best.dims });
    done++;
    if (done % 20 === 0) console.log(`  ${done}/${toReplace.length} (failures: ${failures})`);
  }
}

await Promise.all(Array.from({ length: CONC }, (_, i) => workerRun(i)));
writeFileSync(join(__dirname, '_replaced.json'), JSON.stringify(results, null, 1));
console.log(`DONE: ${results.filter((r) => r.ok).length} replaced, ${failures} failures`);