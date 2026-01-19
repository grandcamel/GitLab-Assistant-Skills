# PRD: Live Integration Testing with GitLab Enterprise

## Executive Summary

Create a comprehensive live integration testing framework that validates all 19 GitLab Assistant Skills against a local GitLab Enterprise Edition (EE) instance running in Docker. Tests will exercise the complete lifecycle of GitLab objects (groups, projects, issues, merge requests, etc.) using both `glab` CLI commands and `glab api` raw endpoint calls.

## Goals

1. **Validate All Skills** — Verify each of the 19 skills works correctly against a real GitLab instance
2. **Full Lifecycle Testing** — Test create, read, update, delete (CRUD) operations for all supported objects
3. **Reproducible Environment** — Docker-based setup that can be spun up/down for testing
4. **CI/CD Ready** — Tests can run in automated pipelines
5. **Documentation Accuracy** — Confirm all documented commands work as described

## Non-Goals

- Performance/load testing
- Multi-node/HA GitLab configurations
- GitLab Kubernetes deployments
- Production deployment validation

---

## Technical Requirements

### GitLab Enterprise Docker Setup

**Image:** `gitlab/gitlab-ee:latest` (or pinned version like `17.7.0-ee.0`)

**Minimum Resources:**
| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Memory | 4 GB | 8 GB |
| CPU | 2 cores | 4 cores |
| Storage | 10 GB | 20 GB |
| Shared Memory | 256 MB | 256 MB |

**Port Mappings:**
| Service | Container Port | Host Port |
|---------|---------------|-----------|
| HTTP | 80 | 8080 |
| HTTPS | 443 | 8443 |
| SSH | 22 | 2222 |

**Volume Mounts:**
```
$GITLAB_HOME/config → /etc/gitlab
$GITLAB_HOME/logs   → /var/log/gitlab
$GITLAB_HOME/data   → /var/opt/gitlab
```

### Docker Compose Configuration

Create `tests/live/docker-compose.yml`:

```yaml
services:
  gitlab:
    image: gitlab/gitlab-ee:${GITLAB_VERSION:-latest}
    container_name: gitlab-test
    hostname: gitlab.local
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'http://gitlab.local:8080'
        gitlab_rails['gitlab_shell_ssh_port'] = 2222
        # Reduce resource usage for testing
        puma['worker_processes'] = 2
        sidekiq['concurrency'] = 5
        prometheus_monitoring['enable'] = false
        # Disable unnecessary services
        gitlab_kas['enable'] = false
        sentinel['enable'] = false
        registry['enable'] = false
    ports:
      - '8080:80'
      - '8443:443'
      - '2222:22'
    volumes:
      - gitlab-config:/etc/gitlab
      - gitlab-logs:/var/log/gitlab
      - gitlab-data:/var/opt/gitlab
    shm_size: '256m'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/-/health"]
      interval: 30s
      timeout: 10s
      retries: 20
      start_period: 300s

volumes:
  gitlab-config:
  gitlab-logs:
  gitlab-data:
```

### Test Infrastructure

**Directory Structure:**
```
tests/
├── live/
│   ├── docker-compose.yml       # GitLab EE container
│   ├── conftest.py              # Pytest fixtures
│   ├── README.md                # Setup instructions
│   ├── scripts/
│   │   ├── setup-gitlab.sh      # Initial GitLab configuration
│   │   ├── wait-for-gitlab.sh   # Health check script
│   │   ├── create-test-data.sh  # Seed test data
│   │   └── cleanup.sh           # Reset between test runs
│   ├── fixtures/
│   │   ├── test_project/        # Sample project files
│   │   └── test_data.yaml       # Test data definitions
│   └── skills/
│       ├── test_gitlab_group.py
│       ├── test_gitlab_search.py
│       ├── test_gitlab_mr.py
│       ├── test_gitlab_issue.py
│       ├── test_gitlab_ci.py
│       ├── test_gitlab_repo.py
│       ├── test_gitlab_release.py
│       ├── test_gitlab_label.py
│       ├── test_gitlab_milestone.py
│       ├── test_gitlab_variable.py
│       ├── test_gitlab_protected_branch.py
│       ├── test_gitlab_webhook.py
│       ├── test_gitlab_file.py
│       ├── test_gitlab_wiki.py
│       ├── test_gitlab_discussion.py
│       ├── test_gitlab_badge.py
│       ├── test_gitlab_container.py
│       └── test_gitlab_vulnerability.py
```

---

