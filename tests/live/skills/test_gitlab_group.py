"""
Live integration tests for gitlab-group skill.

Tests group/team management operations via API.
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
@pytest.mark.p0
class TestGitLabGroupRead(APISkillTest):
    """Read-only tests for gitlab-group skill."""

    @pytest.mark.readonly
    def test_list_groups(self, gitlab_api: GitLabAPI):
        """Test listing groups."""
        groups = self.api_get(gitlab_api, "/groups")
        self.assert_is_list(groups)

    @pytest.mark.readonly
    def test_get_group(self, gitlab_api: GitLabAPI, gitlab_group: str):
        """Test getting a specific group."""
        group = self.api_get(gitlab_api, f"/groups/{gitlab_group}")
        self.assert_is_dict(group)
        self.assert_field_equals(group, "path", "live-test-group")

    @pytest.mark.readonly
    def test_get_group_with_details(self, gitlab_api: GitLabAPI, gitlab_group: str):
        """Test getting group with additional details."""
        group = self.api_get(gitlab_api, f"/groups/{gitlab_group}?with_projects=true")
        self.assert_is_dict(group)
        self.assert_has_field(group, "projects")

    @pytest.mark.readonly
    def test_list_group_members(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing group members."""
        members = self.api_get(gitlab_api, f"/groups/{gitlab_group_id}/members")
        self.assert_is_list(members, min_length=1)  # At least test-maintainer

    @pytest.mark.readonly
    def test_list_group_projects(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing projects in a group."""
        projects = self.api_get(gitlab_api, f"/groups/{gitlab_group_id}/projects")
        self.assert_is_list(projects, min_length=1)  # At least test-project

    @pytest.mark.readonly
    def test_list_subgroups(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing subgroups."""
        subgroups = self.api_get(gitlab_api, f"/groups/{gitlab_group_id}/subgroups")
        self.assert_is_list(subgroups, min_length=1)  # At least the test subgroup

    @pytest.mark.readonly
    def test_get_subgroup(self, gitlab_api: GitLabAPI):
        """Test getting a subgroup."""
        subgroup = self.api_get(gitlab_api, "/groups/live-test-group%2Fsubgroup")
        self.assert_is_dict(subgroup)
        self.assert_field_equals(subgroup, "path", "subgroup")

    @pytest.mark.readonly
    def test_search_groups(self, gitlab_api: GitLabAPI):
        """Test searching for groups."""
        groups = self.api_get(gitlab_api, "/groups?search=live-test")
        self.assert_is_list(groups, min_length=1)

    @pytest.mark.readonly
    def test_group_not_found(self, gitlab_api: GitLabAPI):
        """Test 404 for non-existent group."""
        result = self.api_get(gitlab_api, "/groups/nonexistent-group-xyz", expected_status=404)
        assert result is None


@pytest.mark.live
@pytest.mark.p0
class TestGitLabGroupWrite(APISkillTest):
    """Write tests for gitlab-group skill."""

    @pytest.mark.destructive
    def test_create_and_delete_group(self, root_api: GitLabAPI, unique_id: str):
        """Test creating and deleting a group."""
        group_path = f"test-group-{unique_id}"

        # Create group
        group = self.api_post(root_api, "/groups", {
            "name": f"Test Group {unique_id}",
            "path": group_path,
            "visibility": "private",
        })
        self.assert_is_dict(group)
        self.assert_field_equals(group, "path", group_path)
        group_id = group["id"]

        try:
            # Verify it exists
            fetched = self.api_get(root_api, f"/groups/{group_id}")
            self.assert_field_equals(fetched, "id", group_id)
        finally:
            # Cleanup
            self.api_delete(root_api, f"/groups/{group_id}")

    @pytest.mark.destructive
    def test_update_group(self, root_api: GitLabAPI, gitlab_group_id: int):
        """Test updating a group."""
        # Get original description
        original = self.api_get(root_api, f"/groups/{gitlab_group_id}")
        original_desc = original.get("description", "")

        try:
            # Update description
            updated = self.api_put(root_api, f"/groups/{gitlab_group_id}", {
                "description": "Updated description for testing",
            })
            self.assert_field_contains(updated, "description", "Updated")
        finally:
            # Restore original
            self.api_put(root_api, f"/groups/{gitlab_group_id}", {
                "description": original_desc,
            })

    @pytest.mark.destructive
    def test_add_and_remove_member(
        self,
        root_api: GitLabAPI,
        gitlab_group_id: int,
        unique_id: str,
    ):
        """Test adding and removing a group member."""
        # Get developer user ID
        users = self.api_get(root_api, "/users?username=test-developer")
        self.assert_is_list(users, min_length=1)
        user_id = users[0]["id"]

        # Remove if already member (cleanup from previous runs)
        try:
            self.api_delete(root_api, f"/groups/{gitlab_group_id}/members/{user_id}")
        except GitLabAPIError:
            pass

        try:
            # Add member
            member = self.api_post(root_api, f"/groups/{gitlab_group_id}/members", {
                "user_id": user_id,
                "access_level": 30,  # Developer
            })
            self.assert_field_equals(member, "access_level", 30)
        finally:
            # Cleanup - remove member
            try:
                self.api_delete(root_api, f"/groups/{gitlab_group_id}/members/{user_id}")
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p0
class TestGitLabGroupPermissions(APISkillTest):
    """Permission tests for gitlab-group skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_groups(self, reporter_api: GitLabAPI, gitlab_group: str):
        """Test that reporter can list groups."""
        groups = self.api_get(reporter_api, "/groups")
        self.assert_is_list(groups)

    @pytest.mark.readonly
    def test_reporter_can_view_group(self, reporter_api: GitLabAPI, gitlab_group: str):
        """Test that reporter can view group details."""
        group = self.api_get(reporter_api, f"/groups/{gitlab_group}")
        self.assert_is_dict(group)

    @pytest.mark.destructive
    def test_developer_cannot_delete_group(self, developer_api: GitLabAPI, gitlab_group_id: int):
        """Test that developer cannot delete a group."""
        # This should fail with 403
        try:
            self.api_delete(developer_api, f"/groups/{gitlab_group_id}")
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code == 403
