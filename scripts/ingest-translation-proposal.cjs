/**
 * Ingests a chunked translation proposal and opens a pending PR.
 * The untrusted payload can only become the body of one existing chapter file.
 * No shell, no checkout-based git push, no writes to main or .github.
 */
const SLUG_RE = /^de-\d{4}$/;
const PROPOSAL_RE = /^[a-f0-9-]{36}$/;
const BRANCH_RE = /^traduction\/de-\d{4}-[a-f0-9]{8}$/;
const CHAPTER_PATH_RE = /^src\/content\/chapitres\/de-\d{4}\.md$/;
const INBOX_PATH_RE = /^inbox\/[a-f0-9-]{36}\/(?:\d+\.txt|_lock)$/;
const CONTRIBUTOR_RE = /^[A-Za-zÀ-ÿ0-9 .'\-]{1,80}$/;
const MODES = new Set(['traduire', 'deja-traduit']);
const INBOX_BRANCH = 'translation-inbox';
const FORBIDDEN_BRANCHES = new Set(['main', 'master', 'gh-pages']);
const MAX_CHUNK_CHARS = 50000;
const MAX_BODY_CHARS = 600000;
const MAX_OPEN_TRANSLATION_PRS = 20;
const FINALIZE_ATTEMPTS = 40;
const FINALIZE_DELAY_MS = 5000;
const FRONTMATTER_KEYS = new Set(['statut', 'titleFr', 'traducteur']);

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function yamlQuote(value) {
  return JSON.stringify(String(value).replace(/[\u0000-\u001F\u007F]/g, ' ').trim());
}

function upsertFrontmatter(yaml, key, value) {
  if (!FRONTMATTER_KEYS.has(key)) {
    throw new Error('Clé frontmatter non autorisée.');
  }
  const re = new RegExp(`^${key}:.*$`, 'm');
  const line = `${key}: ${value}`;
  if (re.test(yaml)) return yaml.replace(re, line);
  return `${yaml.trimEnd()}\n${line}`;
}

function sanitizeLine(value, max) {
  return String(value || '')
    .replace(/\$\{\{[\s\S]*?\}\}/g, '')
    .replace(/[\u0000-\u001F\u007F\u202A-\u202E\u2066-\u2069]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}

function sanitizeBody(text) {
  return String(text)
    .replace(/\u0000/g, '')
    .replace(/[\u202A-\u202E\u2066-\u2069]/g, '')
    .replace(/\$\{\{[\s\S]*?\}\}/g, '')
    .replace(/<%[\s\S]*?%>/g, '')
    .replace(/<\/?[a-zA-Z][^>]*>/g, '')
    .replace(/\son[a-z]+\s*=/gi, ' ')
    .replace(/javascript\s*:/gi, '')
    .replace(/data\s*:\s*text\/html/gi, '')
    .replace(/\[[^\]]*\]\(\s*(?:javascript:|data:text\/html)[^)]*\)/gi, '');
}

function applyProposal(existing, { titleFr, contributor, body }) {
  const match = existing.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!match) {
    throw new Error('Fichier chapitre sans frontmatter YAML.');
  }

  let frontmatter = match[1];
  frontmatter = upsertFrontmatter(frontmatter, 'statut', 'traduit');
  if (titleFr) {
    frontmatter = upsertFrontmatter(frontmatter, 'titleFr', yamlQuote(titleFr));
  }
  if (contributor) {
    frontmatter = upsertFrontmatter(frontmatter, 'traducteur', yamlQuote(contributor));
  }

  return `---\n${frontmatter.trimEnd()}\n---\n\n${sanitizeBody(body).trim()}\n`;
}

function decodeContent(data) {
  if (!data || data.type !== 'file' || !data.content) return '';
  return Buffer.from(data.content.replace(/\n/g, ''), 'base64').toString('utf8');
}

function assertSafeWrite(path, branch) {
  if (FORBIDDEN_BRANCHES.has(branch) || branch.startsWith('refs/')) {
    throw new Error('Branche interdite.');
  }
  if (path.includes('..') || path.startsWith('/') || path.includes('\\')) {
    throw new Error('Chemin interdit.');
  }
  if (path.startsWith('.github/') || path.includes('.github/')) {
    throw new Error('Les workflows GitHub ne sont pas modifiables.');
  }

  const inboxOk = branch === INBOX_BRANCH && INBOX_PATH_RE.test(path);
  const chapterOk = BRANCH_RE.test(branch) && CHAPTER_PATH_RE.test(path);
  if (!inboxOk && !chapterOk) {
    throw new Error('Seul un fichier de chapitre (ou un fragment inbox) peut être écrit.');
  }
}

