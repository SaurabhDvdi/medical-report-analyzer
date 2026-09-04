/**
 * Strict numeric formatting helper for clinical laboratory analytics.
 * Guarantees valid numeric zero (0, 0.0, "0") renders as 0.00,
 * while preventing type coercion of empty strings, whitespace, null,
 * undefined, NaN, Infinity, -Infinity, or non-numeric strings into zero.
 */
export function safeFormatNumber(val, dec = 2, fallback = 'Unavailable') {
  if (val === null || val === undefined) return fallback
  if (typeof val === 'string' && val.trim() === '') return fallback
  const num = Number(val)
  if (!Number.isFinite(num)) return fallback
  if (dec === 'auto' || dec === null) {
    return Number.isInteger(num) ? String(num) : parseFloat(num.toFixed(2)).toString()
  }
  return num.toFixed(dec)
}
