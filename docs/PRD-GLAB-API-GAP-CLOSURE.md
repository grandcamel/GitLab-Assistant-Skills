# PRD: GitLab API Gap Closure via `glab api`

**Version:** 1.0.0
**Date:** 2026-01-19
**Status:** Draft
**Author:** Assistant Builder

---

## Executive Summary

The `glab` CLI covers approximately 25-30% of GitLab's REST API. This PRD defines how to extend GitLab-Assistant-Skills to close critical functionality gaps using the `glab api` escape hatch command, which allows raw API calls to any GitLab REST endpoint.

### Scope

- **In Scope:** Features addressable via `glab api` REST calls
- **Out of Scope:** GraphQL API, features requiring GitLab Premium/Ultimate only, instance admin features (require admin access)

---

## Gap Prioritization

### Priority Matrix

| Priority | Category | Business Value | Implementation Complexity | Target |
|:--------:|----------|:--------------:|:-------------------------:|--------|
| P0 | Group Management | High | Low | Phase 1 |
| P0 | Search | High | Low | Phase 1 |
| P1 | Protected Branches | High | Medium | Phase 1 |
| P1 | Webhooks | High | Medium | Phase 1 |
| P1 | Repository Files | High | Medium | Phase 1 |
| P2 | Wiki | Medium | Low | Phase 2 |
| P2 | Project Badges | Low | Low | Phase 2 |
| P2 | Discussions | Medium | Medium | Phase 2 |
| P3 | Container Registry | Medium | High | Phase 3 |
| P3 | Package Registry | Medium | High | Phase 3 |
| P3 | Security/Vulnerabilities | High | High | Phase 3 |
| P4 | User Administration | Low | Medium | Future |
| P4 | Notifications | Low | Low | Future |

---

## Phase 1: Critical Developer Workflows

### 1.1 Group Management Skill (`gitlab-group`)

**Gap:** 0% CLI coverage for group operations

**API Endpoints:**
```
GET    /groups                          # List groups
GET    /groups/:id                       # Get group details
POST   /groups                           # Create group
PUT    /groups/:id                       # Update group
DELETE /groups/:id                       # Delete group
GET    /groups/:id/subgroups             # List subgroups
GET    /groups/:id/projects              # List group projects
GET    /groups/:id/members               # List members
POST   /groups/:id/members               # Add member
PUT    /groups/:id/members/:user_id      # Update member
DELETE /groups/:id/members/:user_id      # Remove member
POST   /groups/:id/share                 # Share with group
GET    /groups/:id/variables             # List group variables
POST   /groups/:id/variables             # Create group variable
```

**Implementation Pattern:**
```bash
# List groups
glab api groups --method GET

# Get group by ID or path
glab api "groups/$(echo 'my-group' | jq -Rr @uri)" --method GET

# Create group
glab api groups --method POST -f name="My Group" -f path="my-group" -f visibility="private"

# List group members
glab api "groups/:id/members" --method GET

# Add member to group (access_level: 10=Guest, 20=Reporter, 30=Developer, 40=Maintainer, 50=Owner)
glab api "groups/:id/members" --method POST -f user_id=123 -f access_level=30

# List group variables
glab api "groups/:id/variables" --method GET

# Create group variable
glab api "groups/:id/variables" --method POST \
  -f key="API_KEY" -f value="secret" -f protected=true -f masked=true
```

**Skill Commands:**

| Operation | Risk | Command Pattern |
|-----------|:----:|-----------------|
| List groups | - | `glab api groups` |
| Get group | - | `glab api groups/:id` |
| Create group | ⚠️ | `glab api groups -X POST -f ...` |
| Update group | ⚠️ | `glab api groups/:id -X PUT -f ...` |
| Delete group | ⚠️⚠️⚠️ | `glab api groups/:id -X DELETE` |
| List members | - | `glab api groups/:id/members` |
| Add member | ⚠️ | `glab api groups/:id/members -X POST -f ...` |
| Remove member | ⚠️⚠️ | `glab api groups/:id/members/:uid -X DELETE` |
| List subgroups | - | `glab api groups/:id/subgroups` |
| List projects | - | `glab api groups/:id/projects` |
| Group variables | ⚠️ | See gitlab-variable patterns |

