"""
Live integration tests for gitlab-label skill.

Tests label operations via glab CLI.
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
class TestGitLabLabelList(CLISkillTest):
    """Tests for listing labels."""

    @pytest.mark.readonly
    def test_list_labels(self, run_glab, gitlab_project: str):
        """Test listing all labels."""
        result = self.run_command(run_glab, "label", "list", repo=gitlab_project)
        self.assert_success(result)
        # Should contain labels created by setup
        self.assert_output_contains(result, "bug")

    @pytest.mark.readonly
    def test_list_labels_with_search(self, run_glab, gitlab_project: str):
        """Test listing labels with search filter."""
        result = self.run_command(
            run_glab, "label", "list",
            "--search", "priority",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p1
class TestGitLabLabelCreate(CLISkillTest):
    """Tests for creating labels."""

    @pytest.mark.destructive
    def test_create_label(
        self,
        run_glab,
        gitlab_project: str,
        unique_id: str,
        created_labels: list,
    ):
        """Test creating a label."""
        label_name = f"test-label-{unique_id}"

        result = self.run_command(
            run_glab, "label", "create", label_name,
            "--color", "#ff5500",
            "--description", f"Test label {unique_id}",
            repo=gitlab_project
        )
        self.assert_success(result)
        created_labels.append(label_name)

    @pytest.mark.destructive
    def test_create_scoped_label(
        self,
        run_glab,
        gitlab_project: str,
        unique_id: str,
        created_labels: list,
    ):
        """Test creating a scoped label."""
        label_name = f"scope-{unique_id}::value"

        result = self.run_command(
            run_glab, "label", "create", label_name,
            "--color", "#00ff55",
            repo=gitlab_project
        )
        self.assert_success(result)
        created_labels.append(label_name)


@pytest.mark.live
@pytest.mark.p1
class TestGitLabLabelAPI(APISkillTest):
    """API tests for gitlab-label skill."""

    @pytest.mark.readonly
    def test_list_labels_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing labels via API."""
        labels = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/labels")
        self.assert_is_list(labels, min_length=1)

        # Verify expected labels exist
        label_names = [l["name"] for l in labels]
        assert "bug" in label_names
        assert "enhancement" in label_names

    @pytest.mark.readonly
    def test_get_label_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific label."""
        label = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/labels/bug")
        self.assert_is_dict(label)
        self.assert_field_equals(label, "name", "bug")

    @pytest.mark.destructive
    def test_create_label_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_labels: list,
    ):
        """Test creating label via API."""
        label_name = f"api-label-{unique_id}"

        label = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/labels",
            {
                "name": label_name,
                "color": "#123456",
                "description": f"API created label {unique_id}",
            }
        )
        created_labels.append(label_name)

        self.assert_is_dict(label)
        self.assert_field_equals(label, "name", label_name)

    @pytest.mark.destructive
    def test_update_label_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_label,
        unique_id: str,
    ):
        """Test updating a label."""
        label = create_test_label(f"update-label-{unique_id}", color="#000000")

        # Update the label
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/labels/{label['name'].replace(' ', '%20')}",
            {"color": "#ffffff", "description": "Updated description"}
        )
        self.assert_field_equals(updated, "color", "#ffffff")

    @pytest.mark.destructive
    def test_delete_label_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a label."""
        label_name = f"delete-label-{unique_id}"

        # Create label
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/labels",
            {"name": label_name, "color": "#abcdef"}
        )

        # Delete label
        result = self.api_delete(
            gitlab_api,
            f"/projects/{gitlab_project_id}/labels/{label_name}"
        )
        # Should succeed (returns None or empty)

        # Verify deleted
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/labels/{label_name}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p1
class TestGitLabLabelGroup(APISkillTest):
    """Tests for group-level labels."""

    @pytest.mark.readonly
    def test_list_group_labels(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing group labels."""
        labels = self.api_get(gitlab_api, f"/groups/{gitlab_group_id}/labels")
        self.assert_is_list(labels)

    @pytest.mark.destructive
    def test_create_group_label(
        self,
        root_api: GitLabAPI,
        gitlab_group_id: int,
        unique_id: str,
    ):
        """Test creating a group-level label."""
        label_name = f"group-label-{unique_id}"

        try:
            label = root_api.post(
                f"/groups/{gitlab_group_id}/labels",
                {"name": label_name, "color": "#654321"}
            )
            self.assert_is_dict(label)
            self.assert_field_equals(label, "name", label_name)
        finally:
            # Cleanup
            try:
                root_api.delete(f"/groups/{gitlab_group_id}/labels/{label_name}")
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p1
class TestGitLabLabelSubscription(APISkillTest):
    """Tests for label subscriptions."""

    @pytest.mark.destructive
    def test_subscribe_to_label(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test subscribing to a label."""
        # Subscribe to bug label
        result = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/labels/bug/subscribe",
            {}
        )
        self.assert_is_dict(result)

        # Unsubscribe
        self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/labels/bug/unsubscribe",
            {}
        )


@pytest.mark.live
@pytest.mark.p1
class TestGitLabLabelPermissions(APISkillTest):
    """Permission tests for gitlab-label skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_labels(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list labels."""
        labels = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/labels")
        self.assert_is_list(labels)

    @pytest.mark.destructive
    def test_reporter_cannot_create_label(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that reporter cannot create labels."""
        try:
            reporter_api.post(
                f"/projects/{gitlab_project_id}/labels",
                {"name": f"fail-label-{unique_id}", "color": "#ffffff"}
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.destructive
    def test_developer_can_create_label(
        self,
        developer_api: GitLabAPI,
        gitlab_api: GitLabAPI,  # For cleanup
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that developer can create labels."""
        label_name = f"dev-label-{unique_id}"

        try:
            label = developer_api.post(
                f"/projects/{gitlab_project_id}/labels",
                {"name": label_name, "color": "#aabbcc"}
            )
            self.assert_is_dict(label)
        finally:
            # Cleanup with maintainer
            try:
                gitlab_api.delete(f"/projects/{gitlab_project_id}/labels/{label_name}")
            except GitLabAPIError:
                pass
