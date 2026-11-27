// Tile URL helpers for the rain overlays. The API's tiles template carries rescale=0,<hi> for
// the whole region; auto-stretch swaps in the range of the pixels on screen.

// At most 2 decimals, no trailing zeros, for the rescale parameter
const num = (v) => String(+Number(v).toFixed(2));

// The template with its rescale=<a>,<b> replaced by range ([lo, hi]); unchanged when range is null.
export function withRange(template, range) {
  if (!range) return template;
  return template.replace(/rescale=[^&]*/, `rescale=${num(range[0])},${num(range[1])}`);
}

// A legend end: whole numbers from 100 up, one decimal below
export function fmtRange(v) {
  return v >= 100 ? Math.round(v) : +v.toFixed(1);
}