## Test Scenarios by Skill

### Phase 1: Core Infrastructure (P0)

#### 1. gitlab-group
| Test | Operation | Validation |
|------|-----------|------------|
| Create root group | `POST /groups` | Group exists, correct attributes |
| Create subgroup | `POST /groups` with parent_id | Hierarchy correct |
| Add member | `POST /groups/:id/members` | Member has correct access level |
| Update member access | `PUT /groups/:id/members/:user_id` | Access level changed |
| Remove member | `DELETE /groups/:id/members/:user_id` | Member removed |
| List subgroups | `GET /groups/:id/subgroups` | Returns correct list |
| Share with group | `POST /groups/:id/share` | Sharing configured |
| Delete group | `DELETE /groups/:id` | Group removed |

#### 2. gitlab-repo
| Test | Operation | Validation |
|------|-----------|------------|
| Create project | `glab repo create` | Project exists |
| Clone project | `glab repo clone` | Local copy created |
| Fork project | `glab repo fork` | Fork exists |
| Archive project | API call | Project archived |
| List projects | `glab repo list` | Returns projects |
| Delete project | API call | Project removed |

#### 3. gitlab-issue
| Test | Operation | Validation |
|------|-----------|------------|
| Create issue | `glab issue create` | Issue created with correct fields |
| List issues | `glab issue list` | Returns issues |
| View issue | `glab issue view` | Displays correct data |
| Update issue | `glab issue update` | Fields updated |
| Add labels | `glab issue update --label` | Labels applied |
| Assign issue | `glab issue update --assignee` | Assignee set |
| Close issue | `glab issue close` | State changed |
| Reopen issue | `glab issue reopen` | State changed |
| Delete issue | `glab issue delete` | Issue removed |

#### 4. gitlab-mr
| Test | Operation | Validation |
|------|-----------|------------|
| Create branch | `git checkout -b` + push | Branch exists |
| Create MR | `glab mr create` | MR created |
| List MRs | `glab mr list` | Returns MRs |
| View MR | `glab mr view` | Displays correct data |
| Update MR | `glab mr update` | Fields updated |
| Approve MR | `glab mr approve` | Approval recorded |
| Merge MR | `glab mr merge` | MR merged, branch deleted |
| Close MR | `glab mr close` | State changed |

#### 5. gitlab-ci
| Test | Operation | Validation |
|------|-----------|------------|
| View pipeline status | `glab ci status` | Shows current status |
| List pipelines | `glab ci list` | Returns pipelines |
| View pipeline | `glab ci view` | Displays jobs |
| View job logs | `glab ci trace` | Shows logs |
| Retry pipeline | `glab ci retry` | New pipeline created |
| Cancel pipeline | `glab ci cancel` | Pipeline cancelled |
| Run pipeline | `glab ci run` | Pipeline triggered |

### Phase 2: Project Management (P1)

#### 6. gitlab-label
| Test | Operation | Validation |
|------|-----------|------------|
| Create label | `glab label create` | Label exists |
| List labels | `glab label list` | Returns labels |
| Update label | API call | Label updated |
| Delete label | API call | Label removed |

#### 7. gitlab-milestone
| Test | Operation | Validation |
|------|-----------|------------|
| Create milestone | `glab milestone create` | Milestone exists |
| List milestones | `glab milestone list` | Returns milestones |
| Update milestone | API call | Fields updated |
| Close milestone | API call | State changed |
| Delete milestone | `glab milestone delete` | Milestone removed |

#### 8. gitlab-release
| Test | Operation | Validation |
|------|-----------|------------|
| Create tag | `git tag` + push | Tag exists |
| Create release | `glab release create` | Release exists |
| List releases | `glab release list` | Returns releases |
| View release | `glab release view` | Displays data |
| Upload asset | `glab release upload` | Asset attached |
| Delete release | `glab release delete` | Release removed |

#### 9. gitlab-variable
| Test | Operation | Validation |
|------|-----------|------------|
| Set variable | `glab variable set` | Variable exists |
| List variables | `glab variable list` | Returns variables |
| Get variable | `glab variable get` | Returns value |
| Update variable | `glab variable update` | Value changed |
| Delete variable | `glab variable delete` | Variable removed |

### Phase 3: API-Based Skills (P2)

