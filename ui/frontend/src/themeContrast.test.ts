import { describe, expect, it } from "vitest";
import css from "./styles.css?raw";

/* post162: every text / fill pair the UI draws, in BOTH themes, meets WCAG 2.2 AA
   (1.4.3 text 4.5:1; 1.4.11 the focus ring 3:1). Tokens are read from styles.css
   itself, so a palette edit that breaks contrast fails here. */

function block(selector: string): Record<string, string> {
  const start = css.indexOf(`${selector} {`);
  expect(start, `${selector} block`).toBeGreaterThanOrEqual(0);
  const body = css.slice(start, css.indexOf("\n}", start));
  const out: Record<string, string> = {};
  for (const m of body.matchAll(/--([a-z0-9-]+):\s*([^;]+);/g)) out[m[1]] = m[2].trim();
  return out;
}

const light = block(":root");
const dark = { ...light, ...block(':root[data-theme="dark"]') };

function hex(tokens: Record<string, string>, name: string, seen: string[] = []): string {
  const value = tokens[name];
  expect(value, `--${name}`).toBeDefined();
  const ref = /^var\(--([a-z0-9-]+)\)$/.exec(value);
  if (ref) {
    expect(seen).not.toContain(name);
    return hex(tokens, ref[1], [...seen, name]);
  }
  expect(value, `--${name} must be a hex colour`).toMatch(/^#[0-9a-fA-F]{6}$/);
  return value;
}

function luminance(color: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(color.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// [text, background] - the pairs the stylesheet actually uses
const TEXT_PAIRS: [string, string][] = [
  ["ink", "page"], ["ink", "surface"], ["ink", "surface-2"],
  ["ink-2", "surface"], ["ink-2", "surface-2"], ["ink-2", "hairline"],
  ["muted", "page"], ["muted", "surface"], ["muted", "surface-2"],
  ["heading", "page"], ["heading", "surface"],
  ["accent", "page"], ["accent", "surface"], ["accent", "surface-2"], ["accent", "accent-tint"],
  ["on-accent", "accent-deep"], ["on-accent", "accent-hover"], ["on-accent", "accent"],
  ["on-accent-light", "accent-light"],
  ["on-critical", "critical"], ["on-warning", "warning"],
  ["good-text", "good-bg"], ["good-text", "surface"],
  ["warning-text", "warning-bg"], ["warning-text", "surface"],
  ["critical-text", "critical-bg"], ["critical-text", "surface"],
  ["info", "info-bg"], ["info", "surface"],
  ["flag-text", "surface"], ["flag-text", "surface-2"],
  ["shell-ink", "shell-bg"],
  ["sidebar-ink", "sidebar-bg"], ["sidebar-muted", "sidebar-bg"],
  ["code-keyword", "surface-2"], ["code-string", "surface-2"],
  ["code-number", "surface-2"], ["code-function", "surface-2"],
];

describe.each([
  ["light", light],
  ["dark", dark],
])("the %s theme", (_name, tokens) => {
  it.each(TEXT_PAIRS)("--%s on --%s is at least 4.5:1", (fg, bg) => {
    expect(contrast(hex(tokens, fg), hex(tokens, bg))).toBeGreaterThanOrEqual(4.5);
  });

  it("the focus ring (--accent) stands out from every surface at 3:1", () => {
    for (const bg of ["page", "surface", "surface-2"]) {
      expect(contrast(hex(tokens, "accent"), hex(tokens, bg))).toBeGreaterThanOrEqual(3);
    }
  });
});

describe("dark still reads as ACFC", () => {
  it("uses ACFC light blue as its accent and ACFC yellow / orange for status", () => {
    expect(dark.accent.toLowerCase()).toBe("#69b3e7");
    expect(dark.warning.toLowerCase()).toBe("#ffcb05");
    expect(dark.flag.toLowerCase()).toBe("#f7921e");
  });

  it("never paints pure black: every surface is a navy (blue channel highest)", () => {
    for (const name of ["page", "surface", "surface-2"]) {
      const c = hex(dark, name);
      const [r, g, b] = [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
      expect(c).not.toBe("#000000");
      expect(b).toBeGreaterThan(r);
      expect(b).toBeGreaterThan(g);
    }
  });
});
