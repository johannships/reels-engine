import type {Scene} from '../types';

/**
 * Which caption words get the accent colour.
 *
 * In the reference reel roughly one word per 3-word cue is violet, and it is
 * always the word that carries the sentence: the number, the repo name, or
 * the money word. This module derives that set from the script text so no
 * hand-tagging is needed; an episode can still add `accentWords` to force
 * extra ones.
 */

/** Spelled-out numbers — the scripts say "ninety eight percent", not "98%". */
const NUMBER_WORDS = new Set([
  'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
  'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
  'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty', 'thirty',
  'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety', 'hundred',
  'thousand', 'million', 'billion', 'first', 'second', 'third',
]);

/** Money / traction words — the "why you care" half of every line. */
const MONEY_WORDS = new Set([
  'free', 'sell', 'sells', 'selling', 'sold', 'money', 'paid', 'pay',
  'pays', 'paying', 'charge', 'charges', 'charging', 'price', 'priced',
  'cost', 'costs', 'bill', 'revenue', 'profit', 'dollar', 'dollars',
  'cash', 'client', 'clients', 'stars', 'star', 'percent',
]);

/**
 * Repo names are full of ordinary English ("i-have-adhd", "context-mode",
 * "browser-use"), and accenting a name's parts would light up pronouns and
 * filler all through the script. These are never taken from a repo name.
 */
const STOPWORDS = new Set([
  'have', 'this', 'that', 'with', 'from', 'your', 'they', 'them', 'then',
  'than', 'what', 'when', 'will', 'were', 'been', 'because', 'about',
  'into', 'over', 'just', 'like', 'make', 'more', 'most', 'some', 'such',
  'code', 'open', 'source', 'tool', 'tools', 'agent', 'agents', 'data',
  'text', 'file', 'files', 'mode', 'main', 'core', 'auto', 'user', 'users',
  'self', 'full', 'best', 'good', 'next', 'live', 'time', 'work', 'help',
]);

const strip = (word: string) =>
  word.toLowerCase().replace(/[^a-z0-9$'-]/g, '');

/**
 * Every token that identifies a repo in this episode: the full "owner/name",
 * the name on its own, and each hyphen-separated part of it. Scripts say
 * "camofox-browser" and "context-mode", so the hyphenated form is what a
 * caption word will actually be.
 */
export const repoTokens = (scenes: Scene[]): Set<string> => {
  const out = new Set<string>();
  for (const scene of scenes) {
    if (scene.type !== 'repo') continue;
    const [owner, name] = scene.repo.split('/');
    for (const part of [owner, name]) {
      if (!part) continue;
      out.add(strip(part));
      // Hyphenated names also show up split across whisper tokens.
      for (const piece of part.split(/[-_.]/)) {
        // Single letters ("i" in "i-have-adhd") would accent every stray
        // pronoun, so only keep pieces that read as words — and never a
        // stopword, or "i-have-adhd" would accent every "have" in the script.
        const token = strip(piece);
        if (token.length >= 4 && !STOPWORDS.has(token)) out.add(token);
      }
    }
  }
  out.delete('');
  return out;
};

export type AccentTest = (word: string) => boolean;

export const makeAccentTest = (
  scenes: Scene[],
  explicit: string[] | undefined,
): AccentTest => {
  const repos = repoTokens(scenes);
  const forced = new Set((explicit ?? []).map(strip));
  forced.delete('');
  return (raw: string) => {
    const word = strip(raw);
    if (!word) return false;
    if (forced.has(word)) return true;
    // Any digit at all: "35,615", "98%", "10,659".
    if (/\d/.test(word)) return true;
    if (raw.includes('$')) return true;
    if (NUMBER_WORDS.has(word)) return true;
    if (MONEY_WORDS.has(word)) return true;
    if (repos.has(word)) return true;
    return false;
  };
};

/**
 * Accent flags for one cue. If the test would light up every word (e.g.
 * "Thirty one thousand stars") the cue would read as a solid block of
 * violet and lose the emphasis entirely, so in that case only the first two
 * words keep the accent.
 */
export const accentFlags = (words: string[], test: AccentTest): boolean[] => {
  const flags = words.map(test);
  const lit = flags.filter(Boolean).length;
  if (words.length > 1 && lit === words.length) {
    return flags.map((_, i) => i < 2);
  }
  return flags;
};
