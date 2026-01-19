"""
Live integration tests for gitlab-repo skill.

Tests repository operations via glab CLI.
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
class TestGitLabRepoRead(CLISkillTest):
    """Read-only tests for gitlab-repo skill using CLI."""

    @pytest.mark.readonly
    def test_repo_view(self, run_glab, gitlab_project: str):
        """Test viewing repository information."""
        result = self.run_command(run_glab, "repo", "view", repo=gitlab_project)
        self.assert_success(result)
        self.assert_output_contains(result, "test-project")

    @pytest.mark.readonly
    def test_repo_list(self, run_glab, gitlab_group: str):
        """Test listing repositories in a group."""
        result = self.run_command(
            run_glab, "repo", "list",
            "--group", gitlab_group,
        )
        self.assert_success(result)
        self.assert_output_contains(result, "test-project")


@pytest.mark.live
@pytest.mark.p0
class TestGitLabRepoAPI(APISkillTest):
    """API tests for gitlab-repo skill."""

    @pytest.mark.readonly
    def test_get_project(self, gitlab_api: GitLabAPI, gitlab_project: str):
        """Test getting project details via API."""
        project = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project.replace('/', '%2F')}"
        )
        self.assert_is_dict(project)
        self.assert_field_equals(project, "path", "test-project")

    @pytest.mark.readonly
    def test_list_project_branches(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing branches."""
        branches = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/repository/branches")
        self.assert_is_list(branches, min_length=1)  # At least main

        # Find main branch
        main_branch = next((b for b in branches if b["name"] == "main"), None)
        assert main_branch is not None, "main branch not found"

    @pytest.mark.readonly
    def test_list_project_tags(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing tags."""
        tags = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/repository/tags")
        self.assert_is_list(tags)  # May be empty

    @pytest.mark.readonly
    def test_get_repository_tree(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting repository tree."""
        tree = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/repository/tree")
        self.assert_is_list(tree, min_length=1)  # At least README

    @pytest.mark.readonly
    def test_get_file_content(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting file content."""
        file_info = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/README.md?ref=main"
        )
        self.assert_is_dict(file_info)
        self.assert_has_field(file_info, "content")

    @pytest.mark.readonly
    def test_get_commits(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing commits."""
        commits = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/repository/commits")
        self.assert_is_list(commits, min_length=1)

    @pytest.mark.readonly
    def test_compare_branches(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test comparing branches."""
        # Compare feature branch to main
        comparison = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/compare?from=main&to=feature/test-branch"
        )
        self.assert_is_dict(comparison)
        self.assert_has_field(comparison, "commits")
        self.assert_has_field(comparison, "diffs")


@pytest.mark.live
@pytest.mark.p0
class TestGitLabRepoWrite(APISkillTest):
    """Write tests for gitlab-repo skill."""

    @pytest.mark.destructive
    def test_create_branch(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test creating a branch."""
        branch_name = f"test/branch-{unique_id}"

        branch = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        self.assert_is_dict(branch)
        self.assert_field_equals(branch, "name", branch_name)

    @pytest.mark.destructive
    def test_create_and_delete_tag(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test creating and deleting a tag."""
        tag_name = f"v0.0.1-test-{unique_id}"

        try:
            # Create tag
            tag = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/repository/tags",
                {"tag_name": tag_name, "ref": "main", "message": "Test tag"}
            )
            self.assert_field_equals(tag, "name", tag_name)
        finally:
            # Cleanup
            self.api_delete(
                gitlab_api,
                f"/projects/{gitlab_project_id}/repository/tags/{tag_name}"
            )

    @pytest.mark.destructive
    def test_create_file(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test creating a file in the repository."""
        branch_name = f"test/file-{unique_id}"
        file_path = f"test-file-{unique_id}.txt"

        # Create branch first
        self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create file
        file_info = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/{file_path}",
            {
                "branch": branch_name,
                "content": f"Test content {unique_id}",
                "commit_message": f"Add test file {unique_id}",
            }
        )
        self.assert_is_dict(file_info)
        self.assert_field_equals(file_info, "file_path", file_path)

    @pytest.mark.destructive
    def test_update_file(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test updating a file in the repository."""
        branch_name = f"test/update-{unique_id}"
        file_path = f"test-update-{unique_id}.txt"

        # Create branch
        self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create file
        self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/{file_path}",
            {
                "branch": branch_name,
                "content": "Initial content",
                "commit_message": "Add file",
            }
        )

        # Update file
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/{file_path}",
            {
                "branch": branch_name,
                "content": "Updated content",
                "commit_message": "Update file",
            }
        )
        self.assert_is_dict(updated)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabRepoClone(CLISkillTest):
    """Clone-related tests for gitlab-repo skill."""

    @pytest.mark.readonly
    def test_repo_clone_url(self, run_glab, gitlab_project: str):
        """Test getting clone URL (doesn't actually clone)."""
        # We can't easily test actual cloning, but we can verify the repo view
        # shows clone information
        result = self.run_command(run_glab, "repo", "view", repo=gitlab_project)
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabRepoPermissions(APISkillTest):
    """Permission tests for gitlab-repo skill."""

    @pytest.mark.readonly
    def test_reporter_can_view_repo(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can view repository."""
        project = self.api_get(reporter_api, f"/projects/{gitlab_project_id}")
        self.assert_is_dict(project)

    @pytest.mark.readonly
    def test_reporter_can_list_branches(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list branches."""
        branches = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/repository/branches")
        self.assert_is_list(branches)

    @pytest.mark.destructive
    def test_reporter_cannot_create_branch(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that reporter cannot create branches."""
        try:
            self.api_post(
                reporter_api,
                f"/projects/{gitlab_project_id}/repository/branches",
                {"branch": f"test-fail-{unique_id}", "ref": "main"}
            )
            pytest.fail("Expected 403 Forbidden")
        except Exception as e:
            # Handle GitLabAPIError from any module path (pytest can load it differently)
            if type(e).__name__ == "GitLabAPIError":
                assert getattr(e, "status_code", 0) in (403, 401)
            else:
                raise
