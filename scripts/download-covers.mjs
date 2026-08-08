import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CHAPTERS = join(__dirname, '..', 'src', 'content', 'chapters');
const COVERS = join(__dirname, '..', 'public', 'images', 'covers');

if (!existsSync(COVERS)) mkdirSync(COVERS, { recursive: true });

const files = readFileSync(join(CHAPTERS, '_index.txt'), 'utf-8').trim().split('\n').filter(Boolean);

async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  writeFileSync(dest, buf);
}

let ok = 0, fail = 0;
const tasks = files.map(async (raw) => {
  const file = raw.trim();
  const content = readFileSync(join(CHAPTERS, file), 'utf-8');
  const coverMatch = content.match(/^cover: "(.+)"$/m);
  if (!coverMatch) return;
  const url = coverMatch[1];
  const dest = join(COVERS, file.replace('.md', '.jpg'));
  try {
    await download(url, dest);
    ok++;
    console.log(`OK ${file}`);
  } catch (e) {
    fail++;
    console.log(`FAIL ${file} (${e.message})`);
  }
});

await Promise.all(tasks);
console.log(`Done! ${ok} downloaded, ${fail} failed.`);
