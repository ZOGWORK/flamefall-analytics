// Retrieval and extraction only. A question is scored against sourced statements and catalogue
// rows with the TF-IDF index that Python built (search.json); the answer is those statements
// themselves. No text is generated, so no number can be invented.
// Mirrors flamefall/catalogue.py: expand, search, parse_filters, answer.

import type { SearchData, SearchDoc } from "./types";

export interface Filters {
  o2_at_least?: number;
  o2_at_most?: number;
  evidence_class?: string;
}

export interface Hit {
  doc: SearchDoc;
  score: number;
}

export interface Answer {
  query: string;
  filters: Filters;
  n_hits: number;
  statements: Hit[];
  hits: Hit[];
  investigations: string[];
}

const ABOVE = /(above|over|greater than|more than|at least|exceed\w*|>=?)\s*(\d+(?:\.\d+)?)\s*(%|percent)/i;
const BELOW = /(below|under|less than|at most|<=?)\s*(\d+(?:\.\d+)?)\s*(%|percent)/i;

export class SearchIndex {
  private termIndex = new Map<string, number>();
  private stop: Set<string>;

  constructor(private data: SearchData) {
    data.vocab.forEach((term, i) => this.termIndex.set(term, i));
    this.stop = new Set(data.stop_words);
  }

  /** The question as lower-case words, plus the synonyms of any word that has them. */
  expand(query: string): string {
    const words = query.toLowerCase().match(/[a-z0-9]+/g) ?? [];
    const extra = words.filter((w) => w in this.data.synonyms).map((w) => this.data.synonyms[w]);
    return [...words, ...extra].join(" ");
  }

  /** TF-IDF vector of a question: words of two or more characters, stop words removed, 1- and 2-grams. */
  private vector(query: string): Map<number, number> {
    const tokens = (this.expand(query).match(/\b\w\w+\b/g) ?? []).filter((t) => !this.stop.has(t));
    const grams = [...tokens];
    for (let i = 0; i + 1 < tokens.length; i++) grams.push(`${tokens[i]} ${tokens[i + 1]}`);
    const counts = new Map<number, number>();
    for (const gram of grams) {
      const j = this.termIndex.get(gram);
      if (j !== undefined) counts.set(j, (counts.get(j) ?? 0) + 1);
    }
    let norm = 0;
    const weights = new Map<number, number>();
    for (const [j, tf] of counts) {
      const w = (1 + Math.log(tf)) * this.data.idf[j];
      weights.set(j, w);
      norm += w * w;
    }
    norm = Math.sqrt(norm);
    if (norm > 0) for (const [j, w] of weights) weights.set(j, w / norm);
    return weights;
  }

  /** Cosine score of every document against the question, in corpus order. */
  scores(query: string): number[] {
    const q = this.vector(query);
    return this.data.vectors.map((vec) => {
      let s = 0;
      for (const [j, w] of vec) {
        const qw = q.get(j);
        if (qw !== undefined) s += qw * w;
      }
      return s;
    });
  }

  search(query: string, k = 8): Hit[] {
    if (!query || !query.trim()) return [];
    const scores = this.scores(query);
    return this.data.docs
      .map((doc, i) => ({ doc, score: scores[i], i }))
      .filter((h) => h.score >= this.data.min_score)
      .sort((a, b) => b.score - a.score || a.i - b.i)
      .slice(0, k)
      .map(({ doc, score }) => ({ doc, score }));
  }

  /** Numeric oxygen limits and a fuel class, if the question states them in words. */
  parseFilters(query: string): Filters {
    const q = query.toLowerCase();
    const out: Filters = {};
    if (q.includes("oxygen") || /\bo2\b/.test(q)) {
      // "co2" must not be read as "o2"
      const above = ABOVE.exec(q);
      if (above) out.o2_at_least = Number(above[2]);
      const below = BELOW.exec(q);
      if (below) out.o2_at_most = Number(below[2]);
    }
    const classes = new Set<string>();
    for (const [word, cls] of Object.entries(this.data.class_words)) {
      if (new RegExp(`\\b${word}s?\\b`).test(q)) classes.add(cls);
    }
    // words of two classes ("materials ... smoke detector") name no single class
    if (classes.size === 1) out.evidence_class = [...classes][0];
    return out;
  }

  /**
   * Extractive answer: the retrieved, sourced statements.
   * If the question states an oxygen limit, the evidence is first filtered on its recorded
   * ambient-oxygen range (a burner feed is never matched), and the filter is reported back.
   * The same limit is applied to the investigations listed with the answer, on their tested ranges.
   */
  answer(query: string, k = 6): Answer {
    const filters = this.parseFilters(query);
    let hits = this.search(query, k);
    let statements = hits.filter((h) => h.doc.kind === "evidence");
    const hasO2 = filters.o2_at_least !== undefined || filters.o2_at_most !== undefined;
    if (Object.keys(filters).length > 0) {
      const scores = this.scores(query);
      let docs = this.data.docs
        .map((doc, i) => ({ doc, score: scores[i], i }))
        .filter((h) => h.doc.kind === "evidence");
      if (hasO2) {
        docs = docs.filter((h) => h.doc.o2_is_ambient === true && h.doc.o2_max_pct !== null);
        if (filters.o2_at_least !== undefined) {
          docs = docs.filter((h) => (h.doc.o2_max_pct as number) >= (filters.o2_at_least as number));
        }
        if (filters.o2_at_most !== undefined) {
          docs = docs.filter((h) => h.doc.o2_min_pct !== null && h.doc.o2_min_pct <= (filters.o2_at_most as number));
        }
      } else {
        docs = docs.filter((h) => h.score >= this.data.min_score); // class only: still a text match
      }
      let wanted: Set<string> | null = null;
      if (filters.evidence_class) {
        wanted = new Set([filters.evidence_class]);
        if (filters.evidence_class === "solid") wanted.add("partial_g");
        const w = wanted;
        docs = docs.filter((h) => h.doc.evidence_class !== null && w.has(h.doc.evidence_class));
      }
      statements = docs
        .sort((a, b) => b.score - a.score || a.i - b.i)
        .slice(0, k)
        .map(({ doc, score }) => ({ doc, score }));
      if (hasO2) {
        const matching = new Set(docs.map((h) => h.doc.doc_id));
        const inRange = (id: string) => {
          const range = this.data.investigation_o2[id];
          if (!range) return false; // no tested range: cannot match a limit
          if (filters.o2_at_least !== undefined && range[1] < filters.o2_at_least) return false;
          if (filters.o2_at_most !== undefined && range[0] > filters.o2_at_most) return false;
          return true;
        };
        hits = hits.filter((h) => (h.doc.kind === "evidence" ? matching.has(h.doc.doc_id) : inRange(h.doc.investigation_id)));
      }
      if (wanted) {
        const w = wanted;
        const keep = new Set(statements.map((s) => s.doc.investigation_id));
        for (const [id, cls] of Object.entries(this.data.investigation_class)) if (w.has(cls)) keep.add(id);
        hits = hits.filter((h) => keep.has(h.doc.investigation_id));
      }
    }
    const investigations = [
      ...new Set([...statements.map((s) => s.doc.investigation_id), ...hits.map((h) => h.doc.investigation_id)]),
    ];
    return {
      query,
      filters,
      n_hits: statements.length + hits.filter((h) => h.doc.kind !== "evidence").length,
      statements,
      hits,
      investigations,
    };
  }
}
