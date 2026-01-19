"""
Live integration tests for gitlab-issue skill.

Tests issue operations via glab CLI.
"""

import pytest

from tests.live.skills.base import CLISkillTest, APISkillTest
try:
    # When running under pytest, conftest is loaded directly
    from conftest import GitLabAPI, GitLabAPIError
except ImportError:
    # When running directly, use the full path
    from tests.live.conftest import GitLabAPI, GitLabAPIError


@pytest.mark.live
@pytest.mark.p0
class TestGitLabIssueList(CLISkillTest):
    """Tests for listing issues."""

    @pytest.mark.readonly
    def test_list_issues(self, run_glab, gitlab_project: str):
        """Test listing all issues."""
        result = self.run_command(run_glab, "issue", "list", repo=gitlab_project)
        self.assert_success(result)

    @pytest.mark.readonly
    def test_list_open_issues(self, run_glab, gitlab_project: str):
        """Test listing open issues."""
        result = self.run_command(
            run_glab, "issue", "list",
            "--opened",
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.readonly
    def test_list_closed_issues(self, run_glab, gitlab_project: str):
        """Test listing closed issues."""
        result = self.run_command(
            run_glab, "issue", "list",
            "--closed",
            repo=gitlab_project
        )
        self.assert_success(result)
        # Should show closed issues (may have none initially, or test-created ones)
        self.assert_output_contains(result, "closed")

    @pytest.mark.readonly
    def test_list_issues_with_label(self, run_glab, gitlab_project: str):
        """Test listing issues with specific label."""
        result = self.run_command(
            run_glab, "issue", "list",
            "--label", "bug",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabIssueView(CLISkillTest):
    """Tests for viewing issues."""

    @pytest.mark.readonly
    def test_view_issue(self, run_glab, gitlab_project: str):
        """Test viewing a specific issue."""
        result = self.run_command(
            run_glab, "issue", "view", "1",
            repo=gitlab_project
        )
        self.assert_success(result)
        self.assert_output_contains(result, "crashes")

    @pytest.mark.readonly
    def test_view_issue_web(self, run_glab, gitlab_project: str):
        """Test getting web URL for issue (without opening browser)."""
        # Just verify the command works, we won't actually open browser
        result = self.run_command(
            run_glab, "issue", "view", "1",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabIssueCreate(CLISkillTest):
    """Tests for creating issues."""

    @pytest.mark.destructive
    def test_create_issue(self, run_glab, gitlab_project: str, unique_id: str, created_issues: list):
        """Test creating an issue."""
        title = f"Test Issue {unique_id}"

        result = self.run_command(
            run_glab, "issue", "create",
            "--title", title,
            "--description", f"Test description {unique_id}",
            "--yes",  # Skip confirmation
            repo=gitlab_project
        )
        self.assert_success(result)
        # glab returns URL on success (e.g., http://localhost:8080/.../issues/123)
        self.assert_output_contains(result, "issues")

        # Extract issue IID from output for cleanup
        # glab output format: URL like http://localhost:8080/group/project/-/issues/123
        import re
        match = re.search(r'/issues/(\d+)', result.stdout)
        if match:
            created_issues.append(int(match.group(1)))

    @pytest.mark.destructive
    def test_create_issue_with_labels(
        self,
        run_glab,
        gitlab_project: str,
        unique_id: str,
        created_issues: list,
    ):
        """Test creating an issue with labels."""
        title = f"Test Issue Labels {unique_id}"

        result = self.run_command(
            run_glab, "issue", "create",
            "--title", title,
            "--description", f"Test issue with labels {unique_id}",
            "--label", "bug",
            "--label", "priority::high",
            "--yes",
            repo=gitlab_project
        )
        self.assert_success(result)

        import re
        match = re.search(r'#(\d+)', result.stdout)
        if match:
            created_issues.append(int(match.group(1)))


@pytest.mark.live
@pytest.mark.p0
class TestGitLabIssueUpdate(CLISkillTest):
    """Tests for updating issues."""

    @pytest.mark.destructive
    def test_close_issue(self, create_test_issue, run_glab, gitlab_project: str):
        """Test closing an issue."""
        issue = create_test_issue(title="Issue to Close")
        iid = issue["iid"]

        result = self.run_command(
            run_glab, "issue", "close", str(iid),
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.destructive
    def test_reopen_issue(
        self,
        create_test_issue,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        run_glab,
        gitlab_project: str,
    ):
        """Test reopening a closed issue."""
        issue = create_test_issue(title="Issue to Reopen")
        iid = issue["iid"]

        # Close it first via API
        gitlab_api.put(
            f"/projects/{gitlab_project_id}/issues/{iid}",
            {"state_event": "close"}
        )

        # Reopen via CLI
        result = self.run_command(
            run_glab, "issue", "reopen", str(iid),
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.destructive
    def test_update_issue_title(
        self,
        create_test_issue,
        run_glab,
        gitlab_project: str,
        unique_id: str,
    ):
        """Test updating issue title."""
        issue = create_test_issue(title=f"Original Title {unique_id}")
        iid = issue["iid"]

        result = self.run_command(
            run_glab, "issue", "update", str(iid),
            "--title", f"Updated Title {unique_id}",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabIssueNote(CLISkillTest):
    """Tests for issue notes/comments."""

    @pytest.mark.destructive
    def test_add_note(self, create_test_issue, run_glab, gitlab_project: str, unique_id: str):
        """Test adding a note to an issue."""
        issue = create_test_issue(title=f"Issue for Note {unique_id}")
        iid = issue["iid"]

        result = self.run_command(
            run_glab, "issue", "note", str(iid),
            "--message", f"Test comment {unique_id}",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabIssueAPI(APISkillTest):
    """API tests for gitlab-issue skill."""

    @pytest.mark.readonly
    def test_list_issues_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing issues via API."""
        issues = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/issues")
        self.assert_is_list(issues, min_length=1)

    @pytest.mark.readonly
    def test_get_issue_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting issue details via API."""
        issue = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/issues/1")
        self.assert_is_dict(issue)
        self.assert_field_contains(issue, "title", "crash")

    @pytest.mark.readonly
    def test_list_issue_notes_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing issue notes via API."""
        notes = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/issues/1/notes")
        self.assert_is_list(notes)

    @pytest.mark.destructive
    def test_create_issue_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_issues: list,
    ):
        """Test creating issue via API."""
        issue = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues",
            {
                "title": f"API Test Issue {unique_id}",
                "description": "Created via API",
                "labels": "bug",
            }
        )
        created_issues.append(issue["iid"])

        self.assert_is_dict(issue)
        self.assert_field_contains(issue, "title", unique_id)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabIssuePermissions(APISkillTest):
    """Permission tests for gitlab-issue skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_issues(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list issues."""
        issues = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/issues")
        self.assert_is_list(issues)

    @pytest.mark.readonly
    def test_reporter_can_view_issue(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can view issue."""
        issue = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/issues/1")
        self.assert_is_dict(issue)

    @pytest.mark.destructive
    def test_reporter_can_create_issue(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_issues: list,
    ):
        """Test that reporter can create issues."""
        # Reporters can create issues in most GitLab configurations
        issue = self.api_post(
            reporter_api,
            f"/projects/{gitlab_project_id}/issues",
            {"title": f"Reporter Issue {unique_id}"}
        )
        created_issues.append(issue["iid"])
        self.assert_is_dict(issue)
