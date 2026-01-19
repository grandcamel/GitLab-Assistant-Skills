"""
Live integration tests for gitlab-milestone skill.

Tests milestone operations via glab CLI.
"""

import pytest
from datetime import datetime, timedelta

from tests.live.skills.base import CLISkillTest, APISkillTest
try:
    # When running under pytest, conftest is loaded directly
    from conftest import GitLabAPI, GitLabAPIError
except ImportError:
    # When running directly, use the full path
    from tests.live.conftest import GitLabAPI, GitLabAPIError


@pytest.mark.live
@pytest.mark.p1
class TestGitLabMilestoneList(CLISkillTest):
    """Tests for listing milestones."""

    @pytest.mark.readonly
    def test_list_milestones(self, run_glab, gitlab_project: str):
        """Test listing all milestones."""
        result = self.run_command(run_glab, "milestone", "list", repo=gitlab_project)
        self.assert_success(result)
        # Should contain milestones created by setup
        self.assert_output_contains(result, "v1.0.0")


@pytest.mark.live
@pytest.mark.p1
class TestGitLabMilestoneCreate(CLISkillTest):
    """Tests for creating milestones."""

    @pytest.mark.destructive
    def test_create_milestone(
        self,
        run_glab,
        gitlab_project: str,
        unique_id: str,
        created_milestones: list,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test creating a milestone."""
        title = f"v0.0.1-test-{unique_id}"
        due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        result = self.run_command(
            run_glab, "milestone", "create",
            "--title", title,
            "--description", f"Test milestone {unique_id}",
            "--due-date", due_date,
            repo=gitlab_project
        )
        self.assert_success(result)

        # Get milestone ID for cleanup
        milestones = gitlab_api.get(f"/projects/{gitlab_project_id}/milestones?search={title}")
        if milestones:
            created_milestones.append(milestones[0]["id"])


@pytest.mark.live
@pytest.mark.p1
class TestGitLabMilestoneAPI(APISkillTest):
    """API tests for gitlab-milestone skill."""

    @pytest.mark.readonly
    def test_list_milestones_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing milestones via API."""
        milestones = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/milestones")
        self.assert_is_list(milestones, min_length=1)

        # Verify expected milestones exist
        titles = [m["title"] for m in milestones]
        assert "v1.0.0" in titles

    @pytest.mark.readonly
    def test_get_milestone_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific milestone."""
        # Get milestones first
        milestones = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/milestones")
        if milestones:
            milestone_id = milestones[0]["id"]
            milestone = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/milestones/{milestone_id}"
            )
            self.assert_is_dict(milestone)
            self.assert_has_field(milestone, "title")

    @pytest.mark.readonly
    def test_list_active_milestones(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing only active milestones."""
        milestones = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/milestones?state=active"
        )
        self.assert_is_list(milestones)

    @pytest.mark.destructive
    def test_create_milestone_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_milestones: list,
    ):
        """Test creating milestone via API."""
        due_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")

        milestone = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/milestones",
            {
                "title": f"API Milestone {unique_id}",
                "description": f"Created via API {unique_id}",
                "due_date": due_date,
            }
        )
        created_milestones.append(milestone["id"])

        self.assert_is_dict(milestone)
        self.assert_field_contains(milestone, "title", unique_id)

    @pytest.mark.destructive
    def test_update_milestone_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_milestone,
        unique_id: str,
    ):
        """Test updating a milestone."""
        milestone = create_test_milestone(f"Update Milestone {unique_id}")

        # Update the milestone
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/milestones/{milestone['id']}",
            {"description": "Updated description"}
        )
        self.assert_field_equals(updated, "description", "Updated description")

    @pytest.mark.destructive
    def test_close_milestone_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_milestone,
        unique_id: str,
    ):
        """Test closing a milestone."""
        milestone = create_test_milestone(f"Close Milestone {unique_id}")

        # Close the milestone
        closed = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/milestones/{milestone['id']}",
            {"state_event": "close"}
        )
        self.assert_field_equals(closed, "state", "closed")

    @pytest.mark.destructive
    def test_delete_milestone_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a milestone."""
        # Create milestone
        milestone = gitlab_api.post(
            f"/projects/{gitlab_project_id}/milestones",
            {"title": f"Delete Milestone {unique_id}"}
        )

        # Delete milestone
        self.api_delete(
            gitlab_api,
            f"/projects/{gitlab_project_id}/milestones/{milestone['id']}"
        )

        # Verify deleted
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/milestones/{milestone['id']}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p1
class TestGitLabMilestoneIssues(APISkillTest):
    """Tests for milestone issues."""

    @pytest.mark.readonly
    def test_list_milestone_issues(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing issues in a milestone."""
        # Get a milestone
        milestones = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/milestones")
        if milestones:
            milestone_id = milestones[0]["id"]
            issues = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/milestones/{milestone_id}/issues"
            )
            self.assert_is_list(issues)

    @pytest.mark.readonly
    def test_list_milestone_merge_requests(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing merge requests in a milestone."""
        milestones = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/milestones")
        if milestones:
            milestone_id = milestones[0]["id"]
            mrs = self.api_get(
                gitlab_api,
                f"/projects/{gitlab_project_id}/milestones/{milestone_id}/merge_requests"
            )
            self.assert_is_list(mrs)


@pytest.mark.live
@pytest.mark.p1
class TestGitLabMilestoneGroup(APISkillTest):
    """Tests for group-level milestones."""

    @pytest.mark.readonly
    def test_list_group_milestones(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing group milestones."""
        milestones = self.api_get(gitlab_api, f"/groups/{gitlab_group_id}/milestones")
        self.assert_is_list(milestones)

    @pytest.mark.destructive
    def test_create_group_milestone(
        self,
        root_api: GitLabAPI,
        gitlab_group_id: int,
        unique_id: str,
    ):
        """Test creating a group-level milestone."""
        milestone = None
        try:
            milestone = root_api.post(
                f"/groups/{gitlab_group_id}/milestones",
                {"title": f"Group Milestone {unique_id}"}
            )
            self.assert_is_dict(milestone)
            self.assert_field_contains(milestone, "title", unique_id)
        finally:
            # Cleanup
            if milestone:
                try:
                    root_api.delete(f"/groups/{gitlab_group_id}/milestones/{milestone['id']}")
                except GitLabAPIError:
                    pass


@pytest.mark.live
@pytest.mark.p1
class TestGitLabMilestonePermissions(APISkillTest):
    """Permission tests for gitlab-milestone skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_milestones(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list milestones."""
        milestones = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/milestones")
        self.assert_is_list(milestones)

    @pytest.mark.destructive
    def test_reporter_cannot_create_milestone(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that reporter cannot create milestones."""
        try:
            reporter_api.post(
                f"/projects/{gitlab_project_id}/milestones",
                {"title": f"Fail Milestone {unique_id}"}
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.destructive
    def test_developer_can_create_milestone(
        self,
        developer_api: GitLabAPI,
        gitlab_api: GitLabAPI,  # For cleanup
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that developer can create milestones."""
        milestone = None
        try:
            milestone = developer_api.post(
                f"/projects/{gitlab_project_id}/milestones",
                {"title": f"Dev Milestone {unique_id}"}
            )
            self.assert_is_dict(milestone)
        finally:
            # Cleanup with maintainer
            if milestone:
                try:
                    gitlab_api.delete(f"/projects/{gitlab_project_id}/milestones/{milestone['id']}")
                except GitLabAPIError:
                    pass