async function ensureBranch(github, owner, repo, branch, from = 'main') {
  if (from !== 'main') throw new Error('Base de branche interdite.');
  if (FORBIDDEN_BRANCHES.has(branch)) throw new Error('Branche interdite.');
  if (branch !== INBOX_BRANCH && !BRANCH_RE.test(branch)) {
    throw new Error('Nom de branche non autorisé.');
  }

  try {
    await github.rest.git.getRef({ owner, repo, ref: `heads/${branch}` });
    return;
  } catch (error) {
    if (error.status !== 404) throw error;
  }

  const { data: base } = await github.rest.git.getRef({
    owner,
    repo,
    ref: 'heads/main',
  });
  try {
    await github.rest.git.createRef({
      owner,
      repo,
      ref: `refs/heads/${branch}`,
      sha: base.object.sha,
    });
  } catch (error) {
    if (error.status !== 422) throw error;
  }
}

async function putFile(github, { owner, repo, path, content, branch, message, sha }) {
  assertSafeWrite(path, branch);
  const params = {
    owner,
    repo,
    path,
    message: sanitizeLine(message, 120),
    content: Buffer.from(content, 'utf8').toString('base64'),
    branch,
  };
  if (sha) params.sha = sha;
  return github.rest.repos.createOrUpdateFileContents(params);
}

async function getFile(github, { owner, repo, path, ref }) {
  try {
    const { data } = await github.rest.repos.getContent({ owner, repo, path, ref });
    return data;
  } catch (error) {
    if (error.status === 404) return null;
    throw error;
  }
}

async function tooManyOpenPrs(github, owner, repo) {
  const { data: prs } = await github.rest.pulls.list({
    owner,
    repo,
    state: 'open',
    per_page: 50,
  });
  return prs.filter((pr) => pr.head && pr.head.ref && BRANCH_RE.test(pr.head.ref)).length >= MAX_OPEN_TRANSLATION_PRS;
}

async function writeChunk(github, { owner, repo, proposalId, chunkIndex, chunk }) {
  await ensureBranch(github, owner, repo, INBOX_BRANCH);
  const path = `inbox/${proposalId}/${chunkIndex}.txt`;
  const existing = await getFile(github, { owner, repo, path, ref: INBOX_BRANCH });
  await putFile(github, {
    owner,
    repo,
    path,
    content: chunk,
    branch: INBOX_BRANCH,
    message: `inbox chunk ${chunkIndex}`,
    sha: existing && existing.sha,
  });
}

async function readChunks(github, { owner, repo, proposalId, chunkTotal }) {
  const parts = [];
  for (let index = 0; index < chunkTotal; index += 1) {
    const file = await getFile(github, {
      owner,
      repo,
      path: `inbox/${proposalId}/${index}.txt`,
      ref: INBOX_BRANCH,
    });
    if (!file) return null;
    parts.push(decodeContent(file));
  }
  return parts.join('');
}

async function tryLock(github, { owner, repo, proposalId }) {
  try {
    await putFile(github, {
      owner,
      repo,
      path: `inbox/${proposalId}/_lock`,
      content: new Date().toISOString(),
      branch: INBOX_BRANCH,
      message: 'inbox lock',
    });
    return true;
  } catch (error) {
    if (error.status === 422 || error.status === 409) return false;
    throw error;
  }
}

