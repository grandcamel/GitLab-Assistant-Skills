"""
Live integration tests for gitlab-webhook skill.

Tests webhook management via API.
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
class TestGitLabWebhookList(APISkillTest):
    """Tests for listing webhooks."""

    @pytest.mark.readonly
    def test_list_project_webhooks(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing project webhooks."""
        hooks = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/hooks")
        self.assert_is_list(hooks)

    @pytest.mark.readonly
    def test_get_webhook(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific webhook."""
        hooks = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/hooks")
        if hooks:
            hook_id = hooks[0]["id"]
            hook = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/hooks/{hook_id}")
            self.assert_is_dict(hook)
            self.assert_has_field(hook, "url")


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWebhookCreate(APISkillTest):
    """Tests for creating webhooks."""

    @pytest.mark.destructive
    def test_create_webhook(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_webhooks: list,
    ):
        """Test creating a webhook."""
        hook = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/hooks",
            {
                "url": f"https://example.com/hook/{unique_id}",
                "push_events": True,
            }
        )
        created_webhooks.append(hook["id"])

        self.assert_is_dict(hook)
        self.assert_field_contains(hook, "url", unique_id)

    @pytest.mark.destructive
    def test_create_webhook_with_events(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_webhooks: list,
    ):
        """Test creating a webhook with multiple events."""
        hook = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/hooks",
            {
                "url": f"https://example.com/events/{unique_id}",
                "push_events": True,
                "merge_requests_events": True,
                "issues_events": True,
                "note_events": True,
                "pipeline_events": True,
            }
        )
        created_webhooks.append(hook["id"])

        self.assert_is_dict(hook)
        self.assert_field_equals(hook, "push_events", True)
        self.assert_field_equals(hook, "merge_requests_events", True)
        self.assert_field_equals(hook, "issues_events", True)

    @pytest.mark.destructive
    def test_create_webhook_with_token(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_webhooks: list,
    ):
        """Test creating a webhook with a secret token."""
        hook = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/hooks",
            {
                "url": f"https://example.com/secret/{unique_id}",
                "push_events": True,
                "token": f"secret-token-{unique_id}",
            }
        )
        created_webhooks.append(hook["id"])

        self.assert_is_dict(hook)
        # Token is not returned in response for security


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWebhookUpdate(APISkillTest):
    """Tests for updating webhooks."""

    @pytest.mark.destructive
    def test_update_webhook(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_webhook,
        unique_id: str,
    ):
        """Test updating a webhook."""
        hook = create_test_webhook(f"https://example.com/update/{unique_id}")

        # Update the webhook
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/hooks/{hook['id']}",
            {
                "url": f"https://example.com/updated/{unique_id}",
                "merge_requests_events": True,
            }
        )
        self.assert_field_contains(updated, "url", "updated")
        self.assert_field_equals(updated, "merge_requests_events", True)

    @pytest.mark.destructive
    def test_enable_disable_webhook_events(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_webhook,
        unique_id: str,
    ):
        """Test enabling and disabling webhook events."""
        hook = create_test_webhook(f"https://example.com/toggle/{unique_id}")

        # Enable pipeline events
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/hooks/{hook['id']}",
            {"pipeline_events": True}
        )
        self.assert_field_equals(updated, "pipeline_events", True)

        # Disable pipeline events
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/hooks/{hook['id']}",
            {"pipeline_events": False}
        )
        self.assert_field_equals(updated, "pipeline_events", False)


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWebhookDelete(APISkillTest):
    """Tests for deleting webhooks."""

    @pytest.mark.destructive
    def test_delete_webhook(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a webhook."""
        # Create webhook
        hook = gitlab_api.post(
            f"/projects/{gitlab_project_id}/hooks",
            {"url": f"https://example.com/delete/{unique_id}", "push_events": True}
        )

        # Delete it
        self.api_delete(gitlab_api, f"/projects/{gitlab_project_id}/hooks/{hook['id']}")

        # Verify deleted
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/hooks/{hook['id']}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWebhookTest(APISkillTest):
    """Tests for testing webhooks."""

    @pytest.mark.destructive
    def test_test_webhook(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_webhook,
        unique_id: str,
    ):
        """Test triggering a test webhook."""
        hook = create_test_webhook(f"https://httpbin.org/post?id={unique_id}")

        # Trigger test
        # Note: This will actually send a request to the URL
        try:
            result = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/hooks/{hook['id']}/test/push_events",
                {}
            )
            # Result contains test response info
            self.assert_is_dict(result)
        except GitLabAPIError:
            # Test might fail if URL is unreachable, that's OK
            pass


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWebhookGroup(APISkillTest):
    """Tests for group-level webhooks."""

    @pytest.mark.readonly
    def test_list_group_webhooks(self, root_api: GitLabAPI, gitlab_group_id: int):
        """Test listing group webhooks."""
        hooks = self.api_get(root_api, f"/groups/{gitlab_group_id}/hooks")
        self.assert_is_list(hooks)

    @pytest.mark.destructive
    def test_create_group_webhook(
        self,
        root_api: GitLabAPI,
        gitlab_group_id: int,
        unique_id: str,
    ):
        """Test creating a group-level webhook."""
        hook = None
        try:
            hook = root_api.post(
                f"/groups/{gitlab_group_id}/hooks",
                {
                    "url": f"https://example.com/group/{unique_id}",
                    "push_events": True,
                }
            )
            self.assert_is_dict(hook)
            self.assert_field_contains(hook, "url", unique_id)
        finally:
            if hook:
                try:
                    root_api.delete(f"/groups/{gitlab_group_id}/hooks/{hook['id']}")
                except GitLabAPIError:
                    pass


@pytest.mark.live
@pytest.mark.p2
class TestGitLabWebhookPermissions(APISkillTest):
    """Permission tests for gitlab-webhook skill."""

    @pytest.mark.readonly
    def test_developer_cannot_list_webhooks(
        self,
        developer_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that developer cannot list webhooks (maintainer+ required)."""
        try:
            developer_api.get(f"/projects/{gitlab_project_id}/hooks")
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.destructive
    def test_reporter_cannot_create_webhook(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that reporter cannot create webhooks."""
        try:
            reporter_api.post(
                f"/projects/{gitlab_project_id}/hooks",
                {"url": f"https://example.com/fail/{unique_id}", "push_events": True}
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)
