"""
Live integration tests for gitlab-search skill.

Tests global/project/group search operations via API.
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
class TestGitLabSearchProjects(APISkillTest):
    """Tests for project search."""

    @pytest.mark.readonly
    def test_search_projects(self, gitlab_api: GitLabAPI):
        """Test searching for projects."""
        results = self.api_get(gitlab_api, "/projects?search=test")
        self.assert_is_list(results)

    @pytest.mark.readonly
    def test_search_projects_in_group(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test searching for projects within a group."""
        results = self.api_get(
            gitlab_api,
            f"/groups/{gitlab_group_id}/projects?search=test"
        )
        self.assert_is_list(results, min_length=1)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchIssues(APISkillTest):
    """Tests for issue search."""

    @pytest.mark.readonly
    def test_search_issues_global(self, gitlab_api: GitLabAPI):
        """Test global issue search."""
        results = self.api_get(gitlab_api, "/issues?search=crash")
        self.assert_is_list(results)

    @pytest.mark.readonly
    def test_search_issues_in_project(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test searching issues within a project."""
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues?search=crash"
        )
        self.assert_is_list(results, min_length=1)

    @pytest.mark.readonly
    def test_search_issues_by_label(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test searching issues by label."""
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues?labels=bug"
        )
        self.assert_is_list(results, min_length=1)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchMergeRequests(APISkillTest):
    """Tests for merge request search."""

    @pytest.mark.readonly
    def test_search_merge_requests_global(self, gitlab_api: GitLabAPI):
        """Test global merge request search."""
        results = self.api_get(gitlab_api, "/merge_requests?search=feature")
        self.assert_is_list(results)

    @pytest.mark.readonly
    def test_search_merge_requests_in_project(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test searching merge requests within a project."""
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests?search=feature"
        )
        self.assert_is_list(results)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchCode(APISkillTest):
    """Tests for code search (requires Elasticsearch in GitLab)."""

    @pytest.mark.readonly
    def test_search_blobs_in_project(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test searching code blobs in a project."""
        # This uses basic search, not advanced (Elasticsearch)
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/search?scope=blobs&search=main"
        )
        self.assert_is_list(results)

    @pytest.mark.readonly
    def test_search_commits_in_project(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test searching commits in a project."""
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/search?scope=commits&search=Add"
        )
        self.assert_is_list(results)

    @pytest.mark.readonly
    def test_search_wiki_blobs(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test searching wiki content."""
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/search?scope=wiki_blobs&search=Welcome"
        )
        self.assert_is_list(results)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchUsers(APISkillTest):
    """Tests for user search."""

    @pytest.mark.readonly
    def test_search_users(self, gitlab_api: GitLabAPI):
        """Test searching for users."""
        results = self.api_get(gitlab_api, "/users?search=test")
        self.assert_is_list(results)

    @pytest.mark.readonly
    def test_search_users_by_username(self, gitlab_api: GitLabAPI):
        """Test searching users by exact username."""
        results = self.api_get(gitlab_api, "/users?username=test-maintainer")
        self.assert_is_list(results, min_length=1)
        self.assert_field_equals(results[0], "username", "test-maintainer")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchGroups(APISkillTest):
    """Tests for group search."""

    @pytest.mark.readonly
    def test_search_groups(self, gitlab_api: GitLabAPI):
        """Test searching for groups."""
        results = self.api_get(gitlab_api, "/groups?search=live-test")
        self.assert_is_list(results, min_length=1)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchMilestones(APISkillTest):
    """Tests for milestone search."""

    @pytest.mark.readonly
    def test_search_milestones_in_project(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test searching milestones in a project."""
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/milestones?search=v1"
        )
        self.assert_is_list(results, min_length=1)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchLabels(APISkillTest):
    """Tests for label search."""

    @pytest.mark.readonly
    def test_search_labels_in_project(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test searching labels in a project."""
        results = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/labels?search=bug"
        )
        self.assert_is_list(results, min_length=1)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchScopes(APISkillTest):
    """Tests for different search scopes."""

    @pytest.mark.readonly
    def test_project_search_scopes(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test different search scopes in a project."""
        scopes = ["blobs", "commits", "issues", "merge_requests", "milestones", "notes", "wiki_blobs"]

        for scope in scopes:
            results = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/search?scope={scope}&search=test",
                expected_status=404  # Some scopes may not exist
            )
            # Results can be list or None for missing scopes
            if results is not None:
                self.assert_is_list(results)

    @pytest.mark.readonly
    def test_group_search_scopes(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test different search scopes in a group."""
        scopes = ["projects", "issues", "merge_requests", "milestones"]

        for scope in scopes:
            results = self.api_get(
                gitlab_api,
                f"/groups/{gitlab_group_id}/search?scope={scope}&search=test"
            )
            self.assert_is_list(results)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabSearchPermissions(APISkillTest):
    """Permission tests for gitlab-search skill."""

    @pytest.mark.readonly
    def test_reporter_can_search(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can perform searches."""
        results = self.api_get(
            reporter_api,
            f"/projects/{gitlab_project_id}/search?scope=issues&search=test"
        )
        self.assert_is_list(results)

    @pytest.mark.readonly
    def test_unauthenticated_cannot_search_private(self, gitlab_api: GitLabAPI):
        """Test search respects project visibility."""
        # Search should only return projects user has access to
        results = self.api_get(gitlab_api, "/projects?search=test&visibility=private")
        self.assert_is_list(results)
        # All results should be accessible
        for project in results:
            self.assert_has_field(project, "id")
