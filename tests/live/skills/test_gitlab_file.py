"""
Live integration tests for gitlab-file skill.

Tests repository file operations via API.
"""

import base64
import pytest

from tests.live.skills.base import APISkillTest
try:
    # When running under pytest, conftest is loaded directly
    from conftest import GitLabAPI, GitLabAPIError
except ImportError:
    # When running directly, use the full path
    from tests.live.conftest import GitLabAPI, GitLabAPIError


@pytest.mark.live
@pytest.mark.p2
class TestGitLabFileGet(APISkillTest):
    """Tests for getting file content."""

    @pytest.mark.readonly
    def test_get_file(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting file content."""
        file_info = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/README.md?ref=main"
        )
        self.assert_is_dict(file_info)
        self.assert_has_field(file_info, "content")
        self.assert_has_field(file_info, "encoding")

    @pytest.mark.readonly
    def test_get_file_raw(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting raw file content."""
        content = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/README.md/raw?ref=main"
        )
        # Raw content is returned as dict with 'raw' key
        assert content is not None

    @pytest.mark.readonly
    def test_get_file_blame(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting file blame."""
        blame = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/README.md/blame?ref=main"
        )
        self.assert_is_list(blame)

    @pytest.mark.readonly
    def test_get_file_not_found(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test 404 for non-existent file."""
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/nonexistent.txt?ref=main",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p2
class TestGitLabFileCreate(APISkillTest):
    """Tests for creating files."""

    @pytest.mark.destructive
    def test_create_file(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test creating a file."""
        branch_name = f"test/file-create-{unique_id}"
        file_path = f"test-create-{unique_id}.txt"

        # Create branch
        gitlab_api.post(
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
    def test_create_file_with_encoding(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test creating a file with base64 encoding."""
        branch_name = f"test/file-b64-{unique_id}"
        file_path = f"test-b64-{unique_id}.txt"

        # Create branch
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create file with base64 content
        content = base64.b64encode(f"Binary content {unique_id}".encode()).decode()
        file_info = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/{file_path}",
            {
                "branch": branch_name,
                "content": content,
                "encoding": "base64",
                "commit_message": f"Add base64 file {unique_id}",
            }
        )
        self.assert_is_dict(file_info)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabFileUpdate(APISkillTest):
    """Tests for updating files."""

    @pytest.mark.destructive
    def test_update_file(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test updating a file."""
        branch_name = f"test/file-update-{unique_id}"
        file_path = f"test-update-{unique_id}.txt"

        # Create branch
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create file
        gitlab_api.post(
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
@pytest.mark.p2
class TestGitLabFileDelete(APISkillTest):
    """Tests for deleting files."""

    @pytest.mark.destructive
    def test_delete_file(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test deleting a file."""
        branch_name = f"test/file-delete-{unique_id}"
        file_path = f"test-delete-{unique_id}.txt"

        # Create branch
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create file
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/files/{file_path}",
            {
                "branch": branch_name,
                "content": "To be deleted",
                "commit_message": "Add file to delete",
            }
        )

        # Delete file
        self.api_delete(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/{file_path}?branch={branch_name}&commit_message=Delete%20file"
        )

        # Verify deleted
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/files/{file_path}?ref={branch_name}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p2
class TestGitLabFileTree(APISkillTest):
    """Tests for repository tree."""

    @pytest.mark.readonly
    def test_get_tree(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting repository tree."""
        tree = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/tree"
        )
        self.assert_is_list(tree)

    @pytest.mark.readonly
    def test_get_tree_with_path(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting tree for a specific path."""
        tree = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/tree?path=src"
        )
        self.assert_is_list(tree)

    @pytest.mark.readonly
    def test_get_tree_recursive(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting recursive tree."""
        tree = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/repository/tree?recursive=true"
        )
        self.assert_is_list(tree)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabFilePermissions(APISkillTest):
    """Permission tests for gitlab-file skill."""

    @pytest.mark.readonly
    def test_reporter_can_read_file(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter can read files."""
        file_info = self.api_get(
            reporter_api,
            f"/projects/{gitlab_project_id}/repository/files/README.md?ref=main"
        )
        self.assert_is_dict(file_info)

    @pytest.mark.destructive
    def test_reporter_cannot_create_file(
        self,
        reporter_api: GitLabAPI,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test that reporter cannot create files."""
        branch_name = f"test/reporter-file-{unique_id}"

        # Create branch as maintainer
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Try to create file as reporter
        try:
            reporter_api.post(
                f"/projects/{gitlab_project_id}/repository/files/fail-{unique_id}.txt",
                {
                    "branch": branch_name,
                    "content": "Should fail",
                    "commit_message": "Fail",
                }
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.destructive
    def test_developer_can_create_file(
        self,
        developer_api: GitLabAPI,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test that developer can create files."""
        branch_name = f"test/dev-file-{unique_id}"

        # Create branch as maintainer
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Create file as developer
        file_info = developer_api.post(
            f"/projects/{gitlab_project_id}/repository/files/dev-{unique_id}.txt",
            {
                "branch": branch_name,
                "content": "Developer content",
                "commit_message": "Dev file",
            }
        )
        self.assert_is_dict(file_info)
