#!/usr/bin/env python3
"""Build a static editorial website from feishu-doc-webify content.json."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
MEDIA_TAG_RE = re.compile(r"<(image|file|whiteboard)\b([^>]*)/?>", re.IGNORECASE)
ATTR_RE = re.compile(r'([A-Za-z_:-]+)="([^"]*)"')


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or fallback


def attrs(raw: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in ATTR_RE.finditer(raw)}


def inline_markdown(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def merge_media(content: dict, content_path: Path) -> dict[str, dict]:
    media_by_token = {item.get("token"): item for item in content.get("media", []) if item.get("token")}
    sibling_manifest = content_path.parent / "media-manifest.json"
    if sibling_manifest.exists():
        manifest = json.loads(sibling_manifest.read_text(encoding="utf-8"))
        for item in manifest.get("media", []):
            token = item.get("token")
            if token:
                media_by_token.setdefault(token, {}).update(item)
    return media_by_token


def resolve_downloaded_file(local_path: str | None) -> Path | None:
    if not local_path:
        return None
    path = Path(local_path)
    if path.exists():
        return path
    matches = sorted(path.parent.glob(path.name + "*")) if path.parent.exists() else []
    return matches[0] if matches else None


def media_replacer(media_by_token: dict[str, dict], out_dir: Path):
    media_dir = out_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    def replace(match: re.Match) -> str:
        kind = match.group(1).lower()
        item_attrs = attrs(match.group(2))
        token = item_attrs.get("token")
        item = media_by_token.get(token or "", {})
        title = item.get("name") or item_attrs.get("name") or kind
        downloaded = resolve_downloaded_file(item.get("local_path"))
        if downloaded:
            target = media_dir / downloaded.name
            if downloaded.resolve() != target.resolve():
                shutil.copy2(downloaded, target)
            rel = "media/" + target.name
            if kind in {"image", "whiteboard"}:
                return f'<figure><img class="local-media" src="{html.escape(rel)}" alt="{html.escape(title)}"><figcaption>{html.escape(title)}</figcaption></figure>'
            return f'<p><a class="file-link" href="{html.escape(rel)}">{html.escape(title)}</a></p>'
        return f'<div class="media-placeholder">{html.escape(title)} media placeholder ({html.escape(kind)})</div>'

    return replace


def markdown_to_html(markdown: str, media_by_token: dict[str, dict], out_dir: Path) -> tuple[str, list[dict]]:
    markdown = MEDIA_TAG_RE.sub(media_replacer(media_by_token, out_dir), markdown)
    markdown = re.sub(r"</?view\b[^>]*>", "", markdown, flags=re.IGNORECASE)
    lines = markdown.splitlines()
    html_parts: list[str] = []
    toc: list[dict] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            html_parts.append("<p>" + inline_markdown(" ".join(paragraph).strip()) + "</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_parts.append("</ul>")
            in_list = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip()
                code_lines = []
            else:
                language_class = f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                html_parts.append(f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines))}</code></pre>")
                in_code = False
                code_lang = ""
                code_lines = []
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            i += 1
            continue

        heading = HEADING_RE.match(stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            anchor = slugify(text, f"section-{len(toc) + 1}")
            toc.append({"level": level, "text": re.sub(r"<[^>]+>", "", text), "id": anchor})
            html_parts.append(f'<h{level} id="{anchor}">{inline_markdown(text)}</h{level}>')
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            quote = stripped.lstrip("> ")
            html_parts.append(f"<blockquote>{inline_markdown(quote)}</blockquote>")
            i += 1
            continue

        if re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append("<li>" + inline_markdown(re.sub(r"^[-*]\s+", "", stripped)) + "</li>")
            i += 1
            continue

        if "|" in stripped and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:-]+\|", lines[i + 1]):
            flush_paragraph()
            close_list()
            rows = [stripped, lines[i + 1].strip()]
            i += 2
            while i < len(lines) and "|" in lines[i]:
                rows.append(lines[i].strip())
                i += 1
            header_cells = [cell.strip() for cell in rows[0].strip("|").split("|")]
            body_rows = rows[2:]
            table = ["<table><thead><tr>"]
            table.extend(f"<th>{inline_markdown(cell)}</th>" for cell in header_cells)
            table.append("</tr></thead><tbody>")
            for row in body_rows:
                table.append("<tr>")
                table.extend(f"<td>{inline_markdown(cell.strip())}</td>" for cell in row.strip("|").split("|"))
                table.append("</tr>")
            table.append("</tbody></table>")
            html_parts.append("".join(table))
            continue

        if stripped.startswith("<") and stripped.endswith(">"):
            flush_paragraph()
            close_list()
            html_parts.append(stripped)
            i += 1
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    close_list()
    return "\n".join(html_parts), toc


def load_css() -> str:
    skill_dir = Path(__file__).resolve().parents[1]
    css_path = skill_dir / "assets" / "editorial-theme.css"
    return css_path.read_text(encoding="utf-8")


def page_shell(title: str, body: str, sidebar: str, subtitle: str = "") -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="progress" id="progress"></div>
  <main class="shell">
    <aside class="sidebar">
      <p class="brand">Feishu Doc Webify</p>
      {sidebar}
    </aside>
    <section class="content">
      <header class="hero">
        <p class="eyebrow">{html.escape(subtitle or "Knowledge Site")}</p>
        <h1>{html.escape(title)}</h1>
      </header>
      {body}
      <footer class="footer">Generated from Feishu content. Review visibility before sharing public links.</footer>
    </section>
  </main>
  <script src="app.js"></script>
</body>
</html>
"""