#### 10. gitlab-search
| Test | Operation | Validation |
|------|-----------|------------|
| Search projects | `GET /search?scope=projects` | Returns matches |
| Search issues | `GET /search?scope=issues` | Returns matches |
| Search MRs | `GET /search?scope=merge_requests` | Returns matches |
| Search code (blobs) | `GET /search?scope=blobs` | Returns matches |
| Search commits | `GET /search?scope=commits` | Returns matches |
| Project-scoped search | `GET /projects/:id/search` | Scoped results |
| Group-scoped search | `GET /groups/:id/search` | Scoped results |

#### 11. gitlab-protected-branch
| Test | Operation | Validation |
|------|-----------|------------|
| Protect branch | `POST /protected_branches` | Protection applied |
| List protected | `GET /protected_branches` | Returns list |
| Get protection | `GET /protected_branches/:name` | Returns rules |
| Update protection | `PATCH /protected_branches/:name` | Rules updated |
| Unprotect branch | `DELETE /protected_branches/:name` | Protection removed |

#### 12. gitlab-webhook
| Test | Operation | Validation |
|------|-----------|------------|
| Create webhook | `POST /hooks` | Webhook exists |
| List webhooks | `GET /hooks` | Returns webhooks |
| Get webhook | `GET /hooks/:id` | Returns config |
| Update webhook | `PUT /hooks/:id` | Config updated |
| Test webhook | `POST /hooks/:id/test/push_events` | Test triggered |
| Delete webhook | `DELETE /hooks/:id` | Webhook removed |

#### 13. gitlab-file
| Test | Operation | Validation |
|------|-----------|------------|
| Get file info | `GET /repository/files/:path` | Returns metadata |
| Get raw content | `GET /repository/files/:path/raw` | Returns content |
| Get blame | `GET /repository/files/:path/blame` | Returns blame |
| Create file | `POST /repository/files/:path` | File created |
| Update file | `PUT /repository/files/:path` | File updated |
| Delete file | `DELETE /repository/files/:path` | File removed |

#### 14. gitlab-wiki
| Test | Operation | Validation |
|------|-----------|------------|
| Create wiki page | `POST /wikis` | Page created |
| List wiki pages | `GET /wikis` | Returns pages |
| Get wiki page | `GET /wikis/:slug` | Returns content |
| Update wiki page | `PUT /wikis/:slug` | Content updated |
| Delete wiki page | `DELETE /wikis/:slug` | Page removed |

#### 15. gitlab-discussion
| Test | Operation | Validation |
|------|-----------|------------|
| Create MR discussion | `POST /merge_requests/:iid/discussions` | Thread created |
| List discussions | `GET /merge_requests/:iid/discussions` | Returns threads |
| Add note to thread | `POST /discussions/:id/notes` | Reply added |
| Resolve thread | `PUT /discussions/:id` | Thread resolved |
| Create issue note | `POST /issues/:iid/notes` | Comment added |

#### 16. gitlab-badge
| Test | Operation | Validation |
|------|-----------|------------|
| Create badge | `POST /badges` | Badge exists |
| List badges | `GET /badges` | Returns badges |
| Get badge | `GET /badges/:id` | Returns config |
| Update badge | `PUT /badges/:id` | Config updated |
| Preview badge | `GET /badges/render` | Returns preview |
| Delete badge | `DELETE /badges/:id` | Badge removed |

### Phase 4: Advanced Features (P3)

#### 17. gitlab-container
| Test | Operation | Validation |
|------|-----------|------------|
| List repositories | `GET /registry/repositories` | Returns repos |
| Get repository | `GET /registry/repositories/:id` | Returns details |
| List tags | `GET /registry/repositories/:id/tags` | Returns tags |
| Get tag | `GET /registry/repositories/:id/tags/:name` | Returns tag info |
| Delete tag | `DELETE /registry/repositories/:id/tags/:name` | Tag removed |
| Bulk delete tags | `DELETE /registry/repositories/:id/tags` | Tags removed |

**Note:** Requires container registry enabled and actual image pushes.

#### 18. gitlab-vulnerability (Ultimate Only)
| Test | Operation | Validation |
|------|-----------|------------|
| List vulnerabilities | `GET /vulnerabilities` | Returns list |
| Get vulnerability | `GET /vulnerabilities/:id` | Returns details |
| Confirm vulnerability | `POST /vulnerabilities/:id/confirm` | State changed |
| Dismiss vulnerability | `POST /vulnerabilities/:id/dismiss` | State changed |
| Resolve vulnerability | `POST /vulnerabilities/:id/resolve` | State changed |
| Revert to detected | `POST /vulnerabilities/:id/revert` | State changed |

