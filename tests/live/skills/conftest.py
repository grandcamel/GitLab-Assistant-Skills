"""
Skills-specific fixtures for GitLab live integration tests.

Provides fixtures tailored for testing CLI and API skills.
"""

import os
import subprocess
from typing import Generator

import pytest

try:
    # When running under pytest, conftest is loaded directly
    from conftest import GitLabAPI, GitLabAPIError, GitLabConfig
except ImportError:
    # When running directly, use the full path
    from tests.live.conftest import GitLabAPI, GitLabAPIError, GitLabConfig


# =============================================================================
# CLI Execution Helpers
# =============================================================================

@pytest.fixture
def glab_env(gitlab_config: GitLabConfig) -> dict[str, str]:
    """Environment variables for glab CLI execution."""
    env = os.environ.copy()
    env["GITLAB_TOKEN"] = gitlab_config.token
    env["GITLAB_HOST"] = gitlab_config.host
    return env


@pytest.fixture
def run_glab(glab_env: dict[str, str], gitlab_host: str):
    """
    Factory fixture to run glab commands.

    Usage:
        def test_something(run_glab):
            result = run_glab("issue", "list")
            assert result.returncode == 0
    """
    def _run_glab(*args, repo: str = None, timeout: int = 30) -> subprocess.CompletedProcess:
        cmd = ["glab"]

        if repo:
            cmd.extend(["--repo", repo])

        cmd.extend(args)

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=glab_env,
        )

    return _run_glab


# =============================================================================
# Resource Creation Fixtures
# =============================================================================

@pytest.fixture
def create_test_issue(gitlab_api: GitLabAPI, gitlab_project_id: int, created_issues: list[int]):
    """
    Factory fixture to create test issues with automatic cleanup.

    Usage:
        def test_something(create_test_issue):
            issue = create_test_issue(title="Test Issue", description="...")
            assert issue["iid"] > 0
    """
    def _create_issue(
        title: str,
        description: str = "",
        labels: list[str] = None,
        assignee_ids: list[int] = None,
        milestone_id: int = None,
    ) -> dict:
        data = {
            "title": title,
            "description": description,
        }
        if labels:
            data["labels"] = ",".join(labels)
        if assignee_ids:
            data["assignee_ids"] = assignee_ids
        if milestone_id:
            data["milestone_id"] = milestone_id

        issue = gitlab_api.post(f"/projects/{gitlab_project_id}/issues", data)
        created_issues.append(issue["iid"])
        return issue

    return _create_issue


@pytest.fixture
def create_test_branch(gitlab_api: GitLabAPI, gitlab_project_id: int, created_branches: list[str]):
    """
    Factory fixture to create test branches with automatic cleanup.

    Usage:
        def test_something(create_test_branch):
            branch = create_test_branch("feature/test-123")
            assert branch["name"] == "feature/test-123"
    """
    def _create_branch(name: str, ref: str = "main") -> dict:
        branch = gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": name, "ref": ref}
        )
        created_branches.append(name)
        return branch

    return _create_branch


@pytest.fixture
def create_test_label(gitlab_api: GitLabAPI, gitlab_project_id: int, created_labels: list[str]):
    """
    Factory fixture to create test labels with automatic cleanup.

    Usage:
        def test_something(create_test_label):
            label = create_test_label("test-label", color="#ff0000")
            assert label["name"] == "test-label"
    """
    def _create_label(name: str, color: str = "#428bca", description: str = "") -> dict:
        label = gitlab_api.post(
            f"/projects/{gitlab_project_id}/labels",
            {"name": name, "color": color, "description": description}
        )
        created_labels.append(name)
        return label

    return _create_label


@pytest.fixture
def create_test_milestone(gitlab_api: GitLabAPI, gitlab_project_id: int, created_milestones: list[int]):
    """
    Factory fixture to create test milestones with automatic cleanup.

    Usage:
        def test_something(create_test_milestone):
            milestone = create_test_milestone("v0.0.1-test")
            assert milestone["title"] == "v0.0.1-test"
    """
    def _create_milestone(
        title: str,
        description: str = "",
        due_date: str = None,
        start_date: str = None,
    ) -> dict:
        data = {"title": title, "description": description}
        if due_date:
            data["due_date"] = due_date
        if start_date:
            data["start_date"] = start_date

        milestone = gitlab_api.post(f"/projects/{gitlab_project_id}/milestones", data)
        created_milestones.append(milestone["id"])
        return milestone

    return _create_milestone


# =============================================================================
# MR-specific Fixtures
# =============================================================================

@pytest.fixture
def created_merge_requests(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[int], None, None]:
    """Track and cleanup merge requests created during tests."""
    mr_iids: list[int] = []
    yield mr_iids

    # Cleanup - close MRs
    for iid in mr_iids:
        try:
            gitlab_api.put(
                f"/projects/{gitlab_project_id}/merge_requests/{iid}",
                {"state_event": "close"}
            )
        except GitLabAPIError:
            pass


