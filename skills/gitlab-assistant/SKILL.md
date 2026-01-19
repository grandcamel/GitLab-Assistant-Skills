---
name: "gitlab-assistant"
description: "GitLab automation hub. Routes requests to specialized skills. ALWAYS use this skill when: (1) any GitLab operation, (2) unsure which skill to use, (3) multi-step GitLab workflows. Start here for any gitlab task."
version: "1.0.0"
author: "GitLab-Assistant-Skills"
license: "MIT"
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# GitLab Assistant

Central hub for GitLab automation using the `glab` CLI. Routes requests to the most appropriate specialized skill.

## Quick Reference

| I want to... | Use this skill | Risk |
|--------------|----------------|:----:|
| Work with merge requests | `gitlab-mr` | ⚠️ |
| Work with issues | `gitlab-issue` | ⚠️ |
| Check/run CI pipelines | `gitlab-ci` | ⚠️ |
| Clone/fork/create repos | `gitlab-repo` | ⚠️ |
| Manage releases | `gitlab-release` | ⚠️ |
| Manage labels | `gitlab-label` | ⚠️ |
| Manage milestones | `gitlab-milestone` | ⚠️ |
| Manage CI/CD variables | `gitlab-variable` | ⚠️ |

**Risk Legend**: - Safe | ⚠️ Caution | ⚠️⚠️ Warning | ⚠️⚠️⚠️ Danger

## Routing Rules

### Rule 1: Explicit Resource Type

Route based on the GitLab resource being worked with:

| Keywords | Route to |
|----------|----------|
| MR, merge request, pull request, review, approve, merge | `gitlab-mr` |
| issue, bug, ticket, task, feature request | `gitlab-issue` |
| CI, CD, pipeline, build, job, deploy, artifacts | `gitlab-ci` |
| repo, repository, project, clone, fork | `gitlab-repo` |
| release, tag, version, changelog | `gitlab-release` |
| label, tag (for issues/MRs) | `gitlab-label` |
| milestone, sprint, iteration | `gitlab-milestone` |
| variable, secret, env, CI variable | `gitlab-variable` |

### Rule 2: Common Workflows

| Workflow | Skills Involved |
|----------|-----------------|
| Code review | `gitlab-mr` (checkout, review, approve, merge) |
| Bug tracking | `gitlab-issue` (create, assign, close) |
| Deployment | `gitlab-ci` (run, status, artifacts) |
| Release process | `gitlab-release` + `gitlab-ci` |
| Project setup | `gitlab-repo` (create, clone) |

### Rule 3: Multi-Step Operations

For complex workflows that span multiple skills, coordinate them:

```
Example: "Release version 1.2.0"
1. gitlab-mr: Ensure all MRs are merged
2. gitlab-ci: Verify pipeline passes
3. gitlab-release: Create release with changelog
```

## Skills Overview

### gitlab-mr (Merge Requests)

- **Purpose**: Create, review, approve, and merge MRs
- **Key commands**: `glab mr list`, `glab mr create`, `glab mr checkout`, `glab mr merge`
- **Risk**: ⚠️ (merge is destructive)
- **Triggers**: MR, merge request, review, approve, merge, checkout

### gitlab-issue (Issues)

- **Purpose**: Track bugs, features, and tasks
- **Key commands**: `glab issue list`, `glab issue create`, `glab issue close`
- **Risk**: ⚠️ (close/delete are destructive)
- **Triggers**: issue, bug, task, ticket, feature

### gitlab-ci (CI/CD Pipelines)

- **Purpose**: View, trigger, and manage CI/CD pipelines
- **Key commands**: `glab ci status`, `glab ci view`, `glab ci run`, `glab ci artifact`
- **Risk**: ⚠️ (run triggers compute resources)
- **Triggers**: CI, pipeline, build, job, deploy, artifacts, lint

### gitlab-repo (Repositories)

- **Purpose**: Clone, fork, create, and manage repositories
- **Key commands**: `glab repo clone`, `glab repo fork`, `glab repo create`
- **Risk**: ⚠️⚠️ (delete is highly destructive)
- **Triggers**: repo, repository, project, clone, fork

### gitlab-release (Releases)

- **Purpose**: Create and manage releases
- **Key commands**: `glab release create`, `glab release list`, `glab release view`
- **Risk**: ⚠️ (creates tags and releases)
- **Triggers**: release, version, changelog, tag

### gitlab-label (Labels)

- **Purpose**: Manage project labels
- **Key commands**: `glab label create`, `glab label list`
- **Risk**: ⚠️ (affects issue/MR categorization)
- **Triggers**: label, tag (for categorization)

### gitlab-milestone (Milestones)

- **Purpose**: Manage project milestones
- **Key commands**: `glab milestone create`, `glab milestone list`
- **Risk**: ⚠️ (affects planning)
- **Triggers**: milestone, sprint, iteration

### gitlab-variable (CI/CD Variables)

- **Purpose**: Manage CI/CD variables and secrets
- **Key commands**: `glab variable set`, `glab variable list`
- **Risk**: ⚠️⚠️ (contains secrets)
- **Triggers**: variable, secret, env var, CI variable

## Connection Verification

Before any operation, verify GitLab is configured:

```bash
glab auth status
```

If not authenticated:
```bash
glab auth login
```

Check current repository context:
```bash
glab repo view
```

## Common glab Commands Quick Reference

```bash
# Authentication
glab auth login              # Interactive login
glab auth status             # Check auth status

# Merge Requests
glab mr list                 # List MRs
glab mr create               # Create MR
glab mr view <id>            # View MR details
glab mr checkout <id>        # Checkout MR branch
glab mr merge <id>           # Merge MR

# Issues
glab issue list              # List issues
glab issue create            # Create issue
glab issue view <id>         # View issue
glab issue close <id>        # Close issue

# CI/CD
glab ci status               # Current pipeline status
glab ci view                 # Interactive pipeline view
glab ci run                  # Trigger pipeline
glab ci artifact             # Download artifacts

# Repository
glab repo clone <path>       # Clone repository
glab repo fork <path>        # Fork repository
glab repo view               # View repo info
```

## Disambiguation

When request is ambiguous, ask for clarification:

| Ambiguous Request | Clarifying Question |
|-------------------|---------------------|
| "Show me the status" | "Do you want CI pipeline status (`glab ci status`) or MR status (`glab mr list`)?" |
| "Create a new one" | "What would you like to create? An issue, MR, or repository?" |
| "List everything" | "What would you like to list? MRs, issues, pipelines, or repos?" |

## Related Documentation

- [Decision Tree](./docs/DECISION_TREE.md)
- [Safeguards](../shared/docs/SAFEGUARDS.md)
- [Quick Reference](../shared/docs/QUICK_REFERENCE.md)
