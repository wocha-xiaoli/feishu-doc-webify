# GitHub Pages Publishing

Use this reference before calling `scripts/publish_github_pages.sh`.

## Required Confirmation

Before publishing, ask the user for:
- Repository name.
- Visibility: `public` or `private`.

Do not infer visibility from the source document. A Feishu knowledge base may contain sensitive internal content.

## Environment Check

```bash
command -v gh
command -v git
gh auth status
```

If `gh auth status` fails, ask the user to run `gh auth login` or offer to start it.

## Public Repositories

Public GitHub Pages is the safest default for broad compatibility:

```bash
gh repo create <repo> --public --source=. --remote=origin --push
gh api -X POST /repos/<owner>/<repo>/pages -f source[branch]=main -f source[path]=/
```

If Pages already exists, update the Pages source instead of failing.

## Private Repositories

Private Pages availability depends on account and organization settings. If enabling Pages fails:
- Stop.
- Report the exact GitHub CLI/API error.
- Do not switch to public without asking.

## Verification

After publishing:
- Print the expected URL: `https://<owner>.github.io/<repo>/`.
- Check the Pages API response or HTTP availability when possible.
- Tell the user that first build can take 2-5 minutes.

## Safety

- Never commit credentials or local auth files.
- Keep generated content source-controlled only in the target Pages repository.
- Avoid force-push unless the user explicitly requests overwriting an existing site.

