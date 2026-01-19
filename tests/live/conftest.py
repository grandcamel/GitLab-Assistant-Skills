"""
Main fixtures for GitLab live integration tests.

Provides:
- GitLab connection and authentication
- GitLabAPI wrapper for direct API calls
- Session and module scoped fixtures
"""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, Optional
import json

import pytest


# =============================================================================
# Configuration
# =============================================================================

def _load_env_file() -> dict[str, str]:
    """Load environment variables from .env.test file."""
    env_file = Path(__file__).parent / ".env.test"
    env_vars = {}

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    return env_vars


# Load environment from file
_env_vars = _load_env_file()


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable from .env.test or environment."""
    return os.environ.get(key, _env_vars.get(key, default))


# =============================================================================
# GitLab API Wrapper
# =============================================================================

@dataclass
class GitLabConfig:
    """GitLab connection configuration."""
    url: str
    host: str
    token: str
    root_token: str
    maintainer_token: str
    developer_token: str
    reporter_token: str


class GitLabAPIError(Exception):
    """Exception raised for GitLab API errors."""

    def __init__(self, message: str, status_code: int = 0, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class GitLabAPI:
    """
    Wrapper for GitLab API calls using glab CLI.

    Features:
    - 3 retries with exponential backoff
    - 30-second timeout per call
    - Role-based authentication
    """

    def __init__(self, config: GitLabConfig):
        self.config = config
        self._current_token = config.token

    def as_role(self, role: str) -> "GitLabAPI":
        """Return API instance with specified role's token."""
        token_map = {
            "root": self.config.root_token,
            "admin": self.config.root_token,
            "maintainer": self.config.maintainer_token,
            "developer": self.config.developer_token,
            "reporter": self.config.reporter_token,
        }
        token = token_map.get(role)
        if not token:
            raise ValueError(f"Unknown role: {role}")

        api = GitLabAPI(self.config)
        api._current_token = token
        return api

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        retries: int = 3,
        timeout: int = 30,
    ) -> dict | list | None:
        """
        Make an API request to GitLab.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint (e.g., "/projects")
            data: Request body data
            retries: Number of retries on failure
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response or None for 204 responses

        Raises:
            GitLabAPIError: On API errors after all retries
        """
        last_error = None

        for attempt in range(retries):
            try:
                result = self._make_request(method, endpoint, data, timeout)
                return result
            except GitLabAPIError as e:
                last_error = e
                # Don't retry on 4xx errors (except 429 rate limit)
                if 400 <= e.status_code < 500 and e.status_code != 429:
                    raise
                # Exponential backoff
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)

        raise last_error or GitLabAPIError("Request failed")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict],
        timeout: int,
    ) -> dict | list | None:
        """Execute a single API request."""
        cmd = [
            "glab", "api",
            "-X", method.upper(),
        ]

        # Add data for POST/PUT/PATCH
        if data and method.upper() in ("POST", "PUT", "PATCH"):
            cmd.extend(["--input", "-", "-H", "Content-Type: application/json"])

        cmd.append(endpoint)

        env = os.environ.copy()
        env["GITLAB_HOST"] = self.config.host
        env["GITLAB_TOKEN"] = self._current_token

        input_data = json.dumps(data) if data and method.upper() in ("POST", "PUT", "PATCH") else None

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                input=input_data,
            )
        except subprocess.TimeoutExpired as e:
            raise GitLabAPIError(f"Request timed out after {timeout}s", 0) from e

        # Handle errors
        if result.returncode != 0:
            # Try to parse error response
            try:
                error_data = json.loads(result.stderr or result.stdout)
                message = error_data.get("message", str(error_data))
            except json.JSONDecodeError:
                message = result.stderr or result.stdout or "Unknown error"

            # Extract status code from glab output if available
            status_code = 500
            if "404" in message:
                status_code = 404
            elif "401" in message or "unauthorized" in message.lower():
                status_code = 401
            elif "403" in message or "forbidden" in message.lower():
                status_code = 403
            elif "422" in message:
                status_code = 422
            elif "429" in message:
                status_code = 429

            raise GitLabAPIError(message, status_code)

        # Parse response
        if not result.stdout.strip():
            return None

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw": result.stdout}

    # Convenience methods
    def get(self, endpoint: str, **kwargs) -> dict | list | None:
        """Make a GET request."""
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, data: dict, **kwargs) -> dict | list | None:
        """Make a POST request."""
        return self.request("POST", endpoint, data, **kwargs)

    def put(self, endpoint: str, data: dict, **kwargs) -> dict | list | None:
        """Make a PUT request."""
        return self.request("PUT", endpoint, data, **kwargs)

    def patch(self, endpoint: str, data: dict, **kwargs) -> dict | list | None:
        """Make a PATCH request."""
        return self.request("PATCH", endpoint, data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> dict | list | None:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)


# =============================================================================
# Fixtures - Session Scope
# =============================================================================

@pytest.fixture(scope="session")
def gitlab_config() -> GitLabConfig:
    """GitLab configuration loaded from environment."""
    url = get_env("GITLAB_URL", "http://localhost:8080")
    host = get_env("GITLAB_HOST", "localhost:8080")

    config = GitLabConfig(
        url=url,
        host=host,
        token=get_env("GITLAB_TOKEN", ""),
        root_token=get_env("GITLAB_ROOT_TOKEN", ""),
        maintainer_token=get_env("GITLAB_MAINTAINER_TOKEN", ""),
        developer_token=get_env("GITLAB_DEVELOPER_TOKEN", ""),
        reporter_token=get_env("GITLAB_REPORTER_TOKEN", ""),
    )

    # Validate configuration
    if not config.token:
        pytest.skip("GITLAB_TOKEN not set - run setup-gitlab.sh first")

    return config


