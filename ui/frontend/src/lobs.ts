// A feed can carry a dozen-plus LOB codes (CAQH lists 14 REG segments) —
// headers and cards show the first few; the full list lives in the
// Overview tab.
export function lobLabel(lobs: string[], max = 3): string {
  if (lobs.length <= max) return lobs.join(", ");
  return `${lobs.slice(0, max).join(", ")} +${lobs.length - max} more`;
}
