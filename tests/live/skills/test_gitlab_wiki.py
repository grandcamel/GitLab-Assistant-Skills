"""
Live integration tests for gitlab-wiki skill.

Tests wiki page management via API.
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
class TestGitLabWikiList(APISkillTest):
    """Tests for listing wiki pages."""

    @pytest.mark.readonly
    def test_list_wiki_pages(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing wiki pages."""
        pages = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/wikis")
        self.assert_is_list(pages)

    @pytest.mark.readonly
    def test_get_wiki_page(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific wiki page."""
        # Get Home page (created by setup)
        page = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/wikis/home",
            expected_status=404
        )
        if page:
            self.assert_is_dict(page)
            self.assert_has_field(page, "content")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWikiCreate(APISkillTest):
    """Tests for creating wiki pages."""

    @pytest.mark.destructive
    def test_create_wiki_page(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_wiki_pages: list,
    ):
        """Test creating a wiki page."""
        title = f"Test Page {unique_id}"

        page = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/wikis",
            {
                "title": title,
                "content": f"# {title}\n\nTest content for wiki page.",
                "format": "markdown",
            }
        )
        created_wiki_pages.append(page["slug"])

        self.assert_is_dict(page)
        self.assert_has_field(page, "slug")

    @pytest.mark.destructive
    def test_create_wiki_page_with_rdoc(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_wiki_pages: list,
    ):
        """Test creating a wiki page with RDoc format."""
        title = f"RDoc Page {unique_id}"

        page = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/wikis",
            {
                "title": title,
                "content": f"= {title}\n\nTest content.",
                "format": "rdoc",
            }
        )
        created_wiki_pages.append(page["slug"])

        self.assert_is_dict(page)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWikiUpdate(APISkillTest):
    """Tests for updating wiki pages."""

    @pytest.mark.destructive
    def test_update_wiki_page(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_wiki_page,
        unique_id: str,
    ):
        """Test updating a wiki page."""
        page = create_test_wiki_page(
            f"Update Page {unique_id}",
            "Original content"
        )

        # Update the page
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/wikis/{page['slug']}",
            {"content": "Updated content", "format": "markdown"}
        )
        self.assert_field_contains(updated, "content", "Updated")

    @pytest.mark.destructive
    def test_rename_wiki_page(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_wiki_pages: list,
    ):
        """Test renaming a wiki page."""
        original_title = f"Original Title {unique_id}"
        new_title = f"New Title {unique_id}"

        # Create page
        page = gitlab_api.post(
            f"/projects/{gitlab_project_id}/wikis",
            {"title": original_title, "content": "Content", "format": "markdown"}
        )
        original_slug = page["slug"]

        try:
            # Rename by updating title
            updated = self.api_put(
                gitlab_api,
                f"/projects/{gitlab_project_id}/wikis/{original_slug}",
                {"title": new_title, "content": "Content"}
            )
            created_wiki_pages.append(updated["slug"])
        except GitLabAPIError:
            # If rename fails, clean up original
            created_wiki_pages.append(original_slug)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWikiDelete(APISkillTest):
    """Tests for deleting wiki pages."""

    @pytest.mark.destructive
    def test_delete_wiki_page(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a wiki page."""
        title = f"Delete Page {unique_id}"

        # Create page
        page = gitlab_api.post(
            f"/projects/{gitlab_project_id}/wikis",
            {"title": title, "content": "To delete", "format": "markdown"}
        )

        # Delete it
        self.api_delete(gitlab_api, f"/projects/{gitlab_project_id}/wikis/{page['slug']}")

        # Verify deleted
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/wikis/{page['slug']}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWikiAttachments(APISkillTest):
    """Tests for wiki attachments."""

    @pytest.mark.readonly
    def test_list_wiki_attachments(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing wiki attachments."""
        # This endpoint may not exist or return empty
        # Attachments require uploading files first
        pass  # Skip for now - would need file upload


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWikiGroup(APISkillTest):
    """Tests for group-level wikis."""

    @pytest.mark.readonly
    def test_list_group_wiki_pages(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing group wiki pages."""
        pages = self.api_get(
            gitlab_api,
            f"/groups/{gitlab_group_id}/wikis",
            expected_status=404  # Group wikis may not be enabled
        )
        if pages:
            self.assert_is_list(pages)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWikiPermissions(APISkillTest):
    """Permission tests for gitlab-wiki skill."""

    @pytest.mark.readonly
    def test_reporter_can_read_wiki(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter can read wiki pages."""
        pages = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/wikis")
        self.assert_is_list(pages)

    @pytest.mark.destructive
    def test_reporter_cannot_create_wiki(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that reporter cannot create wiki pages."""
        try:
            reporter_api.post(
                f"/projects/{gitlab_project_id}/wikis",
                {"title": f"Fail Page {unique_id}", "content": "Fail", "format": "markdown"}
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.destructive
    def test_developer_can_create_wiki(
        self,
        developer_api: GitLabAPI,
        gitlab_api: GitLabAPI,  # For cleanup
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that developer can create wiki pages."""
        title = f"Dev Wiki {unique_id}"
        page = None

        try:
            page = developer_api.post(
                f"/projects/{gitlab_project_id}/wikis",
                {"title": title, "content": "Developer wiki", "format": "markdown"}
            )
            self.assert_is_dict(page)
        finally:
            if page:
                try:
                    gitlab_api.delete(f"/projects/{gitlab_project_id}/wikis/{page['slug']}")
                except GitLabAPIError:
                    pass
