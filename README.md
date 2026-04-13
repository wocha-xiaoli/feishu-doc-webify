# Feishu Doc Webify

把沉重的飞书文档和知识库，变成一个真正值得分享的网页。

飞书很适合写知识库，但不擅长做“对外展示”。排版受限、视觉平、导航弱，长文越多越像一堵墙。`feishu-doc-webify` 是一个 Skill：给它一个飞书 `docx`、`doc` 或 `wiki` 链接，它会抓取内容、保留结构、重新排成精美静态网站，并发布到 GitHub Pages。

适合这些场景：

- 你有一套飞书知识库，想变成一个公开文档站。
- 你写了很重的方案、教程、方法论，飞书排版已经装不下它的野心。
- 你想把内部文档整理成客户能看的网页，而不是发一个飞书链接。
- 你想让 AI 帮你做“内容网页化”，但又不想每次从零写抓取、排版、发布脚本。

复制这句就能开始：

```text
用 feishu-doc-webify，把这个飞书 Wiki 做成一个精美知识库网站，并发布到 GitHub Pages：<你的飞书链接>
```

## Before / After

Before:

- 飞书链接只能在飞书里读。
- 长文没有像样的目录和阅读节奏。
- 对外分享时像“临时发了个文档”。
- 每次发布都要手动处理内容、媒体、HTML 和 GitHub Pages。

After:

- 一个可以直接访问的静态网站。
- 文档层级、目录、搜索、阅读进度都在。
- 图片和画板可本地化，附件可按需处理。
- 发布前确认公开/私有，避免误公开内部资料。

## 它能做什么

`feishu-doc-webify` 会引导 Codex 完成一条完整流水线：

1. 读取飞书文档或 Wiki 链接。
2. 用 `lark-cli` 抓取正文、标题、层级和媒体标记。
3. 检测图片、附件、画板，询问是否下载本地化。
4. 生成静态 HTML/CSS/JS 网站。
5. 本地预览，继续打磨排版。
6. 发布到 GitHub Pages。

默认输出是一个“知识库阅读型 editorial”网站：

- 清晰目录
- 章节锚点
- 阅读进度条
- 宽屏双栏阅读
- 移动端单栏适配
- 表格横向滚动
- 代码块高对比展示
- Wiki 多页站点搜索索引
- 媒体缺失时显示占位，不让页面破掉

## 为什么不是简单导出 HTML

飞书导出解决的是“带走内容”，不是“让内容好看、好读、好传播”。

这个 Skill 更像一个文档出版助理：

- **保真美化**：默认保留全部原文、标题层级、列表、表格、引用、代码块和图片位置，只重做网页阅读体验。
- **智能重组**：用户明确要求时，可以增加导读、摘要、专题卡片和章节导航，但不会删除原文。
- **单篇和知识库都能处理**：单篇文档生成 `index.html`；Wiki 子树生成首页、多篇文档页面和搜索索引。
- **发布前保护隐私**：每次发布前都必须确认仓库名和公开/私有，不会偷偷把内部知识库变成公开站点。

## 安装（或者其他agent都可以）

### Codex

```bash
git clone https://github.com/wocha-xiaoli/feishu-doc-webify.git \
  ~/.codex/skills/feishu-doc-webify
```

重启 Codex 后即可使用。

```

## 前置条件

这不是一个独立 SaaS，它使用你本机已有的飞书和 GitHub CLI 权限。

需要安装：

| 工具 | 用途 |
| --- | --- |
| `lark-cli` | 读取飞书文档、Wiki、媒体 |
| `gh` | 创建仓库、发布 GitHub Pages |
| `git` | 提交和推送静态网站 |
| `python3` | 运行抓取和建站脚本 |

建议先确认登录：

```bash
lark-cli whoami
gh auth status
```

如果没有登录，先完成：

```bash
lark-cli login
gh auth login
```

## 怎么用

在 Codex / OpenCode/claude code 里直接说：

```text
用 feishu-doc-webify，把这个飞书文档网页化：
https://example.feishu.cn/docx/xxxx
```

或者：

```text
把这个飞书 Wiki 子树做成一个精美知识库网站，并发布到 GitHub Pages：
https://example.feishu.cn/wiki/xxxx
```

你也可以指定风格和内容策略：

```text
用 feishu-doc-webify，把这个飞书知识库做成公开网站。
默认保留原文，但首页做成更像产品文档的导读。
媒体先检测数量，图片下载本地化，附件先跳过。
```

## 典型流程

Skill 会让 Codex 按这个顺序工作：

```bash
# 1. 抓取单篇文档或 Wiki 子树
python3 scripts/fetch_feishu_content.py \
  --source "https://example.feishu.cn/wiki/xxxx" \
  --scope wiki \
  --out ./feishu-webify-export

