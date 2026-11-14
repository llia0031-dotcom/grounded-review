// Fonts (pairing C): headings in Noto Serif SC (思源宋体) 500, body and controls in
// Noto Sans SC (思源黑体) 400/500, Latin letters and digits in Inter (variable). All from Fontsource (OFL-1.1),
// bundled with the page; only these weights are loaded, each with font-display: swap. The Chinese faces come split by
// character ranges, so a page downloads only the pieces it uses.
import '@fontsource-variable/inter/wght.css'
import '@fontsource/noto-sans-sc/400.css'
import '@fontsource/noto-sans-sc/500.css'
import '@fontsource/noto-serif-sc/500.css'

// Chinese curly quotes. Inter comes first in the stacks (for Latin letters and digits) and also has “ ” ‘ ’, so on a
// Chinese page those would be drawn as narrow Latin quotes next to Chinese text. These two aliases cover only the four
// quote characters and point at the Noto files that hold them, so quotes always take the Chinese faces' glyphs.
import serifQuotes from '@fontsource/noto-serif-sc/files/noto-serif-sc-latin-500-normal.woff2?url'
import sans400Quotes from '@fontsource/noto-sans-sc/files/noto-sans-sc-latin-400-normal.woff2?url'
import sans500Quotes from '@fontsource/noto-sans-sc/files/noto-sans-sc-latin-500-normal.woff2?url'

const QUOTES = 'U+2018-2019, U+201C-201D'
for (const [family, url, weight] of [['Quotes Serif SC', serifQuotes, '500'], ['Quotes Sans SC', sans400Quotes, '400'], ['Quotes Sans SC', sans500Quotes, '500']]) {
  document.fonts.add(new FontFace(family, `url(${url}) format('woff2')`, { unicodeRange: QUOTES, weight, display: 'swap' }))
}
