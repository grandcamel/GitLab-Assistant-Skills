# GitLab-Assistant-Skills

Claude Code guidance for the GitLab-Assistant-Skills project.

## Overview

This project provides Claude Code skills for interacting with GitLab.

## CLI Tool

This project wraps the `glab` CLI tool. Skills document `glab` commands
rather than implementing custom scripts.

### Installation

See `/gitlab-assistant-setup` for installation instructions.


## Available Skills

| Skill | Purpose | Location |
|-------|---------|----------|
| `gitlab-assistant` | Hub skill - routes to specialized skills | `skills/gitlab-assistant/` |
| `gitlab-mr` | Mr operations | `skills/gitlab-mr/` |
| `gitlab-issue` | Issue operations | `skills/gitlab-issue/` |
| `gitlab-ci` | Ci operations | `skills/gitlab-ci/` |
| `gitlab-repo` | Repo operations | `skills/gitlab-repo/` |
| `gitlab-release` | Release operations | `skills/gitlab-release/` |
| `gitlab-label` | Label operations | `skills/gitlab-label/` |
| `gitlab-milestone` | Milestone operations | `skills/gitlab-milestone/` |
| `gitlab-variable` | Variable operations | `skills/gitlab-variable/` |


## Project Structure

```
GitLab-Assistant-Skills/
├── .claude-plugin/           # Plugin manifest and commands
│   ├── plugin.json          # Plugin definition
│   ├── marketplace.json     # Marketplace registry
│   └── commands/            # Slash commands
├── skills/                   # Skill documentation
│   ├── gitlab-assistant/   # Hub/router skill
│   ├── gitlab-*/           # Feature skills
│   └── shared/              # Shared docs and config
├── conftest.py              # Root test fixtures
├── pytest.ini               # Test configuration
├── VERSION                  # Single version source
└── CLAUDE.md               # This file
```

## Configuration

Configuration priority:
1. Environment variables
2. CLI configuration
3. Project defaults

## Testing

### Run Tests

```bash
# All tests
pytest skills/ -v

# Specific skill
pytest skills/gitlab-issue/tests/ -v

# Skip destructive tests
pytest skills/ -v -m "not destructive"

# Only smoke tests
pytest skills/ -v -m "smoke"
```

### Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.unit` | Unit tests (fast, no deps) |
| `@pytest.mark.live` | Live API tests |
| `@pytest.mark.destructive` | Modifies state |
| `@pytest.mark.readonly` | Read-only operations |

## Git Commit Guidelines

Follow conventional commits:

```
feat(skill-name): add new capability
fix(skill-name): correct bug in X
test(skill-name): add tests for Y (N/N passing)
docs(skill-name): update documentation
refactor(skill-name): restructure without behavior change
```

### TDD Two-Commit Pattern

1. `test(scope): add failing tests for feature` - Tests fail
2. `feat(scope): implement feature (N/N tests passing)` - Tests pass

## Risk Levels

All operations are marked with risk levels:

| Risk | Symbol | Description |
|------|:------:|-------------|
| Safe | `-` | Read-only operations |
| Caution | `⚠️` | Single-item modifications |
| Warning | `⚠️⚠️` | Bulk/destructive operations |
| Danger | `⚠️⚠️⚠️` | Irreversible operations |

## Version Management

Single source of truth: `VERSION` file

To update version:
```bash
echo "2.0.0" > VERSION
```
