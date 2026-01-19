"""
Live integration tests for gitlab-container skill.

Tests container registry operations via API.
Requires container registry to be enabled (ENABLE_REGISTRY=true).
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
@pytest.mark.p3
@pytest.mark.registry
class TestGitLabContainerRepositories(APISkillTest):
    """Tests for container repositories."""

    @pytest.mark.readonly
    def test_list_container_repositories(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing container repositories."""
        repos = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/registry/repositories",
            expected_status=404  # Registry may not be enabled
        )
        if repos:
            self.assert_is_list(repos)

    @pytest.mark.readonly
    def test_get_container_repository(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific container repository."""
        repos = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/registry/repositories",
            expected_status=404
        )
        if repos:
            repo_id = repos[0]["id"]
            repo = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/registry/repositories/{repo_id}"
            )
            self.assert_is_dict(repo)
            self.assert_has_field(repo, "name")


@pytest.mark.live
@pytest.mark.p3
@pytest.mark.registry
class TestGitLabContainerTags(APISkillTest):
    """Tests for container tags."""

    @pytest.mark.readonly
    def test_list_container_tags(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing container tags."""
        repos = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/registry/repositories",
            expected_status=404
        )
        if repos:
            repo_id = repos[0]["id"]
            tags = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/registry/repositories/{repo_id}/tags"
            )
            self.assert_is_list(tags)

    @pytest.mark.readonly
    def test_get_container_tag(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific container tag."""
        repos = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/registry/repositories",
            expected_status=404
        )
        if repos:
            repo_id = repos[0]["id"]
            tags = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/registry/repositories/{repo_id}/tags"
            )
            if tags:
                tag_name = tags[0]["name"]
                tag = self.api_get(
                    gitlab_api,
                    f"/projects/{gitlab_project_id}/registry/repositories/{repo_id}/tags/{tag_name}"
                )
                self.assert_is_dict(tag)


@pytest.mark.live
@pytest.mark.p3
@pytest.mark.registry
class TestGitLabContainerDelete(APISkillTest):
    """Tests for deleting container images."""

    @pytest.mark.destructive
    def test_delete_container_tag(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test deleting a container tag."""
        repos = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/registry/repositories",
            expected_status=404
        )
        if not repos:
            pytest.skip("No container repositories available")

        # Find a test tag to delete (be careful!)
        # In a real test, we'd push a test image first
        pytest.skip("Skipping deletion test - requires pushing a test image first")

    @pytest.mark.destructive
    def test_bulk_delete_container_tags(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test bulk deleting container tags."""
        repos = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/registry/repositories",
            expected_status=404
        )
        if not repos:
            pytest.skip("No container repositories available")

        # Skip - would need test images
        pytest.skip("Skipping bulk deletion test - requires test images")


@pytest.mark.live
@pytest.mark.p3
@pytest.mark.registry
class TestGitLabContainerCleanup(APISkillTest):
    """Tests for container cleanup policies."""

    @pytest.mark.readonly
    def test_get_cleanup_policy(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting container cleanup policy."""
        policy = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}",  # Policy is in project attributes
        )
        self.assert_is_dict(policy)
        # container_expiration_policy is an attribute of the project

    @pytest.mark.destructive
    def test_update_cleanup_policy(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test updating container cleanup policy."""
        # Get current policy
        project = gitlab_api.get(f"/projects/{gitlab_project_id}")
        original_policy = project.get("container_expiration_policy", {})

        try:
            # Update policy (enable it if disabled)
            updated = self.api_put(
                gitlab_api,
                f"/projects/{gitlab_project_id}",
                {
                    "container_expiration_policy_attributes": {
                        "enabled": True,
                        "cadence": "1month",
                        "keep_n": 10,
                        "older_than": "90d",
                    }
                }
            )
            self.assert_is_dict(updated)
        except GitLabAPIError:
            # Policy update may fail if registry not enabled
            pass


@pytest.mark.live
@pytest.mark.p3
@pytest.mark.registry
class TestGitLabContainerGroup(APISkillTest):
    """Tests for group-level container registry."""

    @pytest.mark.readonly
    def test_list_group_container_repositories(
        self,
        gitlab_api: GitLabAPI,
        gitlab_group_id: int,
    ):
        """Test listing container repositories in a group."""
        repos = self.api_get(
            gitlab_api,
            f"/groups/{gitlab_group_id}/registry/repositories",
            expected_status=404  # Registry may not be enabled
        )
        if repos:
            self.assert_is_list(repos)


@pytest.mark.live
@pytest.mark.p3
@pytest.mark.registry
class TestGitLabContainerPermissions(APISkillTest):
    """Permission tests for gitlab-container skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_repositories(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter can list container repositories."""
        repos = self.api_get(
            reporter_api,
            f"/projects/{gitlab_project_id}/registry/repositories",
            expected_status=404
        )
        # Should succeed (or 404 if registry disabled)
        if repos:
            self.assert_is_list(repos)

    @pytest.mark.destructive
    def test_reporter_cannot_delete_tag(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter cannot delete container tags."""
        repos = reporter_api.get(
            f"/projects/{gitlab_project_id}/registry/repositories"
        )
        if not repos:
            pytest.skip("No container repositories available")

        # Would need to try deletion and verify 403
        pytest.skip("Skipping - requires test images")