---

### 1.2 Search Skill (`gitlab-search`)

**Gap:** 0% dedicated CLI coverage

**API Endpoints:**
```
GET /search                              # Global search
GET /groups/:id/search                   # Group search
GET /projects/:id/search                 # Project search
```

**Search Scopes:**
- `projects` - Search projects
- `issues` - Search issues
- `merge_requests` - Search MRs
- `milestones` - Search milestones
- `snippet_titles` - Search snippets
- `wiki_blobs` - Search wiki content
- `commits` - Search commits
- `blobs` - Search file content (code search)
- `notes` - Search comments
- `users` - Search users

**Implementation Pattern:**
```bash
# Global search for projects
glab api "search?scope=projects&search=keyword" --method GET

# Search issues globally
glab api "search?scope=issues&search=bug+login" --method GET

# Search code (blobs) globally
glab api "search?scope=blobs&search=function+authenticate" --method GET

# Project-scoped code search
glab api "projects/:id/search?scope=blobs&search=TODO" --method GET

# Group-scoped issue search
glab api "groups/:id/search?scope=issues&search=urgent" --method GET

# Search with pagination
glab api "search?scope=issues&search=bug&per_page=50&page=1" --method GET
```

**Skill Commands:**

| Operation | Risk | Command Pattern |
|-----------|:----:|-----------------|
| Search projects | - | `glab api "search?scope=projects&search=..."` |
| Search issues | - | `glab api "search?scope=issues&search=..."` |
| Search MRs | - | `glab api "search?scope=merge_requests&search=..."` |
| Search code | - | `glab api "search?scope=blobs&search=..."` |
| Search commits | - | `glab api "search?scope=commits&search=..."` |
| Search wiki | - | `glab api "search?scope=wiki_blobs&search=..."` |
| Search users | - | `glab api "search?scope=users&search=..."` |
| Project search | - | `glab api "projects/:id/search?scope=...&search=..."` |
| Group search | - | `glab api "groups/:id/search?scope=...&search=..."` |

---

### 1.3 Protected Branches Skill (`gitlab-protected-branch`)

**Gap:** Not covered by CLI

**API Endpoints:**
```
GET    /projects/:id/protected_branches              # List
GET    /projects/:id/protected_branches/:name        # Get
POST   /projects/:id/protected_branches              # Create
PATCH  /projects/:id/protected_branches/:name        # Update
DELETE /projects/:id/protected_branches/:name        # Delete
```

**Access Levels:**
- 0 = No access
- 30 = Developer
- 40 = Maintainer
- 60 = Admin (instance)

**Implementation Pattern:**
```bash
# List protected branches
glab api "projects/:id/protected_branches" --method GET

# Get specific protected branch
glab api "projects/:id/protected_branches/main" --method GET

# Protect a branch (developers can merge, maintainers can push)
glab api "projects/:id/protected_branches" --method POST \
  -f name="main" \
  -f push_access_level=40 \
  -f merge_access_level=30 \
  -f allow_force_push=false

# Protect with code owner approval required
glab api "projects/:id/protected_branches" --method POST \
  -f name="release/*" \
  -f push_access_level=40 \
  -f merge_access_level=40 \
  -f code_owner_approval_required=true

# Unprotect branch
glab api "projects/:id/protected_branches/feature%2F*" --method DELETE
```

**Skill Commands:**

| Operation | Risk | Command Pattern |
|-----------|:----:|-----------------|
| List protected | - | `glab api projects/:id/protected_branches` |
| Get protection | - | `glab api projects/:id/protected_branches/:name` |
| Protect branch | ⚠️ | `glab api projects/:id/protected_branches -X POST -f ...` |
| Update protection | ⚠️ | `glab api projects/:id/protected_branches/:name -X PATCH -f ...` |
| Unprotect branch | ⚠️⚠️ | `glab api projects/:id/protected_branches/:name -X DELETE` |

---

### 1.4 Webhooks Skill (`gitlab-webhook`)

**Gap:** 0% CLI coverage

