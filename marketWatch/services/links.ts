/**
 * Helpers for turning competitor/signal "source" strings into openable links.
 *
 * Sources come from the backend as either a real URL (SerpAPI result link),
 * a bare domain ("codingninjas.com"), or a plain label ("Google Search").
 * Only the first two are linkable.
 */

/** Return a fully-qualified https URL if `s` looks like one, else null. */
export function linkify(s?: string | null): string | null {
  if (!s) return null;
  const t = s.trim();
  if (/^https?:\/\//i.test(t)) return t;
  // bare domain like "example.com" or "sub.example.co.uk/path"
  if (/^[\w-]+(\.[\w-]+)+(\/\S*)?$/i.test(t)) return `https://${t}`;
  return null;
}

/** Short, human-friendly host label for display, e.g. "techcrunch.com". */
export function hostLabel(url: string): string {
  return url
    .replace(/^https?:\/\//i, "")
    .replace(/^www\./i, "")
    .split("/")[0];
}
