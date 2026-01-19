---
description: "Set up GitLab Assistant Skills with credentials and configuration"
user_invocable: true
arguments:
  - name: profile
    description: "Configuration profile name"
    required: false
    default: "default"
---

# GitLab Assistant Setup

Set up GitLab Assistant Skills for Claude Code.

## Prerequisites

Install the glab CLI:

```bash
brew install glab
```

## Authentication

Authenticate with GitLab:

```bash
glab auth login
```

## Verification

Verify your setup:

```bash
glab auth status
```

## Configuration

Configuration is stored in your glab CLI config.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Auth failed | Run `glab auth login` again |
| CLI not found | Verify installation: `which glab` |
| Permission denied | Check your GitLab permissions |