async function createTranslationPr(github, core, {
  owner,
  repo,
  slug,
  titleFr,
  contributor,
  mode,
  proposalId,
  body,
}) {
  const safeBody = sanitizeBody(body).trim();
  if (safeBody.length < 200) throw new Error('Traduction trop courte.');
  if (safeBody.length > MAX_BODY_CHARS) throw new Error('Traduction trop longue.');
  if (await tooManyOpenPrs(github, owner, repo)) {
    throw new Error('Trop de propositions en attente. Réessayez plus tard.');
  }

  const chapterPath = `src/content/chapitres/${slug}.md`;
  if (!CHAPTER_PATH_RE.test(chapterPath)) throw new Error('Chemin de chapitre invalide.');

  const existing = await getFile(github, { owner, repo, path: chapterPath, ref: 'main' });
  if (!existing || existing.type !== 'file') {
    throw new Error(`Chapitre introuvable: ${slug}`);
  }

  const nextContent = applyProposal(decodeContent(existing), {
    titleFr,
    contributor,
    body: safeBody,
  });
  const chapterNumber = slug.slice(3).replace(/^0+/, '') || '0';
  const branch = `traduction/${slug}-${proposalId.slice(0, 8)}`;
  if (!BRANCH_RE.test(branch)) throw new Error('Branche de PR invalide.');

  await ensureBranch(github, owner, repo, branch, 'main');
  const branchFile = await getFile(github, { owner, repo, path: chapterPath, ref: branch });
  await putFile(github, {
    owner,
    repo,
    path: chapterPath,
    content: nextContent,
    branch,
    message: `traduction: fascicule ${chapterNumber}`,
    sha: branchFile && branchFile.sha,
  });

  const modeLabel = mode === 'deja-traduit' ? 'déjà traduit' : 'à traduire';
  const { data: pr } = await github.rest.pulls.create({
    owner,
    repo,
    title: sanitizeLine(`Traduction PR ${chapterNumber} — ${titleFr || slug}`, 180),
    head: branch,
    base: 'main',
    maintainer_can_modify: true,
    draft: false,
    body: [
      '## Proposition de traduction',
      '',
      `- Fascicule : n° ${chapterNumber} (\`${slug}\`)`,
      `- Titre FR : ${sanitizeLine(titleFr, 200) || '—'}`,
      `- Mode : ${modeLabel}`,
      `- Proposé par : ${sanitizeLine(contributor, 80) || 'anonyme'}`,
      '',
      'PR ouverte automatiquement depuis le site. Elle reste en attente de relecture.',
      'Cette PR ne modifie qu’un fichier markdown de chapitre.',
    ].join('\n'),
  });

  core.info(`PR créée: ${pr.html_url}`);
  return pr;
}

module.exports = async function ingest({ github, context, core }) {
  const payload = context.payload.client_payload || {};
  const slug = sanitizeLine(payload.slug, 20);
  const proposalId = sanitizeLine(payload.proposalId, 36).toLowerCase();
  const mode = sanitizeLine(payload.mode, 20);
  const titleFr = sanitizeLine(payload.titleFr, 200);
  const contributor = sanitizeLine(payload.contributor, 80);
  const chunkIndex = Number(payload.chunkIndex);
  const chunkTotal = Number(payload.chunkTotal);
  const chunk = typeof payload.chunk === 'string' ? payload.chunk : '';

  if (!SLUG_RE.test(slug)) throw new Error('Slug de chapitre invalide.');
  if (!PROPOSAL_RE.test(proposalId)) throw new Error('Identifiant de proposition invalide.');
  if (!MODES.has(mode)) throw new Error('Mode invalide.');
  if (contributor && !CONTRIBUTOR_RE.test(contributor)) {
    throw new Error('Nom du traducteur invalide.');
  }
  if (!Number.isInteger(chunkIndex) || chunkIndex < 0) throw new Error('Index de fragment invalide.');
  if (!Number.isInteger(chunkTotal) || chunkTotal < 1 || chunkTotal > 20) {
    throw new Error('Nombre de fragments invalide.');
  }
  if (chunkIndex >= chunkTotal) throw new Error('Index de fragment hors limites.');
  if (chunk.length > MAX_CHUNK_CHARS) throw new Error('Fragment trop volumineux.');
  if (Object.prototype.hasOwnProperty.call(payload, '__proto__') || Object.prototype.hasOwnProperty.call(payload, 'constructor')) {
    throw new Error('Payload refusé.');
  }

  const owner = context.repo.owner;
  const repo = context.repo.repo;

  core.info(`Chunk ${chunkIndex + 1}/${chunkTotal} pour ${slug}`);
  await writeChunk(github, { owner, repo, proposalId, chunkIndex, chunk });

  for (let attempt = 0; attempt < FINALIZE_ATTEMPTS; attempt += 1) {
    const assembled = await readChunks(github, { owner, repo, proposalId, chunkTotal });
    if (!assembled) {
      await sleep(FINALIZE_DELAY_MS);
      continue;
    }

    const locked = await tryLock(github, { owner, repo, proposalId });
    if (!locked) {
      core.info('Un autre job finalise déjà cette proposition.');
      return;
    }

    await createTranslationPr(github, core, {
      owner,
      repo,
      slug,
      titleFr,
      contributor,
      mode,
      proposalId,
      body: assembled,
    });
    return;
  }

  core.info('Fragments incomplets pour l’instant — un job suivant finalisera.');
};
