import * as cheerio from 'cheerio';

const num = Number(process.argv[2] || 379);
const res = await fetch(`http://rhodan.stellarque.com/perryrhodan/vf.php?init=${num}`);
const buf = Buffer.from(await res.arrayBuffer());
const html = new TextDecoder('utf-8').decode(buf);
const $ = cheerio.load(html);
const central = $('#central');
console.log('central found:', central.length > 0);
const text = central.text();
console.log('--- RAW TEXT (first 1800) ---');
console.log(text.replace(/\s+/g, ' ').substring(0, 1800));
console.log('--- has PARTIE markers ---');
console.log('PREMIÈRE:', /PREMIÈRE PARTIE/i.test(text), 'DEUXIÈME:', /DEUXIÈME PARTIE/i.test(text));
console.log('--- has FASCICULES ---');
console.log('FASCICULES:', /FASCICULES/i.test(text));
console.log('--- b tags ---');
central.find('b').each((_, el) => {
  const t = $(el).text().trim();
  if (t.length > 1 && t.length < 100) console.log('B:', JSON.stringify(t));
});
