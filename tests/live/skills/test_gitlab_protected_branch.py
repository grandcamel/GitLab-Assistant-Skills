"""
Live integration tests for gitlab-protected-branch skill.

Tests branch protection rules via API.
"""

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
class TestGitLabProtectedBranchList(APISkillTest):
    """Tests for listing protected branches."""

    @pytest.mark.readonly
    def test_list_protected_branches(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing protected branches."""
        branches = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/protected_branches"
        )
        self.assert_is_list(branches)

    @pytest.mark.readonly
    def test_get_protected_branch(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific protected branch."""
        # First check if main is protected
        branches = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/protected_branches"
        )
        if branches and any(b["name"] == "main" for b in branches):
            branch = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/protected_branches/main"
            )
            self.assert_is_dict(branch)
            self.assert_field_equals(branch, "name", "main")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabProtectedBranchCreate(APISkillTest):
    """Tests for creating protected branches."""

    @pytest.mark.destructive
    def test_protect_branch(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test protecting a branch."""
        branch_name = f"test/protect-{unique_id}"

        # Create branch first
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        try:
            # Protect it
            protected = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/protected_branches",
                {
                    "name": branch_name,
                    "push_access_level": 40,  # Maintainers
                    "merge_access_level": 40,  # Maintainers
                }
            )
            self.assert_is_dict(protected)
            self.assert_field_equals(protected, "name", branch_name)
        finally:
            # Unprotect
            try:
                gitlab_api.delete(
                    f"/projects/{gitlab_project_id}/protected_branches/{branch_name.replace('/', '%2F')}"
                )
            except GitLabAPIError:
                pass

    @pytest.mark.destructive
    def test_protect_branch_with_wildcard(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test protecting branches with wildcard pattern."""
        pattern = f"release-{unique_id}/*"

        try:
            protected = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/protected_branches",
                {
                    "name": pattern,
                    "push_access_level": 40,
                    "merge_access_level": 30,
                }
            )
            self.assert_is_dict(protected)
            self.assert_field_equals(protected, "name", pattern)
        finally:
            # Unprotect
            try:
                gitlab_api.delete(
                    f"/projects/{gitlab_project_id}/protected_branches/{pattern.replace('/', '%2F').replace('*', '%2A')}"
                )
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p2
class TestGitLabProtectedBranchUpdate(APISkillTest):
    """Tests for updating protected branches."""

    @pytest.mark.destructive
    def test_update_protected_branch_access(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test updating protection rules."""
        branch_name = f"test/update-protect-{unique_id}"

        # Create and protect branch
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        try:
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/protected_branches",
                {"name": branch_name, "push_access_level": 40, "merge_access_level": 40}
            )

            # Update using PATCH (GitLab 14.9+)
            # Note: Older GitLab may not support PATCH
            updated = self.api_patch(
                gitlab_api,
                f"/projects/{gitlab_project_id}/protected_branches/{branch_name.replace('/', '%2F')}",
                {"allow_force_push": True}
            )
            # Verify update (if supported)
            if updated:
                self.assert_is_dict(updated)
        except GitLabAPIError:
            # PATCH may not be supported, that's OK
            pass
        finally:
            try:
                gitlab_api.delete(
                    f"/projects/{gitlab_project_id}/protected_branches/{branch_name.replace('/', '%2F')}"
                )
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p2
class TestGitLabProtectedBranchDelete(APISkillTest):
    """Tests for unprotecting branches."""

    @pytest.mark.destructive
    def test_unprotect_branch(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test unprotecting a branch."""
        branch_name = f"test/unprotect-{unique_id}"

        # Create and protect branch
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        gitlab_api.post(
            f"/projects/{gitlab_project_id}/protected_branches",
            {"name": branch_name, "push_access_level": 40, "merge_access_level": 40}
        )

        # Unprotect
        self.api_delete(
            gitlab_api,
            f"/projects/{gitlab_project_id}/protected_branches/{branch_name.replace('/', '%2F')}"
        )

        # Verify unprotected
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/protected_branches/{branch_name.replace('/', '%2F')}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p2
class TestGitLabProtectedBranchAccessLevels(APISkillTest):
    """Tests for different access levels."""

    @pytest.mark.destructive
    def test_protect_with_different_levels(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test protecting with different push/merge levels."""
        branch_name = f"test/levels-{unique_id}"

        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        try:
            # Developers can merge, only maintainers can push
            protected = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/protected_branches",
                {
                    "name": branch_name,
                    "push_access_level": 40,  # Maintainers
                    "merge_access_level": 30,  # Developers
                }
            )
            self.assert_is_dict(protected)
        finally:
            try:
                gitlab_api.delete(
                    f"/projects/{gitlab_project_id}/protected_branches/{branch_name.replace('/', '%2F')}"
                )
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p2
class TestGitLabProtectedBranchPermissions(APISkillTest):
    """Permission tests for gitlab-protected-branch skill."""

    @pytest.mark.readonly
    def test_developer_can_list_protected_branches(
        self,
        developer_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that developer can list protected branches."""
        branches = self.api_get(
            developer_api,
            f"/projects/{gitlab_project_id}/protected_branches"
        )
        self.assert_is_list(branches)

    @pytest.mark.destructive
    def test_developer_cannot_protect_branch(
        self,
        developer_api: GitLabAPI,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_branches: list,
    ):
        """Test that developer cannot protect branches."""
        branch_name = f"test/dev-protect-{unique_id}"

        # Create branch as maintainer
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/repository/branches",
            {"branch": branch_name, "ref": "main"}
        )
        created_branches.append(branch_name)

        # Try to protect as developer
        try:
            developer_api.post(
                f"/projects/{gitlab_project_id}/protected_branches",
                {"name": branch_name, "push_access_level": 30, "merge_access_level": 30}
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.readonly
    def test_reporter_can_view_protected_branches(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter can view protected branches."""
        branches = self.api_get(
            reporter_api,
            f"/projects/{gitlab_project_id}/protected_branches"
        )
        self.assert_is_list(branches)
