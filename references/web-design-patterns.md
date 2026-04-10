# Web Design Patterns

Use a static, editorial knowledge-site style. The goal is to make dense Feishu content easier to read, navigate, and share.

## Default Direction

Use `style=editorial` unless the user asks for another direction.

Design traits:
- Paper-like reading rhythm without beige or cream dominance.
- Strong typographic hierarchy.
- Left navigation on desktop, top compact navigation on mobile.
- Reading progress indicator.
- Anchored headings.
- Tables and code blocks that survive narrow screens.
- Search for Wiki sites.

Palette:
- Background: `#f7f8f4`
- Surface: `#ffffff`
- Ink: `#171717`
- Muted text: `#5c625f`
- Forest accent: `#2f6f5e`
- Vermilion accent: `#c0442e`
- Gold accent: `#e0b72f`

Avoid:
- Purple or blue-purple gradients.
- Dark-blue/slate dominant themes.
- Beige/cream/sand/tan dominance.
- Cards inside cards.
- Large rounded corners; keep radius at 8px or less.
- Decorative orbs, bokeh blobs, or generic glassmorphism.

## Faithful Mode

Preserve all content and structure:
- Keep heading hierarchy.
- Keep paragraph order.
- Keep lists, blockquotes, code blocks, tables, and images in place.
- Add a table of contents from headings.
- Add section anchors.
- Improve spacing, type scale, and contrast.

## Recompose Mode

Allowed additions:
- Executive guide at the top.
- Key idea cards derived from headings.
- Topic clusters for Wiki sites.
- Summary blocks before long sections.
- "Read next" navigation.

Hard rule:
- Do not delete source content. Full original text must remain in the body or a clearly labeled appendix.

## Static Site Requirements

Single document:
- `index.html`
- `styles.css`
- optional `app.js`
- optional `media/`

Wiki:
- `index.html`
- `docs/<slug>.html`
- `search-index.json`
- `styles.css`
- `app.js`
- optional `media/`

Responsive behavior:
- Desktop: navigation + content columns.
- Tablet: narrower navigation, content remains readable.
- Mobile: single column, nav becomes an expandable/top area.

Accessibility:
- Keep text contrast strong.
- Add `alt` text from media names or nearby context when possible.
- Preserve keyboard focus states.
- Do not rely on color alone for critical states.