**API Endpoints:**
```
GET    /projects/:id/hooks                # List webhooks
GET    /projects/:id/hooks/:hook_id       # Get webhook
POST   /projects/:id/hooks                # Create webhook
PUT    /projects/:id/hooks/:hook_id       # Update webhook
DELETE /projects/:id/hooks/:hook_id       # Delete webhook
POST   /projects/:id/hooks/:hook_id/test/:trigger  # Test webhook
```

**Webhook Events:**
- `push_events`, `tag_push_events`
- `merge_requests_events`, `issues_events`
- `note_events`, `confidential_note_events`
- `job_events`, `pipeline_events`, `deployment_events`
- `wiki_page_events`, `releases_events`

**Implementation Pattern:**
```bash
# List project webhooks
glab api "projects/:id/hooks" --method GET

# Create webhook for push and MR events
glab api "projects/:id/hooks" --method POST \
  -f url="https://example.com/webhook" \
  -f push_events=true \
  -f merge_requests_events=true \
  -f token="secret-token" \
  -f enable_ssl_verification=true

# Create webhook for pipeline events
glab api "projects/:id/hooks" --method POST \
  -f url="https://slack.com/webhook" \
  -f pipeline_events=true \
  -f job_events=true

# Update webhook
glab api "projects/:id/hooks/:hook_id" --method PUT \
  -f push_events=false

# Delete webhook
glab api "projects/:id/hooks/:hook_id" --method DELETE

# Test webhook (trigger: push_events, tag_push_events, note_events, etc.)
glab api "projects/:id/hooks/:hook_id/test/push_events" --method POST
```

**Skill Commands:**

| Operation | Risk | Command Pattern |
|-----------|:----:|-----------------|
| List webhooks | - | `glab api projects/:id/hooks` |
| Get webhook | - | `glab api projects/:id/hooks/:hook_id` |
| Create webhook | ⚠️ | `glab api projects/:id/hooks -X POST -f ...` |
| Update webhook | ⚠️ | `glab api projects/:id/hooks/:hook_id -X PUT -f ...` |
| Delete webhook | ⚠️⚠️ | `glab api projects/:id/hooks/:hook_id -X DELETE` |
| Test webhook | ⚠️ | `glab api projects/:id/hooks/:hook_id/test/:trigger -X POST` |

---

### 1.5 Repository Files Skill (`gitlab-file`)

**Gap:** Limited CLI coverage

**API Endpoints:**
```
GET    /projects/:id/repository/files/:file_path     # Get file
POST   /projects/:id/repository/files/:file_path     # Create file
PUT    /projects/:id/repository/files/:file_path     # Update file
DELETE /projects/:id/repository/files/:file_path     # Delete file
GET    /projects/:id/repository/files/:file_path/raw # Get raw content
GET    /projects/:id/repository/files/:file_path/blame # Get blame
```

**Implementation Pattern:**
```bash
# Get file info (base64 encoded content)
glab api "projects/:id/repository/files/src%2Fmain.py?ref=main" --method GET

# Get raw file content
glab api "projects/:id/repository/files/README.md/raw?ref=main" --method GET

# Create new file
glab api "projects/:id/repository/files/docs%2Fnew-file.md" --method POST \
  -f branch="main" \
  -f content="$(base64 < new-file.md)" \
  -f encoding="base64" \
  -f commit_message="Add new documentation file"

# Update file (requires providing content)
glab api "projects/:id/repository/files/README.md" --method PUT \
  -f branch="main" \
  -f content="$(base64 < README.md)" \
  -f encoding="base64" \
  -f commit_message="Update README"

# Delete file
glab api "projects/:id/repository/files/old-file.txt" --method DELETE \
  -f branch="main" \
  -f commit_message="Remove deprecated file"

# Get file blame
glab api "projects/:id/repository/files/src%2Fapp.py/blame?ref=main" --method GET
```

**Skill Commands:**

