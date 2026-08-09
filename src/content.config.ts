import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const cycles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/cycles' }),
  schema: z.object({
    title: z.string(),
    cycleNumber: z.number(),
    bookStart: z.number(),
    bookEnd: z.number(),
    description: z.string(),
    type: z.enum(['fr', 'de']),
    cover: z.string().optional(),
  }),
});

const accueil = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/accueil' }),
  schema: z.object({
    title: z.string(),
    tagline: z.string(),
    subtitle: z.string(),
    ctaPrimary: z.string(),
    ctaSecondary: z.string(),
    stat1: z.string(),
    stat1Label: z.string(),
    stat2: z.string(),
    stat2Label: z.string(),
    stat3: z.string(),
    stat3Label: z.string(),
    sectionAboutTitle: z.string(),
    sectionAboutQuote: z.string(),
    sectionAboutIntro: z.string(),
    sectionAboutText: z.string(),
    card1Title: z.string(),
    card1Text: z.string(),
    card2Title: z.string(),
    card2Text: z.string(),
    sectionOeuvreTitle: z.string(),
    oeuvre1Title: z.string(),
    oeuvre1Text: z.string(),
    oeuvre2Title: z.string(),
    oeuvre2Text: z.string(),
    oeuvre3Title: z.string(),
    oeuvre3Text: z.string(),
    ctaText: z.string(),
    ctaLabel: z.string(),
  }),
});

const tomes = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/tomes' }),
  schema: z.object({
    title: z.string(),
    cycleNumber: z.number(),
    chapterNumber: z.number(),
    type: z.enum(['synopsis', 'translation']).default('synopsis'),
    cover: z.string().optional(),
    synopsis: z.string().optional(),
    originalTitle: z.string().optional(),
    cycle: z.string().optional(),
    traduction: z.string().optional(),
    edition: z.string().optional(),
    parution: z.string().optional(),
  }),
});

const chapitres = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/chapitres' }),
  schema: z.object({
    title: z.string(),
    titleFr: z.string().optional(),
    cycleNumber: z.number(),
    chapterNumber: z.number(),
    type: z.enum(['synopsis', 'translation']).default('translation'),
    cover: z.string().optional(),
    synopsis: z.string().optional(),
    originalTitle: z.string().optional(),
    auteur: z.string().optional(),
    parution: z.string().optional(),
    statut: z.enum(['wip', 'traduit']).default('wip'),
  }),
});

export const collections = { cycles, accueil, tomes, chapitres };
