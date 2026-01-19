"""
Live integration tests for gitlab-discussion skill.

Tests MR/Issue discussions via API.
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
class TestGitLabDiscussionIssue(APISkillTest):
    """Tests for issue discussions."""

    @pytest.mark.readonly
    def test_list_issue_discussions(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing discussions on an issue."""
        discussions = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues/1/discussions"
        )
        self.assert_is_list(discussions)

    @pytest.mark.destructive
    def test_create_issue_discussion(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_issue,
        unique_id: str,
    ):
        """Test creating a discussion on an issue."""
        issue = create_test_issue(f"Discussion Issue {unique_id}")

        discussion = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/discussions",
            {"body": f"Test discussion {unique_id}"}
        )
        self.assert_is_dict(discussion)
        self.assert_has_field(discussion, "id")
        self.assert_has_field(discussion, "notes")

    @pytest.mark.destructive
    def test_reply_to_issue_discussion(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_issue,
        unique_id: str,
    ):
        """Test replying to an issue discussion."""
        issue = create_test_issue(f"Reply Issue {unique_id}")

        # Create discussion
        discussion = gitlab_api.post(
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/discussions",
            {"body": f"Original discussion {unique_id}"}
        )

        # Reply to it
        reply = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/discussions/{discussion['id']}/notes",
            {"body": f"Reply to discussion {unique_id}"}
        )
        self.assert_is_dict(reply)
        self.assert_has_field(reply, "body")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabDiscussionMR(APISkillTest):
    """Tests for merge request discussions."""

    @pytest.mark.readonly
    def test_list_mr_discussions(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing discussions on a merge request."""
        discussions = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/1/discussions",
            expected_status=404  # MR may not exist
        )
        if discussions:
            self.assert_is_list(discussions)

    @pytest.mark.destructive
    def test_create_mr_discussion(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_mr,
        unique_id: str,
    ):
        """Test creating a discussion on a merge request."""
        mr = create_test_mr(f"Discussion MR {unique_id}")

        discussion = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/{mr['iid']}/discussions",
            {"body": f"Test MR discussion {unique_id}"}
        )
        self.assert_is_dict(discussion)
        self.assert_has_field(discussion, "id")

    @pytest.mark.destructive
    def test_resolve_mr_discussion(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_mr,
        unique_id: str,
    ):
        """Test resolving a merge request discussion."""
        mr = create_test_mr(f"Resolve MR {unique_id}")

        # Create discussion
        discussion = gitlab_api.post(
            f"/projects/{gitlab_project_id}/merge_requests/{mr['iid']}/discussions",
            {"body": f"Discussion to resolve {unique_id}"}
        )

        # Resolve it
        resolved = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/{mr['iid']}/discussions/{discussion['id']}",
            {"resolved": True}
        )
        self.assert_is_dict(resolved)

    @pytest.mark.destructive
    def test_unresolve_mr_discussion(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_mr,
        unique_id: str,
    ):
        """Test unresolving a merge request discussion."""
        mr = create_test_mr(f"Unresolve MR {unique_id}")

        # Create and resolve discussion
        discussion = gitlab_api.post(
            f"/projects/{gitlab_project_id}/merge_requests/{mr['iid']}/discussions",
            {"body": f"Discussion to unresolve {unique_id}"}
        )
        gitlab_api.put(
            f"/projects/{gitlab_project_id}/merge_requests/{mr['iid']}/discussions/{discussion['id']}",
            {"resolved": True}
        )

        # Unresolve it
        unresolved = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/merge_requests/{mr['iid']}/discussions/{discussion['id']}",
            {"resolved": False}
        )
        self.assert_is_dict(unresolved)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabDiscussionNotes(APISkillTest):
    """Tests for discussion notes."""

    @pytest.mark.readonly
    def test_list_issue_notes(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing notes on an issue."""
        notes = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues/1/notes"
        )
        self.assert_is_list(notes)

    @pytest.mark.destructive
    def test_create_issue_note(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_issue,
        unique_id: str,
    ):
        """Test creating a note on an issue."""
        issue = create_test_issue(f"Note Issue {unique_id}")

        note = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/notes",
            {"body": f"Test note {unique_id}"}
        )
        self.assert_is_dict(note)
        self.assert_field_contains(note, "body", unique_id)

    @pytest.mark.destructive
    def test_update_issue_note(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_issue,
        unique_id: str,
    ):
        """Test updating a note on an issue."""
        issue = create_test_issue(f"Update Note Issue {unique_id}")

        # Create note
        note = gitlab_api.post(
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/notes",
            {"body": "Original note"}
        )

        # Update note
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/notes/{note['id']}",
            {"body": f"Updated note {unique_id}"}
        )
        self.assert_field_contains(updated, "body", "Updated")

    @pytest.mark.destructive
    def test_delete_issue_note(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_issue,
        unique_id: str,
    ):
        """Test deleting a note on an issue."""
        issue = create_test_issue(f"Delete Note Issue {unique_id}")

        # Create note
        note = gitlab_api.post(
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/notes",
            {"body": "Note to delete"}
        )

        # Delete note
        self.api_delete(
            gitlab_api,
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/notes/{note['id']}"
        )


@pytest.mark.live
@pytest.mark.p2
class TestGitLabDiscussionPermissions(APISkillTest):
    """Permission tests for gitlab-discussion skill."""

    @pytest.mark.readonly
    def test_reporter_can_read_discussions(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter can read discussions."""
        discussions = self.api_get(
            reporter_api,
            f"/projects/{gitlab_project_id}/issues/1/discussions"
        )
        self.assert_is_list(discussions)

    @pytest.mark.destructive
    def test_reporter_can_create_note(
        self,
        reporter_api: GitLabAPI,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_issue,
        unique_id: str,
    ):
        """Test that reporter can create notes."""
        issue = create_test_issue(f"Reporter Note Issue {unique_id}")

        # Reporter should be able to comment
        note = reporter_api.post(
            f"/projects/{gitlab_project_id}/issues/{issue['iid']}/notes",
            {"body": f"Reporter note {unique_id}"}
        )
        self.assert_is_dict(note)
