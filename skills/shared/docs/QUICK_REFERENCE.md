# Quick Reference

## Authentication

```bash
# Check auth status
glab auth status

# Login interactively
glab auth login

# Login to specific host
glab auth login --hostname gitlab.example.com
```

## Merge Requests

```bash
# List MRs
glab mr list
glab mr list --assignee=@me
glab mr list --reviewer=@me
glab mr list --state=merged

# View MR
glab mr view <id>
glab mr view <id> --web
glab mr view <id> --comments

# Create MR
glab mr create
glab mr create -t "Title" -d "Description"
glab mr create --fill --draft

# Checkout MR branch
glab mr checkout <id>
glab co <id>  # shortcut

# Approve/Merge
glab mr approve <id>
glab mr merge <id>
glab mr merge <id> --squash
```

## Issues

```bash
# List issues
glab issue list
glab issue list --assignee=@me
glab issue list --label=bug
glab issue list --milestone="Sprint 1"

# View issue
glab issue view <id>
glab issue view <id> --web

# Create issue
glab issue create
glab issue create -t "Title" -d "Description" -l "bug,priority"

# Manage issues
glab issue close <id>
glab issue reopen <id>
glab issue note <id> -m "Comment"
```

## CI/CD Pipelines

```bash
# View status
glab ci status
glab ci status --live
glab ci status --branch=main

# Interactive view
glab ci view
glab ci view --web

# List pipelines
glab ci list
glab ci list --status=failed

# Run pipeline
glab ci run
glab ci run --branch=main
glab ci run --variables="KEY=value"

# Jobs and artifacts
glab ci retry <job-id>
glab ci trace <job-id>
glab ci artifact --job=build

# Validate config
glab ci lint
```

## Repository

```bash
# Clone
glab repo clone owner/repo
glab repo clone owner/repo my-dir
glab repo clone -g mygroup --paginate

# Fork
glab repo fork owner/repo
glab repo fork owner/repo --clone

# View
glab repo view
glab repo view --web

# Create
glab repo create my-project
glab repo create my-project --public --readme --clone

# Search
glab repo search "query"
```

## Releases

```bash
# List releases
glab release list

# View release
glab release view <tag>

# Create release
glab release create <tag>
glab release create v1.0.0 -n "Release notes"
```

## Labels

```bash
# List labels
glab label list

# Create label
glab label create <name> -c <color>
glab label create "bug" -c "#ff0000" -d "Bug reports"
```

## CI/CD Variables

```bash
# List variables
glab variable list

# Set variable
glab variable set <key> <value>
glab variable set API_KEY "secret" --masked

# Delete variable
glab variable delete <key>
```

## Common Flags

| Flag | Description |
|------|-------------|
| `-w, --web` | Open in browser |
| `-y, --yes` | Skip confirmation |
| `-P, --per-page` | Results per page |
| `--all` | Get all results |
| `-b, --branch` | Specify branch |

## Output Formats

Most commands support JSON output for scripting:

```bash
glab mr list --output json | jq '.[0].title'
glab ci get | jq '.status'
```

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 401 | Auth failed | Run `glab auth login` |
| 403 | Permission denied | Check access rights |
| 404 | Not found | Verify ID/path |
| 429 | Rate limited | Wait and retry |
| 5xx | Server error | Check GitLab status |

## Useful Aliases

Add to your shell config:

```bash
alias gl='glab'
alias glmr='glab mr'
alias glci='glab ci'
alias glco='glab mr checkout'
```