| Operation | Risk | Command Pattern |
|-----------|:----:|-----------------|
| Get file | - | `glab api projects/:id/repository/files/:path?ref=:branch` |
| Get raw | - | `glab api projects/:id/repository/files/:path/raw?ref=:branch` |
| Create file | ⚠️ | `glab api projects/:id/repository/files/:path -X POST -f ...` |
| Update file | ⚠️ | `glab api projects/:id/repository/files/:path -X PUT -f ...` |
| Delete file | ⚠️⚠️ | `glab api projects/:id/repository/files/:path -X DELETE -f ...` |
| Get blame | - | `glab api projects/:id/repository/files/:path/blame?ref=:branch` |

---

## Phase 2: Collaboration Features

### 2.1 Wiki Skill (`gitlab-wiki`)

**Gap:** 0% CLI coverage

**API Endpoints:**
```
GET    /projects/:id/wikis                # List pages
GET    /projects/:id/wikis/:slug          # Get page
POST   /projects/:id/wikis                # Create page
PUT    /projects/:id/wikis/:slug          # Update page
DELETE /projects/:id/wikis/:slug          # Delete page
POST   /projects/:id/wikis/attachments    # Upload attachment
```

**Implementation Pattern:**
```bash
# List wiki pages
glab api "projects/:id/wikis" --method GET

# Get specific page
glab api "projects/:id/wikis/home" --method GET

# Create wiki page
glab api "projects/:id/wikis" --method POST \
  -f title="Getting Started" \
  -f content="# Getting Started\n\nWelcome to the project!" \
  -f format="markdown"

# Update wiki page
glab api "projects/:id/wikis/getting-started" --method PUT \
  -f title="Getting Started Guide" \
  -f content="# Updated content..."

# Delete wiki page
glab api "projects/:id/wikis/old-page" --method DELETE
```

---

### 2.2 Discussions/Threads Skill (`gitlab-discussion`)

**Gap:** Limited coverage

**API Endpoints:**
```
# Issue discussions
GET    /projects/:id/issues/:iid/discussions
POST   /projects/:id/issues/:iid/discussions
GET    /projects/:id/issues/:iid/discussions/:discussion_id
PUT    /projects/:id/issues/:iid/discussions/:discussion_id

# MR discussions
GET    /projects/:id/merge_requests/:iid/discussions
POST   /projects/:id/merge_requests/:iid/discussions
PUT    /projects/:id/merge_requests/:iid/discussions/:discussion_id/notes/:note_id
POST   /projects/:id/merge_requests/:iid/discussions/:discussion_id/notes/:note_id/resolve
```

**Implementation Pattern:**
```bash
# List MR discussions
glab api "projects/:id/merge_requests/:iid/discussions" --method GET

# Create new discussion on MR (optionally on specific line)
glab api "projects/:id/merge_requests/:iid/discussions" --method POST \
  -f body="This needs refactoring" \
  -f position[base_sha]="abc123" \
  -f position[head_sha]="def456" \
  -f position[start_sha]="abc123" \
  -f position[position_type]="text" \
  -f position[new_path]="src/app.py" \
  -f position[new_line]=42

# Resolve a discussion thread
glab api "projects/:id/merge_requests/:iid/discussions/:discussion_id" --method PUT \
  -f resolved=true

# Reply to a discussion
glab api "projects/:id/merge_requests/:iid/discussions/:discussion_id/notes" --method POST \
  -f body="Good point, I'll fix this."
```

---

### 2.3 Project Badges Skill (`gitlab-badge`)

**Gap:** 0% CLI coverage

**API Endpoints:**
```
GET    /projects/:id/badges               # List badges
GET    /projects/:id/badges/:badge_id     # Get badge
POST   /projects/:id/badges               # Create badge
PUT    /projects/:id/badges/:badge_id     # Update badge
DELETE /projects/:id/badges/:badge_id     # Delete badge
GET    /projects/:id/badges/render        # Preview badge
```

**Implementation Pattern:**
```bash
# List project badges
glab api "projects/:id/badges" --method GET

# Create pipeline status badge
glab api "projects/:id/badges" --method POST \
  -f link_url="https://gitlab.com/%{project_path}/-/pipelines" \
  -f image_url="https://gitlab.com/%{project_path}/badges/%{default_branch}/pipeline.svg"

# Create coverage badge
glab api "projects/:id/badges" --method POST \
  -f link_url="https://gitlab.com/%{project_path}/-/jobs" \
  -f image_url="https://gitlab.com/%{project_path}/badges/%{default_branch}/coverage.svg"

# Preview badge rendering
glab api "projects/:id/badges/render?link_url=...&image_url=..." --method GET

# Delete badge
glab api "projects/:id/badges/:badge_id" --method DELETE
```

