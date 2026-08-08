import * as cheerio from 'cheerio';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE = 'http://rhodan.stellarque.com/perryrhodan/vf.php?init=';
const OUT = join(__dirname, '..', 'src', 'content', 'chapters');

if (!existsSync(OUT)) mkdirSync(OUT, { recursive: true });

const ENTITIES = {
  '&eacute;': 'é', '&egrave;': 'è', '&ecirc;': 'ê', '&aelig;': 'æ',
  '&ccedil;': 'ç', '&agrave;': 'à', '&acirc;': 'â', '&icirc;': 'î',
  '&ocirc;': 'ô', '&ucirc;': 'û', '&euml;': 'ë', '&iuml;': 'ï',
  '&uuml;': 'ü', '&amp;': '&', '&deg;': '°', '&laquo;': '«',
  '&raquo;': '»', '&#039;': "'", '&quot;': '"', '&nbsp;': ' ',
  '&Eacute;': 'É', '&Egrave;': 'È', '&Ccedil;': 'Ç', '&Agrave;': 'À',
  '&Ecirc;': 'Ê', '&Acirc;': 'Â', '&Icirc;': 'Î', '&Ocirc;': 'Ô',
  '&Ucirc;': 'Û', '&Euml;': 'Ë', '&Iuml;': 'Ï', '&Uuml;': 'Ü',
  '&AElig;': 'Æ', '&lsquo;': '\u2018', '&rsquo;': '\u2019',
  '&ldquo;': '\u201C', '&rdquo;': '\u201D', '&ndash;': '\u2013',
  '&mdash;': '\u2014', '&hellip;': '\u2026', '&OElig;': 'Œ', '&oelig;': 'œ',
  '&ntilde;': 'ñ',
};

function decodeEnt(str) {
  let r = str;
  for (const [ent, ch] of Object.entries(ENTITIES)) {
    r = r.split(ent).join(ch);
  }
  r = r.replace(/&#(\d+);/g, (_, code) => String.fromCharCode(parseInt(code)));
  return r;
}

function escapeYaml(str) {
  return str.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

// Convert the synopsis <div align="justify"> HTML to Markdown while
// preserving line breaks (<br>), italics (<i>), and bold (<b>).
function convertSynopsisHtml(html) {
  const $ = cheerio.load(html, null, false);
  const root = $.root().get(0);
  let out = '';
  function walk(node) {
    (node.children || []).forEach((child) => {
      if (child.type === 'text') {
        out += child.data || '';
      } else if (child.type === 'tag') {
        const tag = (child.tagName || '').toLowerCase();
        if (tag === 'br') {
          out += '\n';
        } else if (tag === 'i' || tag === 'em') {
          out += '*';
          walk(child);
          out += '*';
        } else if (tag === 'b' || tag === 'strong') {
          out += '**';
          walk(child);
          out += '**';
        } else {
          walk(child);
        }
      }
    });
  }
  walk(root);
  return decodeEnt(out)
    .replace(/\u00a0/g, ' ')
    .replace(/[ \t]+/g, ' ')
    .replace(/ ?\n ?/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .split('\n')
    .map((l) => l.trim())
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function getField(central, $, label) {
  let out = '';
  central.find('b').each((_, el) => {
    if ($(el).text().trim() === label) {
      const clone = $(el).parent().clone();
      clone.find('b').remove();
      out = decodeEnt(clone.text()).replace(/\s+/g, ' ').trim();
    }
  });
  return out;
}

async function scrapeVolume(num) {
  const url = `${BASE}${num}`;
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const buffer = await res.arrayBuffer();
    const rawHtml = new TextDecoder('utf-8').decode(buffer);
    const $ = cheerio.load(rawHtml, { decodeEntities: false });
    const central = $('#central');
    if (!central.length) return null;

    const text = central.text();

    let bookNumber = num;
    const prMatch = text.match(/PERRY RHODAN n[°º]\s*(\d+)/i);
    if (prMatch) bookNumber = parseInt(prMatch[1]);

    const title = central.find('font[size="4"]').first().text().trim() || `Tome ${bookNumber}`;

    const cycleLink = central.find('a[href*="cycle.php"]').first();
    const cycleName = cycleLink.text().trim();
    const hrefMatch = (cycleLink.attr('href') || '').match(/init=(\d+)/);
    const cycleNumber = hrefMatch ? parseInt(hrefMatch[1]) : 1;

    const traduction = getField(central, $, 'Traduction');
    const edition = getField(central, $, 'Edition originale');
    const parution = getField(central, $, 'Parution');

    const justify = central.find('div[align="justify"]').first();
    const synopsis = justify.length ? convertSynopsisHtml(justify.html() || '') : '';

    return { bookNumber, title, cycleNumber, cycleName, traduction, edition, parution, synopsis };
  } catch (e) {
    console.error(`Error volume ${num}:`, e.message);
    return null;
  }
}

async function main() {
  let created = 0;
  for (let i = 1; i <= 379; i++) {
    const data = await scrapeVolume(i);
    if (!data) {
      console.log(`Skip ${i}`);
      continue;
    }

    const slug = `fr-${String(data.bookNumber).padStart(3, '0')}`;
    const synopsisBody = data.synopsis || 'Synopsis à compléter depuis la source.';
    const titleEsc = escapeYaml(data.title);

    const content = `---
title: "${titleEsc}"
cycleNumber: ${data.cycleNumber}
chapterNumber: ${data.bookNumber}
type: synopsis
cover: "/images/covers/${slug}.jpg"
cycle: "${escapeYaml(data.cycleName)}"
traduction: "${escapeYaml(data.traduction)}"
edition: "${escapeYaml(data.edition)}"
parution: "${escapeYaml(data.parution)}"
---

## ${data.title}

${synopsisBody}
`;
    writeFileSync(join(OUT, `${slug}.md`), content, 'utf-8');
    created++;
    if (i % 50 === 0) console.log(`${i}/379 (${created} created)`);
    await new Promise((r) => setTimeout(r, 150));
  }
  console.log(`Done! ${created} volumes.`);
}

main();
