import { getCollection, getEntry } from 'astro:content';

// The full chapter set is too large to serialize as a single content
// collection (V8 rejects strings over ~512 MB during the data-store write).
// It is split into four collections by leading digit; these helpers aggregate
// them so pages can keep using a single logical "chapitres" set.
export const CHAPITRE_COLLECTIONS = ['chapitres0', 'chapitres1', 'chapitres2', 'chapitres3'];

export function chapterCollectionName(slug: string): string {
  const digit = slug.replace(/^de-/, '').charAt(0);
  return `chapitres${digit}`;
}

export async function getChapitres() {
  const groups = await Promise.all(
    CHAPITRE_COLLECTIONS.map((name) => getCollection(name as any)),
  );
  return groups.flat() as any[];
}

export async function getChapitre(slug: string) {
  return getEntry(chapterCollectionName(slug) as any, slug as any);
}
