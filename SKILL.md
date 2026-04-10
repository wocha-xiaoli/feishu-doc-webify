---
name: feishu-doc-webify
description: Turn Feishu/Lark docs and Wiki knowledge bases into polished static websites. Use when the user provides a Feishu docx/doc/wiki URL and asks to make it webpage-like, webify it, publish it, turn a heavy knowledge base into a beautiful website, improve Feishu document layout beyond Feishu's native formatting, or generate a GitHub Pages site from Feishu document content.
---

# Feishu Doc Webify

## What This Skill Does

Convert a Feishu document or Wiki subtree into a refined static website, preview it locally, then publish it to GitHub Pages by default.

Default behavior:
- Support both single documents and Wiki subtrees.
- Use faithful enhancement unless the user explicitly asks for intelligent restructuring.
- Generate static HTML/CSS/JS, not React/Vite.
- Ask before publishing whether the GitHub repository should be public or private.
- Detect document media and ask whether to download/localize it.

## Required Context

Before touching Feishu content, read:
- `~/.agents/skills/lark-shared/SKILL.md` for auth, identity, permissions, and safety rules.
- `~/.agents/skills/lark-doc/SKILL.md` for doc URL/token handling and `docs +fetch`.
- `~/.agents/skills/lark-wiki/SKILL.md` when handling Wiki links or subtrees.
- `references/lark-doc-pipeline.md` in this skill for the concrete webify pipeline.

Before designing the website, read:
- `references/web-design-patterns.md`.
- Optionally `~/.codex/skills/frontend-design/SKILL.md` or the user's named design skill if they request a specific style.

Before publishing, read:
- `references/github-pages.md`.

## Workflow

### 1. Clarify Only Product Decisions

Do not ask for details that can be discovered from the URL or CLI. Ask only:
- Single document or Wiki subtree, if the user's source is ambiguous.
- Faithful enhancement or intelligent restructuring, if the user asks for design-heavy transformation but does not specify.
- Whether to download detected media.
- GitHub repository name and public/private visibility before publishing.

Defaults:
- `scope=single` for `/docx/` and `/doc/`.
- `scope=wiki` for `/wiki/` when the user says knowledge base, subtree, whole wiki, or multi-page site.
- `mode=faithful`.
- `style=editorial`.

### 2. Check Environment

Run a non-destructive check:

```bash
for cmd in lark-cli gh git python3; do
  command -v "$cmd" >/dev/null && echo "OK $cmd" || echo "MISSING $cmd"
done
lark-cli whoami >/dev/null 2>&1 && echo "OK Feishu auth" || echo "NEEDS Feishu auth"
gh auth status >/dev/null 2>&1 && echo "OK GitHub auth" || echo "NEEDS GitHub auth"
```

If auth is missing, stop and tell the user exactly which login command is needed.

### 3. Fetch Content

Use the fetch script:

```bash
python3 scripts/fetch_feishu_content.py \
  --source "https://example.feishu.cn/wiki/xxxx" \
  --scope wiki \
  --out ./feishu-webify-export
```

Outputs:
- `content.json`: normalized site content.
- `media-manifest.json`: images, files, and whiteboards discovered in Markdown.
- `fetch-report.json`: source, supported docs, skipped nodes, and errors.

If media is present, show the counts by type and ask whether to localize it.

### 4. Download Media When Confirmed

```bash
python3 scripts/download_media.py \
  --manifest ./feishu-webify-export/media-manifest.json \
  --out ./feishu-webify-export/site/media
```

If the user skips media, continue. The generated website should show tasteful placeholders rather than broken links.

### 5. Build Static Site

Faithful mode:

```bash
python3 scripts/build_static_site.py \
  --content ./feishu-webify-export/content.json \
  --mode faithful \
  --style editorial \
  --out ./feishu-webify-export/site
```

Intelligent restructuring mode:

```bash
python3 scripts/build_static_site.py \
  --content ./feishu-webify-export/content.json \
  --mode recompose \
  --style editorial \
  --out ./feishu-webify-export/site
```

Rules:
- Never delete original content.
- In `recompose`, add guide, summary, cards, and thematic navigation, but preserve full source text in the reading body or appendix.
- For Wiki sites, generate a homepage, per-doc pages, navigation, and search index.

Preview with:

```bash
open ./feishu-webify-export/site/index.html
```

Iterate on design until the user accepts it.

### 6. Publish to GitHub Pages

Before publishing, ask:
- Repository name.
- Public or private visibility.

Then run:

```bash
bash scripts/publish_github_pages.sh \
  --site-dir ./feishu-webify-export/site \
  --repo feishu-doc-web \
  --visibility public
```

If private Pages is not supported by the user's GitHub account, stop and explain. Do not silently switch to public.

## Quality Bar

The site should feel like a designed knowledge product, not a pasted document:
- Clear table of contents and section anchors.
- Stable mobile layout.
- Readable code blocks and tables.
- Visible source attribution and update time.
- Search for Wiki sites.
- No broken media links; use placeholders when media is skipped or unavailable.

## Script Reference

- `scripts/fetch_feishu_content.py`: fetch and normalize Feishu document/Wiki content.
- `scripts/download_media.py`: download document media listed in the manifest.
- `scripts/build_static_site.py`: generate the static HTML site.
- `scripts/publish_github_pages.sh`: publish the site to GitHub Pages.