def toc_html(toc: list[dict], current_docs: list[dict] | None = None) -> str:
    parts: list[str] = []
    if current_docs:
        parts.append('<input class="search" id="search" placeholder="搜索这个知识站">')
        parts.append('<ul class="doc-list" id="results">')
        for doc in current_docs:
            href = "index.html" if doc.get("is_index") else f"docs/{doc['slug']}.html"
            parts.append(f'<li><a href="{html.escape(href)}">{html.escape(doc["title"])}</a></li>')
        parts.append("</ul>")
    if toc:
        parts.append('<ul class="toc">')
        for item in toc:
            if item["level"] <= 3:
                parts.append(f'<li><a href="#{html.escape(item["id"])}">{html.escape(item["text"])}</a></li>')
        parts.append("</ul>")
    return "\n".join(parts)


def recompose_intro(doc: dict, toc: list[dict]) -> str:
    cards = toc[:6]
    if not cards:
        return ""
    chunks = ['<section class="guide-grid">']
    for item in cards:
        chunks.append(
            '<a class="guide-card" href="#{}"><strong>{}</strong><br><span>跳转到这一节继续阅读</span></a>'.format(
                html.escape(item["id"]), html.escape(item["text"])
            )
        )
    chunks.append("</section>")
    return "\n".join(chunks)


def render_doc_page(doc: dict, all_docs: list[dict], media_by_token: dict[str, dict], out_dir: Path, mode: str, root_relative: str = "") -> tuple[str, list[dict]]:
    body_html, toc = markdown_to_html(doc.get("markdown", ""), media_by_token, out_dir)
    if mode == "recompose":
        body_html = recompose_intro(doc, toc) + f'<article class="doc-body">{body_html}</article>'
    else:
        body_html = f'<article class="doc-body">{body_html}</article>'
    docs_for_nav = []
    for entry in all_docs:
        nav = dict(entry)
        nav["is_index"] = False
        docs_for_nav.append(nav)
    sidebar = toc_html(toc, docs_for_nav if len(all_docs) > 1 else None)
    page = page_shell(doc["title"], body_html, sidebar, "Feishu Document")
    if root_relative:
        page = page.replace('href="styles.css"', f'href="{root_relative}styles.css"')
        page = page.replace('src="app.js"', f'src="{root_relative}app.js"')
        page = page.replace('href="docs/', f'href="{root_relative}docs/')
        page = page.replace('src="media/', f'src="{root_relative}media/')
        page = page.replace('href="media/', f'href="{root_relative}media/')
    return page, toc


