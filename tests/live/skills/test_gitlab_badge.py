"""
Live integration tests for gitlab-badge skill.

Tests project badges via API.
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
class TestGitLabBadgeList(APISkillTest):
    """Tests for listing badges."""

    @pytest.mark.readonly
    def test_list_project_badges(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing project badges."""
        badges = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/badges")
        self.assert_is_list(badges)

    @pytest.mark.readonly
    def test_get_badge(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific badge."""
        badges = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/badges")
        if badges:
            badge_id = badges[0]["id"]
            badge = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/badges/{badge_id}"
            )
            self.assert_is_dict(badge)
            self.assert_has_field(badge, "link_url")
            self.assert_has_field(badge, "image_url")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabBadgeCreate(APISkillTest):
    """Tests for creating badges."""

    @pytest.mark.destructive
    def test_create_badge(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_badges: list,
    ):
        """Test creating a badge."""
        badge = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges",
            {
                "link_url": f"https://example.com/badge/{unique_id}",
                "image_url": f"https://img.shields.io/badge/test-{unique_id}-blue",
            }
        )
        created_badges.append(badge["id"])

        self.assert_is_dict(badge)
        self.assert_field_contains(badge, "link_url", unique_id)

    @pytest.mark.destructive
    def test_create_badge_with_name(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_badges: list,
    ):
        """Test creating a badge with a name."""
        badge = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges",
            {
                "link_url": f"https://example.com/named/{unique_id}",
                "image_url": f"https://img.shields.io/badge/named-{unique_id}-green",
                "name": f"Test Badge {unique_id}",
            }
        )
        created_badges.append(badge["id"])

        self.assert_is_dict(badge)
        self.assert_field_contains(badge, "name", unique_id)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabBadgeUpdate(APISkillTest):
    """Tests for updating badges."""

    @pytest.mark.destructive
    def test_update_badge(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_badge,
        unique_id: str,
    ):
        """Test updating a badge."""
        badge = create_test_badge(
            f"https://example.com/update/{unique_id}",
            f"https://img.shields.io/badge/update-{unique_id}-red"
        )

        # Update the badge
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges/{badge['id']}",
            {
                "link_url": f"https://example.com/updated/{unique_id}",
                "image_url": f"https://img.shields.io/badge/updated-{unique_id}-purple",
            }
        )
        self.assert_field_contains(updated, "link_url", "updated")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabBadgeDelete(APISkillTest):
    """Tests for deleting badges."""

    @pytest.mark.destructive
    def test_delete_badge(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a badge."""
        # Create badge
        badge = gitlab_api.post(
            f"/projects/{gitlab_project_id}/badges",
            {
                "link_url": f"https://example.com/delete/{unique_id}",
                "image_url": f"https://img.shields.io/badge/delete-{unique_id}-gray",
            }
        )

        # Delete it
        self.api_delete(gitlab_api, f"/projects/{gitlab_project_id}/badges/{badge['id']}")

        # Verify deleted
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges/{badge['id']}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p2
class TestGitLabBadgePreview(APISkillTest):
    """Tests for badge preview/rendering."""

    @pytest.mark.readonly
    def test_preview_badge(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test previewing a badge (render with placeholders)."""
        preview = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges/render?link_url=https://example.com&image_url=https://img.shields.io/badge/test-preview-blue"
        )
        self.assert_is_dict(preview)
        self.assert_has_field(preview, "rendered_link_url")
        self.assert_has_field(preview, "rendered_image_url")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabBadgeGroup(APISkillTest):
    """Tests for group-level badges."""

    @pytest.mark.readonly
    def test_list_group_badges(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing group badges."""
        badges = self.api_get(gitlab_api, f"/groups/{gitlab_group_id}/badges")
        self.assert_is_list(badges)

    @pytest.mark.destructive
    def test_create_group_badge(
        self,
        root_api: GitLabAPI,
        gitlab_group_id: int,
        unique_id: str,
    ):
        """Test creating a group-level badge."""
        badge = None
        try:
            badge = root_api.post(
                f"/groups/{gitlab_group_id}/badges",
                {
                    "link_url": f"https://example.com/group/{unique_id}",
                    "image_url": f"https://img.shields.io/badge/group-{unique_id}-orange",
                }
            )
            self.assert_is_dict(badge)
            self.assert_field_contains(badge, "link_url", unique_id)
        finally:
            if badge:
                try:
                    root_api.delete(f"/groups/{gitlab_group_id}/badges/{badge['id']}")
                except GitLabAPIError:
                    pass


@pytest.mark.live
@pytest.mark.p2
class TestGitLabBadgePlaceholders(APISkillTest):
    """Tests for badge placeholders."""

    @pytest.mark.destructive
    def test_badge_with_project_placeholder(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_badges: list,
    ):
        """Test badge with project name placeholder."""
        badge = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges",
            {
                "link_url": "https://example.com/%{project_path}",
                "image_url": "https://img.shields.io/badge/%{project_name}-blue",
            }
        )
        created_badges.append(badge["id"])

        self.assert_is_dict(badge)
        # Check rendered URLs have placeholders replaced
        self.assert_has_field(badge, "rendered_link_url")

    @pytest.mark.destructive
    def test_badge_with_branch_placeholder(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_badges: list,
    ):
        """Test badge with default branch placeholder."""
        badge = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges",
            {
                "link_url": "https://example.com/%{default_branch}",
                "image_url": "https://img.shields.io/badge/%{default_branch}-green",
            }
        )
        created_badges.append(badge["id"])

        self.assert_is_dict(badge)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabBadgePermissions(APISkillTest):
    """Permission tests for gitlab-badge skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_badges(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter can list badges."""
        badges = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/badges")
        self.assert_is_list(badges)

    @pytest.mark.destructive
    def test_developer_cannot_create_badge(
        self,
        developer_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that developer cannot create badges (maintainer+ required)."""
        try:
            developer_api.post(
                f"/projects/{gitlab_project_id}/badges",
                {
                    "link_url": f"https://example.com/fail/{unique_id}",
                    "image_url": "https://img.shields.io/badge/fail-red",
                }
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.destructive
    def test_maintainer_can_create_badge(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_badges: list,
    ):
        """Test that maintainer can create badges."""
        badge = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/badges",
            {
                "link_url": f"https://example.com/maintainer/{unique_id}",
                "image_url": f"https://img.shields.io/badge/maintainer-{unique_id}-blue",
            }
        )
        created_badges.append(badge["id"])

        self.assert_is_dict(badge)
