import * as cheerio from 'cheerio';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE = 'http://rhodan.stellarque.com/perryrhodan/vf.php?init=';
const OUT = join(__dirname, '..', 'src', 'content', 'chapters');

if (!existsSync(OUT)) mkdirSync(OUT, { recursive: true });

const CYCLE_MAP = {
  'La Troisième Force': 1,
  'Atlan et Arkonis': 2,
  'Les Bioposis': 3,
  'Le Deuxième Empire': 4,
  'Les Maîtres Insulaires': 5,
  'M 87': 6,
  'Les Cappins': 7,
  "L'Essaim": 8,
  'Les Vieux Mutants': 9,
  'Le Concile': 11,
  'Aphilie': 12,
  'Bardioc': 13,
  'Pan-thau-ra': 14,
  'Les Citadelles Cosmiques': 15,
  'La Hanse Cosmique': 16,
  "L'Armada Infinie": 17,
};

function getCycleNumber(cycleName) {
  const norm = cycleName.toLowerCase().replace(/[-–—\s]+/g, ' ');
  for (const [key, val] of Object.entries(CYCLE_MAP)) {
    const normKey = key.toLowerCase().replace(/[-–—\s]+/g, ' ');
    if (norm.includes(normKey)) return val;
  }
  return 1;
}

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
};

function decodeEnt(str) {
  let r = str;
  for (const [ent, ch] of Object.entries(ENTITIES)) {
    r = r.split(ent).join(ch);
  }
  r = r.replace(/&#(\d+);/g, (_, code) => String.fromCharCode(parseInt(code)));
  return r;
}

function cleanText(text) {
  return decodeEnt(text)
    .replace(/\r\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\(\s+/g, '(')
    .replace(/\s+\)/g, ')')
    .trim();
}

function escapeYaml(str) {
  return str.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, ' ').substring(0, 2000);
}

async function scrapeVolume(num) {
  const url = `${BASE}${num}`;
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const buffer = await res.arrayBuffer();
    const rawHtml = new TextDecoder('utf-8').decode(buffer);
    const html = decodeEnt(rawHtml);
    const $ = cheerio.load(html, { decodeEntities: false });

    const central = $('#central');
    if (!central.length) return null;

    const text = central.text();

    let bookNumber = num;
    let title = '';

    const prMatch = text.match(/PERRY RHODAN n[°º]\s*(\d+)/i);
    if (prMatch) bookNumber = parseInt(prMatch[1]);

    const bolds = [];
    central.find('b').each((_, el) => {
      const t = $(el).text().trim();
      if (t && !t.includes('BASIS') && !t.includes('PERRY RHODAN') && t.length > 1 && t.length < 100) {
        bolds.push(t);
      }
    });

    const skipWords = ['Cycle', 'Traduction', 'Edition originale', 'Parution', 'FASCICULES', 'AUTRES EDITIONS', 'PREMIÈRE PARTIE', 'DEUXIÈME PARTIE', 'PREMIERE PARTIE', 'DEUXIEME PARTIE'];
    for (const b of bolds) {
      if (!skipWords.some(sw => b.includes(sw)) && !b.match(/^\d+$/) && b.length > 2) {
        title = b;
        break;
      }
    }

    if (!title) title = `Tome ${bookNumber}`;

    const cycleLink = central.find('a[href*="cycle.php"]').first();
    const cycleName = cycleLink.text().trim();
    const cycleNumber = getCycleNumber(cycleName);

    const coverImg = central.find('img[src*="covers/pr_vf"]').first().attr('src');
    let cover = '';
    if (coverImg) {
      cover = coverImg.replace(/\.\.\//g, '');
      cover = `http://rhodan.stellarque.com/${cover}`;
    }

    let synopsis = '';
    const fullText = cleanText(text);
    const allPartsMatch = fullText.match(/((?:PREMI[ÈE]RE|DEUXI[ÈE]ME|TROISI[ÈE]ME)\s+PARTIE[\s\S]*?)(?:FASCICULES\s+ORIGINAUX|AUTRES\s+EDITIONS|©)/i);
    if (allPartsMatch) {
      synopsis = cleanText(allPartsMatch[1]).substring(0, 2000);
    } else {
      const afterParution = fullText.match(/Parution\s+(?:[a-zA-Zéèêàâûô]+\s+)?\d{4}\s*([\s\S]*)$/i);
      if (afterParution) {
        synopsis = cleanText(afterParution[1])
          .split(/\b(?:FASCICULES\s+ORIGINAUX|AUTRES\s+EDITIONS|©)\b/i)[0]
          .replace(/\s*SOURCE\s*$/i, '')
          .substring(0, 2000);
      }
    }

    return { bookNumber, title, cycleNumber, cycleName, cover, synopsis };
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
    const synopsisEsc = escapeYaml(data.synopsis || 'Synopsis à compléter.');
    const synopsisBody = data.synopsis || 'Synopsis à compléter depuis la source.';
    const titleEsc = data.title.replace(/\\/g, '\\\\').replace(/"/g, '\\"');

    const content = `---
title: "${titleEsc}"
cycleNumber: ${data.cycleNumber}
chapterNumber: ${data.bookNumber}
type: synopsis
synopsis: "${synopsisEsc}"
${data.cover ? `cover: "${data.cover}"` : ''}
---

## ${data.title}

${synopsisBody}
`;
    writeFileSync(join(OUT, `${slug}.md`), content, 'utf-8');
    created++;
    if (i % 50 === 0) console.log(`${i}/379 (${created} created)`);
    await new Promise(r => setTimeout(r, 250));
  }
  console.log(`Done! ${created} volumes.`);
}

main();
