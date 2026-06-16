import type { Entity } from "../types/api";

export interface HighlightSegment {
  start: number;
  end: number;
  text: string;
  entity?: Entity;
}

/** Split deid_text into non-overlapping segments, preferring longer / higher-score entities. */
export function buildHighlightSegments(text: string, entities: Entity[]): HighlightSegment[] {
  if (!text) return [];

  const valid = entities.filter(
    (e) => e.start_char >= 0 && e.end_char > e.start_char && e.end_char <= text.length,
  );

  const winners: (Entity | null)[] = new Array(text.length).fill(null);
  const sorted = [...valid].sort((a, b) => {
    const lenA = a.end_char - a.start_char;
    const lenB = b.end_char - b.start_char;
    if (lenB !== lenA) return lenB - lenA;
    if (b.score !== a.score) return b.score - a.score;
    return a.start_char - b.start_char;
  });

  for (const ent of sorted) {
    for (let i = ent.start_char; i < ent.end_char; i++) {
      if (!winners[i]) winners[i] = ent;
    }
  }

  const segments: HighlightSegment[] = [];
  let i = 0;
  while (i < text.length) {
    const ent = winners[i];
    let j = i + 1;
    while (j < text.length && winners[j] === ent) j++;
    segments.push({ start: i, end: j, text: text.slice(i, j), entity: ent ?? undefined });
    i = j;
  }
  return segments;
}

export function entityAssertionTags(entity: Entity): string[] {
  const tags: string[] = [];
  if (entity.negated) tags.push("negated");
  if (entity.historical) tags.push("historical");
  if (entity.family) tags.push("family");
  if (entity.uncertain) tags.push("uncertain");
  return tags;
}

export function isMutedEntity(entity: Entity): boolean {
  return entity.negated || entity.historical || entity.family;
}

export function linkedCodeLabel(entity: Entity): string | null {
  if (entity.icd10) {
    const desc = entity.icd10_desc ? ` — ${entity.icd10_desc}` : "";
    return `${entity.icd10}${desc}`;
  }
  if (entity.rxnorm) {
    const name = entity.rxnorm_name ?? entity.rxnorm;
    return `RxNorm ${entity.rxnorm}: ${name}`;
  }
  return null;
}
