# API Helpers

Common patterns for using `glab api` to access GitLab REST API endpoints.

## Basic Syntax

```bash
glab api <endpoint> [flags]
```

## Common Flags

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

## URL Encoding

Paths containing slashes or special characters must be URL-encoded:

```bash
# URL-encode a path using jq
glab api "projects/$(echo 'my-group/my-project' | jq -Rr @uri)" --method GET

# URL-encode branch names with slashes
glab api "projects/:id/protected_branches/$(echo 'feature/branch' | jq -Rr @uri)"
```

### Common Encodings

| Character | Encoded |
|-----------|---------|
| `/` | `%2F` |
| ` ` (space) | `%20` |
| `@` | `%40` |
| `#` | `%23` |
| `?` | `%3F` |
| `&` | `%26` |

## Pagination

### Auto-Paginate

```bash
# Get all results automatically
glab api "projects" --paginate | jq '.[].name'
```

### Manual Pagination

```bash
# First page
glab api "projects?per_page=20&page=1"

# Subsequent pages
glab api "projects?per_page=20&page=2"
```

### Pagination Helper Function

```bash
# Get all pages of results
gitlab_api_all() {
  local endpoint="$1"
  local page=1
  local results="[]"
  local separator="?"
  [[ "$endpoint" == *"?"* ]] && separator="&"

  while true; do
    local response=$(glab api "${endpoint}${separator}per_page=100&page=${page}" 2>/dev/null)
    if [ "$(echo "$response" | jq 'length')" -eq 0 ]; then
      break
    fi
    results=$(echo "$results" "$response" | jq -s 'add')
    ((page++))
  done
  echo "$results"
}
```

## Error Handling

### Check for API Errors

```bash
response=$(glab api "endpoint" 2>&1)

if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
  echo "Error: $(echo "$response" | jq -r '.error // .message')" >&2
  exit 1
fi
```

### Common HTTP Status Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad request | Check field names/values |
| 401 | Unauthorized | Run `glab auth login` |
| 403 | Forbidden | Check permissions/token scopes |
| 404 | Not found | Verify ID/path exists |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable | Invalid field values |
| 429 | Rate limited | Wait and retry |
| 5xx | Server error | Check GitLab status |

## Request Methods

### GET (Read)

```bash
# Simple GET
glab api "projects/:id"

# GET with query params
glab api "projects?visibility=public&per_page=10"

# GET with path encoding
glab api "projects/$(echo 'group/project' | jq -Rr @uri)/issues"
```

### POST (Create)

```bash
# Create with fields
glab api "projects/:id/issues" --method POST \
  -f title="Issue title" \
  -f description="Details here"

# Create with JSON body (complex data)
glab api "projects/:id/issues" --method POST \
  --input - <<< '{"title": "Issue", "labels": ["bug", "urgent"]}'
```

### PUT/PATCH (Update)

```bash
# Update fields
glab api "projects/:id/issues/:iid" --method PUT \
  -f state_event="close"

# Partial update
glab api "projects/:id/issues/:iid" --method PATCH \
  -f title="New title"
```

### DELETE (Remove)

```bash
# Simple delete
glab api "projects/:id/issues/:iid" --method DELETE

# Delete with confirmation params
glab api "projects/:id/repository/files/:path" --method DELETE \
  -f branch="main" \
  -f commit_message="Remove file"
```

## JSON Output Formatting

### Using jq

```bash
# Get single field
glab api "projects/:id" | jq -r '.name'

# Get multiple fields
glab api "projects/:id" | jq '{name, id, visibility}'

# Filter array
glab api "projects" | jq '.[] | select(.visibility == "public")'

# Table format
glab api "groups" | jq -r '.[] | [.id, .name, .path] | @tsv'
```

### Table Helper Function

```bash
gitlab_table() {
  jq -r '(.[0] | keys_unsorted) as $keys |
    ($keys | @tsv),
    (.[] | [.[ $keys[] ]] | @tsv)' | column -t
}

# Usage
glab api "groups" | gitlab_table
```

## Project ID Resolution

### Get Current Project ID

```bash
# From git remote
project_path=$(git remote get-url origin | sed 's|.*gitlab.com[:/]||;s|\.git$||')
glab api "projects/$(echo "$project_path" | jq -Rr @uri)" | jq -r '.id'
```

### Using Project Path

```bash
# Use encoded project path instead of numeric ID
glab api "projects/$(echo 'mygroup/myproject' | jq -Rr @uri)/issues"
```

## Authentication

### Token Scopes by Feature

| Feature | Required Scopes |
|---------|-----------------|
| Read projects | `read_api` |
| Manage issues/MRs | `api` |
| Manage webhooks | `api` |
| Manage groups | `api` |
| Container registry | `read_registry`, `write_registry` |
| Security findings | `read_api` (Ultimate) |

### Check Auth Status

```bash
glab auth status
```

### Use Different Host

```bash
glab api "projects" --hostname gitlab.company.com
```

## Rate Limiting

GitLab imposes rate limits. To handle:

1. Use pagination to reduce requests
2. Add delays between bulk operations
3. Check response headers for limits:

```bash
glab api "projects" -i | grep -i "ratelimit"
```

## Tier Requirements

Some API features require GitLab Premium or Ultimate:

| Feature | Tier Required |
|---------|---------------|
| Code owners | Premium |
| Multiple approvers | Premium |
| Security scanning | Ultimate |
| Vulnerability management | Ultimate |
| Compliance features | Ultimate |

## Related Documentation

- [Quick Reference](./QUICK_REFERENCE.md)
- [Safeguards](./SAFEGUARDS.md)
- [GitLab REST API Docs](https://docs.gitlab.com/ee/api/rest/)
