# Live Integration Tests

This directory contains live integration tests that validate GitLab Assistant Skills against a local GitLab Enterprise Edition instance running in Docker.

## Prerequisites

- Docker Desktop (4GB+ memory allocated)
- Docker Compose v2
- Python 3.10+
- `glab` CLI tool
- `pytest` with async support

## Quick Start

```bash
# 1. Start GitLab (takes 5-10 minutes on first run)
cd tests/live
docker compose up -d

# 2. Wait for GitLab to be ready
./scripts/wait-for-gitlab.sh

# 3. Setup test users and tokens
./scripts/setup-gitlab.sh

# 4. Create test data
./scripts/create-test-data.sh

# 5. Run tests
pytest skills/ -v -m "p0"  # Core tests only
pytest skills/ -v          # All tests
```

## Directory Structure

```
tests/live/
├── docker-compose.yml      # GitLab EE container config
├── .env.test              # Generated credentials (gitignored)
├── README.md              # This file
├── conftest.py            # Main pytest fixtures
├── scripts/
│   ├── wait-for-gitlab.sh   # Health check script
│   ├── setup-gitlab.sh      # Create users/tokens
│   ├── create-test-data.sh  # Seed test data
│   └── cleanup.sh           # Reset between runs
├── fixtures/
│   ├── test_data.yaml       # Test data definitions
│   └── test_project/        # Sample project files
└── skills/
    ├── conftest.py          # Skills-specific fixtures
    ├── base.py              # Base test classes
    └── test_gitlab_*.py     # Test files by skill
```

## Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.live` | All live integration tests |
| `@pytest.mark.p0` | Core priority (group, repo, issue, mr, ci) |
| `@pytest.mark.p1` | Management (label, milestone, release, variable) |
| `@pytest.mark.p2` | API skills (search, webhook, file, wiki, etc.) |
| `@pytest.mark.p3` | Advanced (container, vulnerability) |
| `@pytest.mark.readonly` | Safe read-only operations |
| `@pytest.mark.destructive` | Modifies state |
| `@pytest.mark.ultimate` | Requires Ultimate license |
| `@pytest.mark.registry` | Requires container registry |

## Running Tests

### By Phase

```bash
# Core tests (fastest feedback)
pytest skills/ -v -m "p0"

# Management tests
pytest skills/ -v -m "p1"

# API skill tests
pytest skills/ -v -m "p2"

# Advanced tests (may require extra setup)
pytest skills/ -v -m "p3"
```

### By Risk Level

```bash
# Safe read-only tests
pytest skills/ -v -m "readonly"

# All tests including destructive ones
pytest skills/ -v
```

### Specific Skills

```bash
# Single skill
pytest skills/test_gitlab_issue.py -v

# Multiple skills
pytest skills/test_gitlab_issue.py skills/test_gitlab_mr.py -v
```

## Configuration

### Environment Variables

The `setup-gitlab.sh` script creates `.env.test` with these variables:

| Variable | Description |
|----------|-------------|
| `GITLAB_URL` | GitLab base URL (default: `http://localhost:8080`) |
| `GITLAB_HOST` | GitLab hostname for glab (default: `localhost:8080`) |
| `GITLAB_ROOT_TOKEN` | Admin token (full access) |
| `GITLAB_MAINTAINER_TOKEN` | Maintainer access token |
| `GITLAB_DEVELOPER_TOKEN` | Developer access token |
| `GITLAB_REPORTER_TOKEN` | Reporter access token (read-only) |
| `GITLAB_TOKEN` | Default token for tests |

### Docker Configuration

The `docker-compose.yml` is optimized for local development:

- **Image**: `gitlab/gitlab-ee:17.7.0-ee.0` (pinned version)
- **Ports**: 8080 (HTTP), 8443 (HTTPS), 2222 (SSH)
- **Memory**: 4-8GB with Puma/Sidekiq tuning
- **Disabled services**: Prometheus, Grafana, KAS, Sentinel

### Container Registry (Optional)

To enable the container registry for `gitlab-container` tests:

```bash
ENABLE_REGISTRY=true docker compose up -d
```

## Test Users

| User | Access Level | Purpose |
|------|-------------|---------|
| `root` | Admin (owner) | Setup, admin operations |
| `test-maintainer` | 40 (Maintainer) | Most CRUD operations |
| `test-developer` | 30 (Developer) | Limited write operations |
| `test-reporter` | 20 (Reporter) | Read-only operations |

## Cleanup

### Between Test Runs

```bash
# Quick cleanup (keeps users and groups)
./scripts/cleanup.sh

# Full cleanup (removes everything)
./scripts/cleanup.sh --full
```

### Complete Reset

```bash
# Stop GitLab and remove all data
docker compose down -v

# Or use the cleanup script
./scripts/cleanup.sh --volumes
```

## Troubleshooting

### GitLab Won't Start

1. Check Docker has enough memory (4GB+ recommended)
2. Check logs: `docker compose logs -f gitlab`
3. Wait longer on first startup (can take 10+ minutes)

### Tests Fail with 401 Unauthorized

1. Verify tokens exist: `cat .env.test`
2. Re-run setup: `./scripts/setup-gitlab.sh`
3. Check glab auth: `glab auth status`

### Tests Fail with 404 Not Found

1. Verify test data exists: `./scripts/create-test-data.sh`
2. Check GitLab UI at http://localhost:8080

### Connection Refused

1. Verify container is running: `docker compose ps`
2. Check health: `./scripts/wait-for-gitlab.sh`
3. Verify ports aren't blocked by firewall

### Rate Limiting

GitLab may rate-limit requests. If you see 429 errors:

1. Wait a few minutes
2. Run tests in smaller batches
3. Check rate limit settings in GitLab admin

## Writing New Tests

### Test Class Template

```python
import pytest
from tests.live.skills.base import CLISkillTest

@pytest.mark.live
@pytest.mark.p0  # or p1, p2, p3
class TestGitLabFeature(CLISkillTest):
    """Tests for gitlab-feature skill."""

    @pytest.mark.readonly
    def test_list_items(self, gitlab_project):
        """Test listing items."""
        result = self.run_glab("feature", "list")
        assert result.returncode == 0

    @pytest.mark.destructive
    def test_create_item(self, gitlab_project, unique_id):
        """Test creating an item."""
        result = self.run_glab("feature", "create", f"test-{unique_id}")
        assert result.returncode == 0
```

### Fixtures Available

- `gitlab_api` - GitLabAPI wrapper for direct API calls
- `gitlab_project` - Test project path (`live-test-group/test-project`)
- `gitlab_group` - Test group path (`live-test-group`)
- `unique_id` - Unique identifier for test isolation
- `test_user` - Current test user credentials

## CI/CD

Live tests run weekly via GitHub Actions. See `.github/workflows/live-tests.yml`.

To trigger manually:

1. Go to Actions tab
2. Select "Live Integration Tests"
3. Click "Run workflow"
