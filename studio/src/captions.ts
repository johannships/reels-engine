import type {KaraokeWord, Scene} from './types';

/**
 * Placeholder karaoke timings: distribute each scene's words evenly across
 * the scene's duration. Real timings will come from Whisper later and can be
 * passed in via the `captions` prop instead.
 */
export const buildPlaceholderCaptions = (scenes: Scene[]): KaraokeWord[] => {
  const words: KaraokeWord[] = [];
  let sceneStartMs = 0;

  for (const scene of scenes) {
    const sceneDurationMs = scene.durationSec * 1000;
    const tokens = scene.text.split(/\s+/).filter(Boolean);
    // Small lead-in/tail so words don't start on the exact scene cut.
    const leadMs = 200;
    const tailMs = 300;
    const usable = Math.max(sceneDurationMs - leadMs - tailMs, 1);
    const perWord = usable / tokens.length;

    tokens.forEach((token, i) => {
      words.push({
        word: token,
        startMs: sceneStartMs + leadMs + i * perWord,
        endMs: sceneStartMs + leadMs + (i + 1) * perWord,
      });
    });

    sceneStartMs += sceneDurationMs;
  }

  return words;
};

/**
 * Group words into caption lines of at most `maxWords` (3-4 reads best).
 * Lines never straddle a sentence boundary (scene text always ends a
 * sentence), and words within a sentence are balanced across lines so we
 * never end up with an orphan one-word line.
 */
export const groupIntoLines = (
  words: KaraokeWord[],
  maxWords = 4,
): KaraokeWord[][] => {
  // Split into sentences first.
  const sentences: KaraokeWord[][] = [];
  let current: KaraokeWord[] = [];
  for (const word of words) {
    current.push(word);
    if (/[.!?]["')\]]?$/.test(word.word)) {
      sentences.push(current);
      current = [];
    }
  }
  if (current.length > 0) {
    sentences.push(current);
  }

  // Then split each sentence into balanced lines of <= maxWords.
  const lines: KaraokeWord[][] = [];
  for (const sentence of sentences) {
    const lineCount = Math.ceil(sentence.length / maxWords);
    const base = Math.floor(sentence.length / lineCount);
    let remainder = sentence.length % lineCount;
    let cursor = 0;
    for (let i = 0; i < lineCount; i++) {
      const size = base + (remainder > 0 ? 1 : 0);
      remainder -= 1;
      lines.push(sentence.slice(cursor, cursor + size));
      cursor += size;
    }
  }
  return lines;
};