---

## Phase 3: DevOps & Security

### 3.1 Container Registry Skill (`gitlab-container`)

**Gap:** 0% CLI coverage

**API Endpoints:**
```
GET    /projects/:id/registry/repositories                    # List repos
GET    /projects/:id/registry/repositories/:repo_id           # Get repo
DELETE /projects/:id/registry/repositories/:repo_id           # Delete repo
GET    /projects/:id/registry/repositories/:repo_id/tags      # List tags
GET    /projects/:id/registry/repositories/:repo_id/tags/:tag # Get tag
DELETE /projects/:id/registry/repositories/:repo_id/tags/:tag # Delete tag
DELETE /projects/:id/registry/repositories/:repo_id/tags      # Bulk delete tags
```

**Implementation Pattern:**
```bash
# List container repositories
glab api "projects/:id/registry/repositories" --method GET

# List tags in repository
glab api "projects/:id/registry/repositories/:repo_id/tags" --method GET

# Get specific tag details
glab api "projects/:id/registry/repositories/:repo_id/tags/latest" --method GET

# Delete specific tag
glab api "projects/:id/registry/repositories/:repo_id/tags/v1.0.0" --method DELETE

# Bulk delete tags matching regex (keep last 5)
glab api "projects/:id/registry/repositories/:repo_id/tags" --method DELETE \
  -f name_regex_delete=".*" \
  -f keep_n=5

# Delete old tags (older than 30 days, keep 10)
glab api "projects/:id/registry/repositories/:repo_id/tags" --method DELETE \
  -f name_regex_delete=".*" \
  -f keep_n=10 \
  -f older_than="30d"
```

---

### 3.2 Vulnerabilities Skill (`gitlab-vulnerability`)

**Gap:** 0% CLI coverage (requires Ultimate)

**API Endpoints:**
```
GET    /projects/:id/vulnerabilities                    # List vulnerabilities
GET    /projects/:id/vulnerabilities/:id                # Get vulnerability
POST   /projects/:id/vulnerabilities/:id/confirm        # Confirm
POST   /projects/:id/vulnerabilities/:id/dismiss        # Dismiss
POST   /projects/:id/vulnerabilities/:id/resolve        # Resolve
GET    /projects/:id/vulnerability_findings             # List findings
GET    /security/projects                               # Security dashboard
```

**Implementation Pattern:**
```bash
# List project vulnerabilities
glab api "projects/:id/vulnerabilities?state=detected" --method GET

# Get vulnerability details
glab api "projects/:id/vulnerabilities/:vuln_id" --method GET

# Dismiss vulnerability with reason
glab api "projects/:id/vulnerabilities/:vuln_id/dismiss" --method POST \
  -f comment="False positive - not exploitable in our context"

# Confirm vulnerability
glab api "projects/:id/vulnerabilities/:vuln_id/confirm" --method POST

# Resolve vulnerability
glab api "projects/:id/vulnerabilities/:vuln_id/resolve" --method POST

# List vulnerability findings (from scanners)
glab api "projects/:id/vulnerability_findings?severity=critical,high" --method GET
```

---

## Implementation Guidelines

### Helper Functions

Create reusable shell functions for common patterns:

```bash
# URL-encode a path
gitlab_encode() {
  echo "$1" | jq -Rr @uri
}

# Get current project ID
gitlab_project_id() {
  glab api "projects/$(gitlab_encode "$(git remote get-url origin | sed 's|.*gitlab.com[:/]||;s|\.git$||')")" | jq -r '.id'
}

# Paginated API call
gitlab_api_all() {
  local endpoint="$1"
  local page=1
  local results="[]"
  while true; do
    local response=$(glab api "${endpoint}${endpoint:+&}per_page=100&page=${page}" 2>/dev/null)
    if [ "$(echo "$response" | jq 'length')" -eq 0 ]; then
      break
    fi
    results=$(echo "$results" "$response" | jq -s 'add')
    ((page++))
  done
  echo "$results"
}
```