@pytest.fixture(scope="session")
def gitlab_api(gitlab_config: GitLabConfig) -> GitLabAPI:
    """GitLab API wrapper with default (maintainer) authentication."""
    api = GitLabAPI(gitlab_config)

    # Verify connection
    try:
        version = api.get("/version")
        if not version:
            pytest.skip("Cannot connect to GitLab")
    except GitLabAPIError as e:
        pytest.skip(f"GitLab API error: {e}")

    return api


@pytest.fixture(scope="session")
def gitlab_url(gitlab_config: GitLabConfig) -> str:
    """GitLab base URL."""
    return gitlab_config.url


@pytest.fixture(scope="session")
def gitlab_host(gitlab_config: GitLabConfig) -> str:
    """GitLab hostname for glab CLI."""
    return gitlab_config.host


# =============================================================================
# Fixtures - Module Scope (shared within test file)
# =============================================================================

@pytest.fixture(scope="module")
def gitlab_group() -> str:
    """Test group path."""
    return "live-test-group"


@pytest.fixture(scope="module")
def gitlab_project() -> str:
    """Test project path."""
    return "live-test-group/test-project"


@pytest.fixture(scope="module")
def gitlab_project_id(gitlab_api: GitLabAPI, gitlab_project: str) -> int:
    """Test project ID."""
    project = gitlab_api.get(f"/projects/{gitlab_project.replace('/', '%2F')}")
    if not project:
        pytest.skip("Test project not found - run create-test-data.sh")
    return project["id"]


@pytest.fixture(scope="module")
def gitlab_group_id(gitlab_api: GitLabAPI, gitlab_group: str) -> int:
    """Test group ID."""
    group = gitlab_api.get(f"/groups/{gitlab_group}")
    if not group:
        pytest.skip("Test group not found - run create-test-data.sh")
    return group["id"]


# =============================================================================
# Fixtures - Function Scope (per test)
# =============================================================================

@pytest.fixture
def unique_id() -> str:
    """Unique identifier for test isolation."""
    import uuid
    return uuid.uuid4().hex[:8]


@pytest.fixture
def test_user(gitlab_config: GitLabConfig) -> dict[str, str]:
    """Current test user credentials (maintainer by default)."""
    return {
        "username": "test-maintainer",
        "token": gitlab_config.maintainer_token,
    }


@pytest.fixture
def root_api(gitlab_api: GitLabAPI) -> GitLabAPI:
    """GitLab API with root/admin authentication."""
    return gitlab_api.as_role("root")


@pytest.fixture
def developer_api(gitlab_api: GitLabAPI) -> GitLabAPI:
    """GitLab API with developer authentication."""
    return gitlab_api.as_role("developer")


@pytest.fixture
def reporter_api(gitlab_api: GitLabAPI) -> GitLabAPI:
    """GitLab API with reporter (read-only) authentication."""
    return gitlab_api.as_role("reporter")


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture
def created_issues(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[int], None, None]:
    """Track and cleanup issues created during tests."""
    issue_iids: list[int] = []
    yield issue_iids

    # Cleanup
    for iid in issue_iids:
        try:
            gitlab_api.delete(f"/projects/{gitlab_project_id}/issues/{iid}")
        except GitLabAPIError:
            pass


@pytest.fixture
def created_branches(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[str], None, None]:
    """Track and cleanup branches created during tests."""
    branches: list[str] = []
    yield branches

    # Cleanup
    for branch in branches:
        try:
            encoded = branch.replace("/", "%2F")
            gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/branches/{encoded}")
        except GitLabAPIError:
            pass


@pytest.fixture
def created_labels(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[str], None, None]:
    """Track and cleanup labels created during tests."""
    labels: list[str] = []
    yield labels

    # Cleanup
    for label in labels:
        try:
            encoded = label.replace("/", "%2F").replace(" ", "%20")
            gitlab_api.delete(f"/projects/{gitlab_project_id}/labels/{encoded}")
        except GitLabAPIError:
            pass


@pytest.fixture
def created_milestones(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[int], None, None]:
    """Track and cleanup milestones created during tests."""
    milestone_ids: list[int] = []
    yield milestone_ids

    # Cleanup
    for mid in milestone_ids:
        try:
            gitlab_api.delete(f"/projects/{gitlab_project_id}/milestones/{mid}")
        except GitLabAPIError:
            pass


# =============================================================================
# Markers
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "live: live integration tests against GitLab")
    config.addinivalue_line("markers", "p0: core priority tests")
    config.addinivalue_line("markers", "p1: management priority tests")
    config.addinivalue_line("markers", "p2: API skills tests")
    config.addinivalue_line("markers", "p3: advanced tests")
    config.addinivalue_line("markers", "readonly: read-only operations")
    config.addinivalue_line("markers", "destructive: modifies state")
    config.addinivalue_line("markers", "ultimate: requires Ultimate license")
    config.addinivalue_line("markers", "registry: requires container registry")