**Note:** Requires GitLab Ultimate license and security scanning configuration.

---

## Test Data Requirements

### Seed Data Script

Create `tests/live/scripts/create-test-data.sh`:

```bash
#!/bin/bash
# Creates test data hierarchy for live integration tests

# Root group
glab api groups -X POST -f name="Test Group" -f path="test-group"

# Subgroup
glab api groups -X POST -f name="Test Subgroup" -f path="test-subgroup" -f parent_id=<parent_id>

# Project with files
glab api projects -X POST -f name="Test Project" -f namespace_id=<group_id>

# Sample files
# - README.md
# - src/main.py
# - .gitlab-ci.yml (with test jobs)
# - Dockerfile (for container registry tests)

# Issues
# - Open issue
# - Closed issue
# - Issue with labels and milestone

# Merge request
# - Open MR from feature branch
# - Merged MR

# Labels
# - bug, enhancement, documentation

# Milestones
# - Current milestone (open)
# - Past milestone (closed)

# Wiki pages
# - Home
# - API Documentation
```

### Test User Accounts

| User | Role | Purpose |
|------|------|---------|
| root | Admin | Initial setup, admin operations |
| test-maintainer | Maintainer | Most CRUD operations |
| test-developer | Developer | Limited write operations |
| test-reporter | Reporter | Read-only operations |

---

## Implementation Plan

### Phase 1: Infrastructure Setup (Week 1)

1. **Create Docker environment**
   - [ ] Write `docker-compose.yml`
   - [ ] Create `wait-for-gitlab.sh` health check script
   - [ ] Create `setup-gitlab.sh` for initial configuration
   - [ ] Document setup process in `README.md`

2. **Configure glab CLI**
   - [ ] Script to authenticate glab against local instance
   - [ ] Configure SSH keys for git operations
   - [ ] Verify connectivity

3. **Create pytest fixtures**
   - [ ] GitLab instance fixture (session-scoped)
   - [ ] Group fixture (module-scoped)
   - [ ] Project fixture (module-scoped)
   - [ ] Cleanup fixtures

### Phase 2: Core Skill Tests (Week 2)

4. **Implement P0 tests**
   - [ ] `test_gitlab_group.py`
   - [ ] `test_gitlab_repo.py`
   - [ ] `test_gitlab_issue.py`
   - [ ] `test_gitlab_mr.py`
   - [ ] `test_gitlab_ci.py`

### Phase 3: Management Skill Tests (Week 3)

5. **Implement P1 tests**
   - [ ] `test_gitlab_label.py`
   - [ ] `test_gitlab_milestone.py`
   - [ ] `test_gitlab_release.py`
   - [ ] `test_gitlab_variable.py`

### Phase 4: API Skill Tests (Week 4)

6. **Implement P2 tests**
   - [ ] `test_gitlab_search.py`
   - [ ] `test_gitlab_protected_branch.py`
   - [ ] `test_gitlab_webhook.py`
   - [ ] `test_gitlab_file.py`
   - [ ] `test_gitlab_wiki.py`
   - [ ] `test_gitlab_discussion.py`
   - [ ] `test_gitlab_badge.py`

### Phase 5: Advanced Tests (Week 5)

7. **Implement P3 tests**
   - [ ] `test_gitlab_container.py` (requires registry setup)
   - [ ] `test_gitlab_vulnerability.py` (requires Ultimate license)

8. **CI/CD Integration**
   - [ ] GitHub Actions workflow for live tests
   - [ ] Test result reporting
   - [ ] Container caching for faster startup

---

## Test Execution

### Local Development

```bash
# Start GitLab
cd tests/live
docker compose up -d

# Wait for GitLab to be ready (5-10 minutes on first run)
./scripts/wait-for-gitlab.sh

# Get root password
docker exec gitlab-test grep 'Password:' /etc/gitlab/initial_root_password

# Configure glab
glab auth login --hostname localhost:8080

# Run tests
pytest tests/live/skills/ -v

# Cleanup
docker compose down -v
```

### CI/CD Pipeline

```yaml
# .github/workflows/live-tests.yml
name: Live Integration Tests

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  live-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    services:
      gitlab:
        image: gitlab/gitlab-ee:latest
        ports:
          - 8080:80
        options: --shm-size=256m

    steps:
      - uses: actions/checkout@v4

      - name: Wait for GitLab
        run: ./tests/live/scripts/wait-for-gitlab.sh

      - name: Configure glab
        run: |
          glab auth login --hostname localhost:8080 --token ${{ secrets.GITLAB_TEST_TOKEN }}

      - name: Run live tests
        run: pytest tests/live/skills/ -v --tb=short
```