### Error Handling

```bash
# Safe API call with error handling
gitlab_api_safe() {
  local response
  local http_code

  response=$(glab api "$@" 2>&1)

  if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
    echo "Error: $(echo "$response" | jq -r '.error // .message')" >&2
    return 1
  fi

  echo "$response"
}
```

### JSON Output Formatting

```bash
# Pretty table output from JSON
gitlab_table() {
  jq -r '(.[0] | keys_unsorted) as $keys | $keys, map([.[ $keys[] ]])[] | @tsv' | column -t
}

# Usage
glab api "groups" | gitlab_table
```

---

## New Skills Summary

| Skill | Priority | Phase | Operations |
|-------|:--------:|:-----:|------------|
| `gitlab-group` | P0 | 1 | CRUD groups, members, subgroups, sharing |
| `gitlab-search` | P0 | 1 | Global, group, project search across scopes |
| `gitlab-protected-branch` | P1 | 1 | Branch protection rules |
| `gitlab-webhook` | P1 | 1 | CRUD webhooks, test triggers |
| `gitlab-file` | P1 | 1 | Repository file operations |
| `gitlab-wiki` | P2 | 2 | Wiki page CRUD |
| `gitlab-discussion` | P2 | 2 | Threaded discussions on MRs/issues |
| `gitlab-badge` | P2 | 2 | Project badges |
| `gitlab-container` | P3 | 3 | Container registry management |
| `gitlab-vulnerability` | P3 | 3 | Security vulnerability management |

---

## Success Metrics

1. **Coverage Improvement:** Increase from 25-30% to 60%+ API coverage
2. **User Adoption:** Track skill usage via feedback
3. **Error Rate:** < 5% API call failures
4. **Documentation:** 100% of `glab api` patterns documented with examples

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API changes break patterns | Medium | Pin to API v4, document version requirements |
| Complex JSON handling | Medium | Provide jq helper patterns |
| Auth token scope issues | High | Document required scopes per operation |
| Rate limiting | Medium | Implement pagination helpers, caching guidance |
| Premium/Ultimate features | Medium | Clearly mark tier requirements |

---

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | 2 weeks | 5 core skills (group, search, protected-branch, webhook, file) |
| Phase 2 | 2 weeks | 3 collaboration skills (wiki, discussion, badge) |
| Phase 3 | 3 weeks | 2 DevOps skills (container, vulnerability) |

---

## Appendix: `glab api` Reference

### Basic Syntax

```bash
glab api <endpoint> [flags]
```

### Common Flags

| Flag | Description |
|------|-------------|
| `-X, --method` | HTTP method (GET, POST, PUT, PATCH, DELETE) |
| `-f, --field` | Add field to request body (key=value) |
| `-F, --raw-field` | Add raw field (no JSON escaping) |
| `-H, --header` | Add HTTP header |
| `--hostname` | Target specific GitLab instance |
| `-i, --include` | Include HTTP response headers |
| `--paginate` | Auto-paginate results |
| `-q, --quiet` | Suppress output |

### Examples

```bash
# GET request
glab api projects/123

# POST with fields
glab api projects/123/issues -X POST -f title="Bug" -f description="Details"

# PUT/PATCH
glab api projects/123/issues/1 -X PUT -f state_event="close"

# DELETE
glab api projects/123/issues/1 -X DELETE

# With pagination
glab api projects --paginate | jq '.[].name'

# Custom header
glab api projects -H "Private-Token: xxx"

# Different GitLab instance
glab api projects --hostname gitlab.company.com
```

---

## References

- [GitLab REST API Documentation](https://docs.gitlab.com/ee/api/rest/)
- [GitLab API Resources](https://docs.gitlab.com/ee/api/api_resources.html)
- [glab api Command](https://gitlab.com/gitlab-org/cli/-/blob/main/docs/source/api/index.md)
- [Gap Analysis Document](/Users/jasonkrueger/docs/glab-gitlab-api-gap-analysis.md)
