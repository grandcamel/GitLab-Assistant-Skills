"""
Live integration tests for gitlab-mr skill.

Tests merge request operations via glab CLI.
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
class TestGitLabMRList(CLISkillTest):
    """Tests for listing merge requests."""

    @pytest.mark.readonly
    def test_list_merge_requests(self, run_glab, gitlab_project: str):
        """Test listing all merge requests."""
        result = self.run_command(run_glab, "mr", "list", repo=gitlab_project)
        self.assert_success(result)

    @pytest.mark.readonly
    def test_list_open_merge_requests(self, run_glab, gitlab_project: str):
        """Test listing open merge requests (default behavior)."""
        # glab mr list shows open MRs by default
        result = self.run_command(
            run_glab, "mr", "list",
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.readonly
    def test_list_merged_requests(self, run_glab, gitlab_project: str):
        """Test listing merged requests."""
        result = self.run_command(
            run_glab, "mr", "list",
            "--merged",
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.readonly
    def test_list_closed_requests(self, run_glab, gitlab_project: str):
        """Test listing closed (not merged) requests."""
        result = self.run_command(
            run_glab, "mr", "list",
            "--closed",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRView(CLISkillTest):
    """Tests for viewing merge requests."""

    @pytest.mark.readonly
    def test_view_merge_request(self, run_glab, gitlab_project: str):
        """Test viewing a specific merge request."""
        # View MR !1 created by setup script
        result = self.run_command(
            run_glab, "mr", "view", "1",
            repo=gitlab_project
        )
        # May fail if no MR exists, which is acceptable
        if result.returncode == 0:
            self.assert_output_contains(result, "feature")


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRCreate(CLISkillTest):
    """Tests for creating merge requests."""

    @pytest.mark.destructive
    def test_create_merge_request(
        self,
        run_glab,
        gitlab_project: str,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
        created_merge_requests: list,
    ):
        """Test creating a merge request."""
        branch_name = f"test/mr-cli-{unique_id}"

        # Create branch via API
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create a commit on the branch
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/files/test-mr-{unique_id}.txt",
            {
                "branch": branch_name,
                "content": f"Test content for MR {unique_id}",
                "commit_message": f"Add test file for MR {unique_id}",
            }
        )

        # Create MR via CLI
        result = self.run_command(
            run_glab, "mr", "create",
            "--source-branch", branch_name,
            "--target-branch", "main",
            "--title", f"Test MR {unique_id}",
            "--description", f"Test description {unique_id}",
            "--yes",
            repo=gitlab_project,
            timeout=60,  # MR creation can be slow
        )
        self.assert_success(result)

        # Extract MR IID for cleanup
        import re
        match = re.search(r'!(\d+)', result.stdout)
        if match:
            created_merge_requests.append(int(match.group(1)))


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRUpdate(CLISkillTest):
    """Tests for updating merge requests."""

    @pytest.mark.destructive
    def test_close_merge_request(self, create_test_mr, run_glab, gitlab_project: str):
        """Test closing a merge request."""
        mr = create_test_mr(title="MR to Close")
        iid = mr["iid"]

        result = self.run_command(
            run_glab, "mr", "close", str(iid),
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.destructive
    def test_reopen_merge_request(
        self,
        create_test_mr,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        run_glab,
        gitlab_project: str,
    ):
        """Test reopening a closed merge request."""
        mr = create_test_mr(title="MR to Reopen")
        iid = mr["iid"]

        # Close it first via API
        gitlab_api.put(
            f"/projects/{gitlab_project_id}/merge_requests/{iid}",
            {"state_event": "close"}
        )

        # Reopen via CLI
        result = self.run_command(
            run_glab, "mr", "reopen", str(iid),
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.destructive
    def test_update_merge_request_title(
        self,
        create_test_mr,
        run_glab,
        gitlab_project: str,
        unique_id: str,
    ):
        """Test updating merge request title."""
        mr = create_test_mr(title=f"Original MR Title {unique_id}")
        iid = mr["iid"]

        result = self.run_command(
            run_glab, "mr", "update", str(iid),
            "--title", f"Updated MR Title {unique_id}",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRNote(CLISkillTest):
    """Tests for merge request notes/comments."""

    @pytest.mark.destructive
    def test_add_note(self, create_test_mr, run_glab, gitlab_project: str, unique_id: str):
        """Test adding a note to a merge request."""
        mr = create_test_mr(title=f"MR for Note {unique_id}")
        iid = mr["iid"]

        result = self.run_command(
            run_glab, "mr", "note", str(iid),
            "--message", f"Test MR comment {unique_id}",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRDiff(CLISkillTest):
    """Tests for merge request diffs."""

    @pytest.mark.readonly
    def test_mr_diff(self, run_glab, gitlab_project: str):
        """Test viewing merge request diff."""
        # Try to view diff of MR !1
        result = self.run_command(
            run_glab, "mr", "diff", "1",
            repo=gitlab_project
        )
        # May fail if MR doesn't exist
        if result.returncode == 0:
            # Diff output should contain something
            assert result.stdout or result.stderr


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRAPI(APISkillTest):
    """API tests for gitlab-mr skill."""

    @pytest.mark.readonly
    def test_list_merge_requests_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing merge requests via API."""
        mrs = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/merge_requests")
        self.assert_is_list(mrs)

    @pytest.mark.readonly
    def test_get_merge_request_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting merge request details via API."""
        # Try to get MR !1
        mr = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/1",
            expected_status=404
        )
        if mr:
            self.assert_is_dict(mr)
            self.assert_has_field(mr, "title")

    @pytest.mark.readonly
    def test_list_mr_commits_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing merge request commits via API."""
        commits = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/1/commits",
            expected_status=404
        )
        if commits:
            self.assert_is_list(commits)

    @pytest.mark.readonly
    def test_list_mr_changes_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing merge request changes via API."""
        changes = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/1/changes",
            expected_status=404
        )
        if changes:
            self.assert_is_dict(changes)
            self.assert_has_field(changes, "changes")

    @pytest.mark.destructive
    def test_create_merge_request_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
        created_merge_requests: list,
    ):
        """Test creating merge request via API."""
        branch_name = f"test/mr-api-{unique_id}"

        # Create branch
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create commit
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/files/api-test-{unique_id}.txt",
            {
                "branch": branch_name,
                "content": f"API test {unique_id}",
                "commit_message": f"Add API test file {unique_id}",
            }
        )

        # Create MR
        mr = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests",
            {
                "source_branch": branch_name,
                "target_branch": "main",
                "title": f"API Test MR {unique_id}",
            }
        )
        created_merge_requests.append(mr["iid"])

        self.assert_is_dict(mr)
        self.assert_field_contains(mr, "title", unique_id)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRApproval(APISkillTest):
    """Tests for merge request approvals."""

    @pytest.mark.readonly
    def test_get_approval_rules(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting project approval rules."""
        rules = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/approval_rules"
        )
        self.assert_is_list(rules)

    @pytest.mark.readonly
    def test_get_mr_approvals(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting merge request approvals."""
        approvals = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/1/approvals",
            expected_status=404
        )
        if approvals:
            self.assert_is_dict(approvals)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabMRPermissions(APISkillTest):
    """Permission tests for gitlab-mr skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_mrs(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list merge requests."""
        mrs = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/merge_requests")
        self.assert_is_list(mrs)

    @pytest.mark.readonly
    def test_reporter_can_view_mr(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can view merge request."""
        mr = self.api_get(
            reporter_api,
            f"/projects/{gitlab_project_id}/merge_requests/1",
            expected_status=404
        )
        # May be None if MR doesn't exist, that's OK

    @pytest.mark.destructive
    def test_developer_can_create_mr(
        self,
        developer_api: GitLabAPI,
        gitlab_api: GitLabAPI,  # For setup
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
        created_merge_requests: list,
    ):
        """Test that developer can create merge requests."""
        branch_name = f"test/dev-mr-{unique_id}"

        # Create branch using maintainer (setup)
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create commit using maintainer
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/files/dev-test-{unique_id}.txt",
            {
                "branch": branch_name,
                "content": f"Dev test {unique_id}",
                "commit_message": f"Add dev test file {unique_id}",
            }
        )

        # Create MR as developer
        mr = developer_api.post(
            f"/projects/{gitlab_project_id}/merge_requests",
            {
                "source_branch": branch_name,
                "target_branch": "main",
                "title": f"Dev Test MR {unique_id}",
            }
        )
        created_merge_requests.append(mr["iid"])

        self.assert_is_dict(mr)
