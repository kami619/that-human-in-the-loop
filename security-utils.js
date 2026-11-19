/**
 * Shared client-side guards for static dashboard pages.
 */
(function initSecurityUtils(global) {
  const GRADIENT_TINT_RE =
    /^linear-gradient\(\s*\d+deg\s*,\s*rgba\(\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*[\d.]+\)\s*0%\s*,\s*rgba\(\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*[\d.]+\)\s*\d{1,3}%\s*\)$/i;

  function sanitizeHttpsUrl(url) {
    if (!url) return '';
    try {
      const parsed = new URL(url, global.location.href);
      if (parsed.protocol !== 'https:') return '';
      return parsed.href;
    } catch {
      return '';
    }
  }

  function safeGradientTint(tint, fallback) {
    const fb = fallback || '#10131C';
    if (!tint || typeof tint !== 'string' || tint.length > 256) return fb;
    if (/[;<>\"'\\]/.test(tint)) return fb;
    return GRADIENT_TINT_RE.test(tint) ? tint : fb;
  }

  global.sanitizeHttpsUrl = sanitizeHttpsUrl;
  global.safeGradientTint = safeGradientTint;
})(typeof window !== 'undefined' ? window : globalThis);