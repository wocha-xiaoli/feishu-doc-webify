# Feishu Document Pipeline

Use this reference after reading `lark-shared`, `lark-doc`, and, for Wiki sources, `lark-wiki`.

## Source Handling

Supported source URL patterns:

| Pattern | Default scope | Token behavior |
| --- | --- | --- |
| `/docx/<token>` | `single` | Use URL directly with `lark-cli docs +fetch`. |
| `/doc/<token>` | `single` | Use URL directly with `lark-cli docs +fetch`. |
| `/wiki/<token>` | Ask or infer | Resolve the Wiki node before assuming the underlying object type. |

For Wiki links, first resolve the node:

```bash
lark-cli wiki spaces get_node --params '{"token":"<wiki_node_token>"}'
```

Use these fields:
- `node.space_id`: knowledge space id.
- `node.node_token`: Wiki node token.
- `node.obj_type`: underlying object type.
- `node.obj_token`: underlying document token.
- `node.has_child`: whether recursive traversal is useful.

Only `docx` and `doc` are webified as documents. Put `sheet`, `bitable`, `slides`, `file`, and `mindnote` into the unsupported-node report.

## Fetch Single Document

Use:

```bash
lark-cli docs +fetch --doc "<doc_url_or_token>" --format json
```

For long documents, fetch with `--offset` and `--limit` when `has_more` is returned. Merge Markdown chunks in order.

Expected normalized fields:
- `title`
- `markdown`
- `source`
- `obj_type`
- `obj_token`

## Traverse Wiki Children

The local `lark-cli wiki` command may not expose child listing. Use raw OpenAPI:

```bash
lark-cli api GET "/open-apis/wiki/v2/spaces/<space_id>/nodes" \
  --params '{"parent_node_token":"<node_token>","page_size":50}'
```

Pagination:
- Add `page_token` when `data.has_more` is true.
- Continue even if `items` is empty but `has_more` is true.
- Respect the official 100 requests/minute rate limit; insert small sleeps during large traversals.

Recursive traversal:
1. Resolve the root node.
2. Fetch the root document if it is `docx/doc`.
3. List children with `parent_node_token`.
4. Fetch supported child documents.
5. Queue children whose `has_child` is true.
6. Record unsupported nodes without failing the full export.

## Media Detection

`docs +fetch` returns media tags in Markdown-like content:

```html
<image token="xxx" width="1200" height="800" align="center"/>
<view type="1"><file token="xxx" name="example.zip"/></view>
<whiteboard token="xxx"/>
```

Extract:
- `kind`: `image`, `file`, or `whiteboard`
- `token`
- `name` when present
- `width`, `height`, and `align` when present
- `doc_id` and Markdown occurrence order

Ask the user before downloading media.

Download command:

```bash
lark-cli docs +media-download --token "<token>" --output "<path>"
```

For whiteboards:

```bash
lark-cli docs +media-download --token "<token>" --type whiteboard --output "<path>"
```

If download fails, keep a placeholder in the website and write the failure into `media-manifest.json`.

## Privacy And Permissions

- Never persist or print Feishu access tokens.
- Use `lark-cli` auth rather than custom credential storage.
- If permission is denied, explain whether it is document permission, Wiki node permission, or missing app scope when the error text makes that clear.
- Do not make a private knowledge base public without explicit user confirmation.

