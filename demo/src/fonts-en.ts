// Fonts for the English pages, the same set as the portfolio site: headings in Redaction 400, everything else in
// Geist (variable). Both from Fontsource (OFL-1.1), bundled with the page with font-display: swap.
import '@fontsource/redaction/400.css'
import '@fontsource-variable/geist/index.css'

// The one Chinese label on these pages is the language link, 中文. Its two characters take Noto Sans SC 500 (思源黑体,
// the Chinese body face) from the two Fontsource files that hold them, not a system font.
import zhong from '@fontsource/noto-sans-sc/files/noto-sans-sc-119-500-normal.woff2?url'
import wen from '@fontsource/noto-sans-sc/files/noto-sans-sc-118-500-normal.woff2?url'

for (const [url, range] of [[zhong, 'U+4E2D'], [wen, 'U+6587']]) {
  document.fonts.add(new FontFace('Lang SC', `url(${url}) format('woff2')`, { unicodeRange: range, weight: '500', display: 'swap' }))
}