def build_site(content: dict, content_path: Path, out_dir: Path, mode: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "docs").mkdir(exist_ok=True)
    media_by_token = merge_media(content, content_path)
    docs = content.get("docs") or []
    if not docs:
        raise ValueError("content.json does not contain any supported docs.")

    search_index = []
    for doc in docs:
        search_index.append(
            {
                "title": doc["title"],
                "url": "index.html" if len(docs) == 1 else f"docs/{doc['slug']}.html",
                "text": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", doc.get("markdown", "")))[:4000],
            }
        )

    if len(docs) == 1:
        page, _ = render_doc_page(docs[0], docs, media_by_token, out_dir, mode)
        (out_dir / "index.html").write_text(page, encoding="utf-8")
    else:
        cards = ['<section class="guide-grid">']
        for doc in docs:
            cards.append(
                '<a class="guide-card" href="docs/{}.html"><strong>{}</strong><br><span>阅读文档</span></a>'.format(
                    html.escape(doc["slug"]), html.escape(doc["title"])
                )
            )
        cards.append("</section>")
        skipped = content.get("skipped_nodes") or []
        if skipped:
            cards.append("<h2>未纳入网页化的节点</h2><ul>")
            for item in skipped:
                cards.append(
                    "<li>{} ({}) - {}</li>".format(
                        html.escape(str(item.get("title", "Untitled"))),
                        html.escape(str(item.get("obj_type", "unknown"))),
                        html.escape(str(item.get("reason", "unsupported"))),
                    )
                )
            cards.append("</ul>")
        sidebar = toc_html([], docs)
        index_page = page_shell(content.get("title") or "Feishu Knowledge Site", "\n".join(cards), sidebar, "Wiki Knowledge Site")
        (out_dir / "index.html").write_text(index_page, encoding="utf-8")
        for doc in docs:
            page, _ = render_doc_page(doc, docs, media_by_token, out_dir, mode, root_relative="../")
            (out_dir / "docs" / f"{doc['slug']}.html").write_text(page, encoding="utf-8")

    (out_dir / "styles.css").write_text(load_css(), encoding="utf-8")
    (out_dir / "search-index.json").write_text(json.dumps(search_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "app.js").write_text(APP_JS, encoding="utf-8")


APP_JS = """(() => {
  const progress = document.getElementById('progress');
  const updateProgress = () => {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const pct = height > 0 ? (scrollTop / height) * 100 : 0;
    if (progress) progress.style.width = `${pct}%`;
  };
  document.addEventListener('scroll', updateProgress, { passive: true });
  updateProgress();

  const input = document.getElementById('search');
  const results = document.getElementById('results');
  if (!input || !results) return;
  fetch((location.pathname.includes('/docs/') ? '../' : '') + 'search-index.json')
    .then((response) => response.json())
    .then((items) => {
      const render = (query = '') => {
        const q = query.trim().toLowerCase();
        const matched = q ? items.filter((item) => `${item.title} ${item.text}`.toLowerCase().includes(q)) : items;
        results.innerHTML = matched.slice(0, 30).map((item) => `<li><a href="${location.pathname.includes('/docs/') ? '../' : ''}${item.url}">${item.title}</a></li>`).join('');
      };
      input.addEventListener('input', () => render(input.value));
      render();
    })
    .catch(() => {});
})();
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a static website from feishu-doc-webify content.")
    parser.add_argument("--content", required=True, help="Path to content.json.")
    parser.add_argument("--mode", required=True, choices=["faithful", "recompose"], help="Content treatment mode.")
    parser.add_argument("--style", default="editorial", choices=["editorial"], help="Visual style.")
    parser.add_argument("--out", required=True, help="Output site directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    content_path = Path(args.content).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    content = json.loads(content_path.read_text(encoding="utf-8"))
    build_site(content, content_path, out_dir, args.mode)
    print(json.dumps({"ok": True, "site": str(out_dir), "index": str(out_dir / "index.html")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