---

## Test Markers

```python
# conftest.py markers
pytest.mark.live        # Requires running GitLab instance
pytest.mark.destructive # Creates/modifies/deletes data
pytest.mark.readonly    # Read-only operations
pytest.mark.slow        # Takes > 30 seconds
pytest.mark.ultimate    # Requires GitLab Ultimate license
pytest.mark.registry    # Requires container registry
```

### Running Specific Test Categories

```bash
# All live tests
pytest tests/live/ -v -m live

# Only read-only tests (safe to run repeatedly)
pytest tests/live/ -v -m "live and readonly"

# Skip slow tests
pytest tests/live/ -v -m "live and not slow"

# Skip Ultimate-only tests
pytest tests/live/ -v -m "live and not ultimate"
```

---

## Success Criteria

### Minimum Viable Testing

- [ ] All 9 core CLI-based skills have passing tests
- [ ] All 10 API-based skills have passing tests
- [ ] Tests can run against fresh GitLab instance
- [ ] Tests clean up after themselves
- [ ] Documentation matches actual behavior

### Full Coverage

- [ ] CRUD lifecycle tested for all object types
- [ ] Error cases tested (404, 403, 422)
- [ ] Edge cases documented and tested
- [ ] CI/CD pipeline runs weekly
- [ ] Test results published to GitHub Actions

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| GitLab startup time (5-10 min) | Use container caching, session-scoped fixtures |
| Resource usage (8GB RAM) | Use memory-constrained config, run on capable CI runners |
| Test data pollution | Cleanup fixtures, isolated test groups |
| API rate limiting | Add delays between tests, use pagination |
| Ultimate-only features | Mark tests, skip gracefully |
| Container registry tests | Optional, require explicit setup |

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/live/docker-compose.yml` | GitLab EE container definition |
| `tests/live/conftest.py` | Pytest fixtures and configuration |
| `tests/live/README.md` | Setup and usage instructions |
| `tests/live/scripts/wait-for-gitlab.sh` | Health check script |
| `tests/live/scripts/setup-gitlab.sh` | Initial configuration |
| `tests/live/scripts/create-test-data.sh` | Seed test data |
| `tests/live/scripts/cleanup.sh` | Reset between runs |
| `tests/live/skills/test_gitlab_*.py` | 18 test files (one per skill) |
| `.github/workflows/live-tests.yml` | CI/CD workflow |

---

## References

- [GitLab Docker Installation](https://docs.gitlab.com/install/docker/)
- [GitLab Installation Requirements](https://docs.gitlab.com/ee/install/requirements.html)
- [GitLab Memory-Constrained Environments](https://docs.gitlab.com/omnibus/settings/memory_constrained_envs/)
- [GitLab REST API Documentation](https://docs.gitlab.com/ee/api/rest/)
- [glab CLI Documentation](https://gitlab.com/gitlab-org/cli)

---

## Appendix: Sample Test Structure

```python
# tests/live/skills/test_gitlab_issue.py
import pytest
import subprocess
import json

@pytest.mark.live
class TestGitLabIssue:
    """Live integration tests for gitlab-issue skill."""

    @pytest.fixture(autouse=True)
    def setup(self, test_project):
        """Set up test project context."""
        self.project = test_project
        self.created_issues = []

    def teardown_method(self):
        """Clean up created issues."""
        for issue_iid in self.created_issues:
            subprocess.run(
                ["glab", "issue", "delete", str(issue_iid), "-y"],
                capture_output=True
            )

    @pytest.mark.destructive
    def test_create_issue(self):
        """Test creating an issue via glab CLI."""
        result = subprocess.run(
            ["glab", "issue", "create",
             "--title", "Test Issue",
             "--description", "Created by live test"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        # Extract issue IID from output
        issue_iid = self._extract_iid(result.stdout)
        self.created_issues.append(issue_iid)

        # Verify issue exists
        view_result = subprocess.run(
            ["glab", "issue", "view", str(issue_iid)],
            capture_output=True, text=True
        )
        assert "Test Issue" in view_result.stdout

    @pytest.mark.readonly
    def test_list_issues(self):
        """Test listing issues via glab CLI."""
        result = subprocess.run(
            ["glab", "issue", "list"],
            capture_output=True, text=True
        )
        assert result.returncode == 0
```