@pytest.fixture
def create_test_mr(
    gitlab_api: GitLabAPI,
    gitlab_project_id: int,
    created_merge_requests: list[int],
    created_branches: list[str],
    unique_id: str,
):
    """
    Factory fixture to create test merge requests with automatic cleanup.

    Creates a new branch with a commit and opens an MR.

    Usage:
        def test_something(create_test_mr):
            mr = create_test_mr(title="Test MR")
            assert mr["iid"] > 0
    """
    def _create_mr(
        title: str,
        description: str = "",
        source_branch: str = None,
        target_branch: str = "main",
        labels: list[str] = None,
    ) -> dict:
        # Create source branch if not specified
        if not source_branch:
            source_branch = f"test/mr-{unique_id}"
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/repository/branches",
                {"branch": source_branch, "ref": target_branch}
            )
            created_branches.append(source_branch)

            # Create a commit on the branch
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/repository/files/test-{unique_id}.txt",
                {
                    "branch": source_branch,
                    "content": f"Test file for MR {unique_id}",
                    "commit_message": f"Add test file for MR {unique_id}",
                }
            )

        # Create MR
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
        }
        if labels:
            data["labels"] = ",".join(labels)

        mr = gitlab_api.post(f"/projects/{gitlab_project_id}/merge_requests", data)
        created_merge_requests.append(mr["iid"])
        return mr

    return _create_mr


# =============================================================================
# Webhook Fixtures
# =============================================================================

@pytest.fixture
def created_webhooks(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[int], None, None]:
    """Track and cleanup webhooks created during tests."""
    hook_ids: list[int] = []
    yield hook_ids

    # Cleanup
    for hook_id in hook_ids:
        try:
            gitlab_api.delete(f"/projects/{gitlab_project_id}/hooks/{hook_id}")
        except GitLabAPIError:
            pass


@pytest.fixture
def create_test_webhook(gitlab_api: GitLabAPI, gitlab_project_id: int, created_webhooks: list[int]):
    """
    Factory fixture to create test webhooks with automatic cleanup.

    Usage:
        def test_something(create_test_webhook):
            hook = create_test_webhook("https://example.com/hook")
            assert hook["id"] > 0
    """
    def _create_webhook(
        url: str,
        push_events: bool = True,
        merge_requests_events: bool = False,
        issues_events: bool = False,
    ) -> dict:
        hook = gitlab_api.post(
            f"/projects/{gitlab_project_id}/hooks",
            {
                "url": url,
                "push_events": push_events,
                "merge_requests_events": merge_requests_events,
                "issues_events": issues_events,
            }
        )
        created_webhooks.append(hook["id"])
        return hook

    return _create_webhook


# =============================================================================
# Variable Fixtures
# =============================================================================

@pytest.fixture
def created_variables(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[str], None, None]:
    """Track and cleanup variables created during tests."""
    var_keys: list[str] = []
    yield var_keys

    # Cleanup
    for key in var_keys:
        try:
            gitlab_api.delete(f"/projects/{gitlab_project_id}/variables/{key}")
        except GitLabAPIError:
            pass


@pytest.fixture
def create_test_variable(gitlab_api: GitLabAPI, gitlab_project_id: int, created_variables: list[str]):
    """
    Factory fixture to create test variables with automatic cleanup.

    Usage:
        def test_something(create_test_variable):
            var = create_test_variable("TEST_VAR_123", "test_value")
            assert var["key"] == "TEST_VAR_123"
    """
    def _create_variable(
        key: str,
        value: str,
        protected: bool = False,
        masked: bool = False,
        environment_scope: str = "*",
    ) -> dict:
        var = gitlab_api.post(
            f"/projects/{gitlab_project_id}/variables",
            {
                "key": key,
                "value": value,
                "protected": protected,
                "masked": masked,
                "environment_scope": environment_scope,
            }
        )
        created_variables.append(key)
        return var

    return _create_variable


# =============================================================================
# Wiki Fixtures
# =============================================================================

@pytest.fixture
def created_wiki_pages(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[str], None, None]:
    """Track and cleanup wiki pages created during tests."""
    slugs: list[str] = []
    yield slugs

    # Cleanup
    for slug in slugs:
        try:
            gitlab_api.delete(f"/projects/{gitlab_project_id}/wikis/{slug}")
        except GitLabAPIError:
            pass


@pytest.fixture
def create_test_wiki_page(gitlab_api: GitLabAPI, gitlab_project_id: int, created_wiki_pages: list[str]):
    """
    Factory fixture to create test wiki pages with automatic cleanup.

    Usage:
        def test_something(create_test_wiki_page):
            page = create_test_wiki_page("Test Page", "# Content")
            assert page["slug"] == "Test-Page"
    """
    def _create_wiki_page(
        title: str,
        content: str,
        format: str = "markdown",
    ) -> dict:
        page = gitlab_api.post(
            f"/projects/{gitlab_project_id}/wikis",
            {"title": title, "content": content, "format": format}
        )
        created_wiki_pages.append(page["slug"])
        return page

    return _create_wiki_page


# =============================================================================
# Badge Fixtures
# =============================================================================

@pytest.fixture
def created_badges(
    gitlab_api: GitLabAPI, gitlab_project_id: int
) -> Generator[list[int], None, None]:
    """Track and cleanup badges created during tests."""
    badge_ids: list[int] = []
    yield badge_ids

    # Cleanup
    for badge_id in badge_ids:
        try:
            gitlab_api.delete(f"/projects/{gitlab_project_id}/badges/{badge_id}")
        except GitLabAPIError:
            pass


@pytest.fixture
def create_test_badge(gitlab_api: GitLabAPI, gitlab_project_id: int, created_badges: list[int]):
    """
    Factory fixture to create test badges with automatic cleanup.

    Usage:
        def test_something(create_test_badge):
            badge = create_test_badge("https://example.com", "https://img.shields.io/...")
            assert badge["id"] > 0
    """
    def _create_badge(link_url: str, image_url: str) -> dict:
        badge = gitlab_api.post(
            f"/projects/{gitlab_project_id}/badges",
            {"link_url": link_url, "image_url": image_url}
        )
        created_badges.append(badge["id"])
        return badge

    return _create_badge
