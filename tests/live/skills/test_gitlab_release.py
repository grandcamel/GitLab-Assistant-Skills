"""
Live integration tests for gitlab-release skill.

Tests release operations via glab CLI.
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
@pytest.mark.p1
class TestGitLabReleaseList(CLISkillTest):
    """Tests for listing releases."""

    @pytest.mark.readonly
    def test_list_releases(self, run_glab, gitlab_project: str):
        """Test listing all releases."""
        result = self.run_command(run_glab, "release", "list", repo=gitlab_project)
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p1
class TestGitLabReleaseCreate(CLISkillTest):
    """Tests for creating releases."""

    @pytest.mark.destructive
    def test_create_release(
        self,
        run_glab,
        gitlab_project: str,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test creating a release."""
        tag_name = f"v0.0.1-test-{unique_id}"

        try:
            result = self.run_command(
                run_glab, "release", "create", tag_name,
                "--name", f"Test Release {unique_id}",
                "--notes", f"Test release notes for {unique_id}",
                repo=gitlab_project
            )
            self.assert_success(result)
        finally:
            # Cleanup - delete release and tag
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/releases/{tag_name}")
            except GitLabAPIError:
                pass
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p1
class TestGitLabReleaseView(CLISkillTest):
    """Tests for viewing releases."""

    @pytest.mark.destructive
    def test_view_release(
        self,
        run_glab,
        gitlab_project: str,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test viewing a specific release."""
        tag_name = f"v0.0.2-view-{unique_id}"

        try:
            # Create release first
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": tag_name,
                    "name": f"View Test Release {unique_id}",
                    "description": "Release for view test",
                }
            )

            # View it
            result = self.run_command(
                run_glab, "release", "view", tag_name,
                repo=gitlab_project
            )
            self.assert_success(result)
            self.assert_output_contains(result, tag_name)
        finally:
            # Cleanup
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/releases/{tag_name}")
            except GitLabAPIError:
                pass
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p1
class TestGitLabReleaseAPI(APISkillTest):
    """API tests for gitlab-release skill."""

    @pytest.mark.readonly
    def test_list_releases_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing releases via API."""
        releases = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/releases")
        self.assert_is_list(releases)

    @pytest.mark.destructive
    def test_create_release_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test creating release via API."""
        tag_name = f"v0.0.3-api-{unique_id}"

        try:
            release = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": tag_name,
                    "name": f"API Release {unique_id}",
                    "description": f"Release created via API {unique_id}",
                    "ref": "main",
                }
            )
            self.assert_is_dict(release)
            self.assert_field_equals(release, "tag_name", tag_name)
        finally:
            # Cleanup
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/releases/{tag_name}")
            except GitLabAPIError:
                pass
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass

    @pytest.mark.destructive
    def test_get_release_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test getting a specific release."""
        tag_name = f"v0.0.4-get-{unique_id}"

        try:
            # Create release
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": tag_name,
                    "name": f"Get Test Release {unique_id}",
                    "description": "Release for get test",
                    "ref": "main",
                }
            )

            # Get it
            release = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/releases/{tag_name}"
            )
            self.assert_is_dict(release)
            self.assert_field_equals(release, "tag_name", tag_name)
        finally:
            # Cleanup
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/releases/{tag_name}")
            except GitLabAPIError:
                pass
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass

    @pytest.mark.destructive
    def test_update_release_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test updating a release."""
        tag_name = f"v0.0.5-update-{unique_id}"

        try:
            # Create release
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": tag_name,
                    "name": f"Update Test Release {unique_id}",
                    "description": "Original description",
                    "ref": "main",
                }
            )

            # Update it
            updated = self.api_put(
                gitlab_api,
                f"/projects/{gitlab_project_id}/releases/{tag_name}",
                {"description": "Updated description"}
            )
            self.assert_field_equals(updated, "description", "Updated description")
        finally:
            # Cleanup
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/releases/{tag_name}")
            except GitLabAPIError:
                pass
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass

    @pytest.mark.destructive
    def test_delete_release_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a release."""
        tag_name = f"v0.0.6-delete-{unique_id}"

        try:
            # Create release
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": tag_name,
                    "name": f"Delete Test Release {unique_id}",
                    "description": "Release to delete",
                    "ref": "main",
                }
            )

            # Delete release
            self.api_delete(gitlab_api, f"/projects/{gitlab_project_id}/releases/{tag_name}")

            # Verify deleted
            result = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/releases/{tag_name}",
                expected_status=404
            )
            assert result is None
        finally:
            # Cleanup tag (release is already deleted)
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p1
class TestGitLabReleaseLinks(APISkillTest):
    """Tests for release links/assets."""

    @pytest.mark.destructive
    def test_create_release_link(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test creating a release link."""
        tag_name = f"v0.0.7-link-{unique_id}"

        try:
            # Create release
            gitlab_api.post(
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": tag_name,
                    "name": f"Link Test Release {unique_id}",
                    "description": "Release for link test",
                    "ref": "main",
                }
            )

            # Add link
            link = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/releases/{tag_name}/assets/links",
                {
                    "name": "Documentation",
                    "url": "https://example.com/docs",
                    "link_type": "other",
                }
            )
            self.assert_is_dict(link)
            self.assert_field_equals(link, "name", "Documentation")
        finally:
            # Cleanup
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/releases/{tag_name}")
            except GitLabAPIError:
                pass
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p1
class TestGitLabReleasePermissions(APISkillTest):
    """Permission tests for gitlab-release skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_releases(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list releases."""
        releases = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/releases")
        self.assert_is_list(releases)

    @pytest.mark.destructive
    def test_reporter_cannot_create_release(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that reporter cannot create releases."""
        try:
            reporter_api.post(
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": f"v0.0.8-fail-{unique_id}",
                    "name": "Should Fail",
                    "ref": "main",
                }
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.destructive
    def test_developer_can_create_release(
        self,
        developer_api: GitLabAPI,
        gitlab_api: GitLabAPI,  # For cleanup
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that developer can create releases."""
        tag_name = f"v0.0.9-dev-{unique_id}"

        try:
            release = developer_api.post(
                f"/projects/{gitlab_project_id}/releases",
                {
                    "tag_name": tag_name,
                    "name": f"Dev Release {unique_id}",
                    "ref": "main",
                }
            )
            self.assert_is_dict(release)
        finally:
            # Cleanup with maintainer
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/releases/{tag_name}")
            except GitLabAPIError:
                pass
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/repository/tags/{tag_name}")
            except GitLabAPIError:
                pass