# 2. 如用户确认，下载文档媒体
python3 scripts/download_media.py \
  --manifest ./feishu-webify-export/media-manifest.json \
  --out ./feishu-webify-export/site/media

# 3. 生成静态网站
python3 scripts/build_static_site.py \
  --content ./feishu-webify-export/content.json \
  --mode faithful \
  --style editorial \
  --out ./feishu-webify-export/site

# 4. 本地预览
open ./feishu-webify-export/site/index.html

# 5. 用户确认公开性后发布
bash scripts/publish_github_pages.sh \
  --site-dir ./feishu-webify-export/site \
  --repo my-knowledge-site \
  --visibility public
```

正常使用时，你不需要手动敲这些命令。Skill 会让 Codex 替你执行，并在关键节点询问确认。

## 生成物

单篇文档：

```text
site/
├── index.html
├── styles.css
├── app.js
├── search-index.json
└── media/
```

Wiki 知识库：

```text
site/
├── index.html
├── docs/
│   ├── chapter-1.html
│   └── chapter-2.html
├── styles.css
├── app.js
├── search-index.json
└── media/
```

抓取阶段还会生成：

```text
feishu-webify-export/
├── content.json
├── media-manifest.json
└── fetch-report.json
```

这些文件方便排查哪些文档被成功纳入、哪些 Wiki 节点暂不支持、哪些媒体下载失败。

## 支持范围

当前支持：

- 飞书新版文档：`/docx/`
- 飞书旧版文档：`/doc/`
- 飞书知识库节点：`/wiki/`
- Wiki 子节点递归抓取
- 图片、附件、画板识别
- 图片/附件/画板按需下载
- GitHub Pages 发布

暂不直接网页化：

- 飞书表格 `sheet`
- 多维表格 `bitable`
- 幻灯片 `slides`
- 思维导图 `mindnote`
- 普通文件节点

这些节点会进入 `fetch-report.json` 的 skipped list，不会让整个网站生成失败。

## 隐私与安全

这个 Skill 默认比较谨慎：

- 不保存飞书 access token。
- 不读取浏览器 cookie。
- 不读取 `~/.ssh`、`~/.aws` 等敏感目录。
- 不硬编码 API Key。
- 飞书认证交给 `lark-cli`。
- GitHub 认证交给 `gh`。
- 发布前必须确认仓库公开性。
- 私有 GitHub Pages 失败时不会自动改成公开。

但你仍然要注意：如果你选择发布到公开 GitHub Pages，网页内容就是公开的。内部文档、客户资料、未发布战略，请先脱敏。

## 目录结构

```text
feishu-doc-webify/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── editorial-theme.css
├── references/
│   ├── github-pages.md
│   ├── lark-doc-pipeline.md
│   └── web-design-patterns.md
└── scripts/
    ├── build_static_site.py
    ├── download_media.py
    ├── fetch_feishu_content.py
    └── publish_github_pages.sh
```

## 给谁用

给那些“内容已经很强，但飞书排版搞不定”的人：

- 创始人写方法论
- 咨询顾问交付知识库
- AI 创作者整理教程
- 团队把内部 SOP 转成外部文档站
- 个人把飞书沉淀变成公开作品集

你写内容，飞书承载协作，`feishu-doc-webify` 负责把它变成一个像样的网站。

## License

MIT
