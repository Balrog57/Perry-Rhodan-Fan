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

const chapters = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/chapters' }),
  schema: z.object({
    title: z.string(),
    cycleNumber: z.number(),
    chapterNumber: z.number(),
    type: z.enum(['synopsis', 'translation']),
    cover: z.string().optional(),
    synopsis: z.string().optional(),
    originalTitle: z.string().optional(),
    cycle: z.string().optional(),
    traduction: z.string().optional(),
    edition: z.string().optional(),
    parution: z.string().optional(),
  }),
});

export const collections = { cycles, chapters };
