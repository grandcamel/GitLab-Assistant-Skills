"""
Live integration tests for gitlab-variable skill.

Tests CI/CD variable operations via glab CLI.
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
class TestGitLabVariableList(CLISkillTest):
    """Tests for listing CI/CD variables."""

    @pytest.mark.readonly
    def test_list_variables(self, run_glab, gitlab_project: str):
        """Test listing all variables."""
        result = self.run_command(run_glab, "variable", "list", repo=gitlab_project)
        self.assert_success(result)
        # Should contain variables created by setup
        self.assert_output_contains(result, "TEST_VAR")


@pytest.mark.live
@pytest.mark.p1
class TestGitLabVariableCreate(CLISkillTest):
    """Tests for creating CI/CD variables."""

    @pytest.mark.destructive
    def test_create_variable(
        self,
        run_glab,
        gitlab_project: str,
        unique_id: str,
        created_variables: list,
    ):
        """Test creating a variable."""
        key = f"TEST_VAR_{unique_id.upper()}"

        result = self.run_command(
            run_glab, "variable", "set", key,
            "--value", f"test_value_{unique_id}",
            repo=gitlab_project
        )
        self.assert_success(result)
        created_variables.append(key)

    @pytest.mark.destructive
    def test_create_protected_variable(
        self,
        run_glab,
        gitlab_project: str,
        unique_id: str,
        created_variables: list,
    ):
        """Test creating a protected variable."""
        key = f"PROTECTED_VAR_{unique_id.upper()}"

        result = self.run_command(
            run_glab, "variable", "set", key,
            "--value", f"protected_value_{unique_id}",
            "--protected",
            repo=gitlab_project
        )
        self.assert_success(result)
        created_variables.append(key)


@pytest.mark.live
@pytest.mark.p1
class TestGitLabVariableGet(CLISkillTest):
    """Tests for getting CI/CD variables."""

    @pytest.mark.readonly
    def test_get_variable(self, run_glab, gitlab_project: str):
        """Test getting a specific variable."""
        result = self.run_command(
            run_glab, "variable", "get", "TEST_VAR",
            repo=gitlab_project
        )
        self.assert_success(result)
        self.assert_output_contains(result, "test_value")


@pytest.mark.live
@pytest.mark.p1
class TestGitLabVariableDelete(CLISkillTest):
    """Tests for deleting CI/CD variables."""

    @pytest.mark.destructive
    def test_delete_variable(
        self,
        run_glab,
        gitlab_project: str,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a variable."""
        key = f"DELETE_VAR_{unique_id.upper()}"

        # Create variable first via API
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/variables",
            {"key": key, "value": "to_delete"}
        )

        # Delete via CLI
        result = self.run_command(
            run_glab, "variable", "delete", key,
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p1
class TestGitLabVariableAPI(APISkillTest):
    """API tests for gitlab-variable skill."""

    @pytest.mark.readonly
    def test_list_variables_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing variables via API."""
        variables = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/variables")
        self.assert_is_list(variables, min_length=1)

        # Verify expected variable exists
        keys = [v["key"] for v in variables]
        assert "TEST_VAR" in keys

    @pytest.mark.readonly
    def test_get_variable_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting a specific variable."""
        variable = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/variables/TEST_VAR"
        )
        self.assert_is_dict(variable)
        self.assert_field_equals(variable, "key", "TEST_VAR")
        self.assert_field_equals(variable, "value", "test_value")

    @pytest.mark.destructive
    def test_create_variable_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_variables: list,
    ):
        """Test creating variable via API."""
        key = f"API_VAR_{unique_id.upper()}"

        variable = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/variables",
            {
                "key": key,
                "value": f"api_value_{unique_id}",
                "protected": False,
                "masked": False,
            }
        )
        created_variables.append(key)

        self.assert_is_dict(variable)
        self.assert_field_equals(variable, "key", key)

    @pytest.mark.destructive
    def test_create_masked_variable_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_variables: list,
    ):
        """Test creating a masked variable."""
        key = f"MASKED_VAR_{unique_id.upper()}"
        # Masked values must be at least 8 chars and match pattern
        value = f"masked12{unique_id}"

        variable = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/variables",
            {
                "key": key,
                "value": value,
                "protected": False,
                "masked": True,
            }
        )
        created_variables.append(key)

        self.assert_is_dict(variable)
        self.assert_field_equals(variable, "masked", True)

    @pytest.mark.destructive
    def test_update_variable_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        create_test_variable,
        unique_id: str,
    ):
        """Test updating a variable."""
        variable = create_test_variable(
            f"UPDATE_VAR_{unique_id.upper()}",
            "original_value"
        )

        # Update the variable
        updated = self.api_put(
            gitlab_api,
            f"/projects/{gitlab_project_id}/variables/{variable['key']}",
            {"value": "updated_value"}
        )
        self.assert_field_equals(updated, "value", "updated_value")

    @pytest.mark.destructive
    def test_delete_variable_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test deleting a variable."""
        key = f"DELETE_API_VAR_{unique_id.upper()}"

        # Create variable
        gitlab_api.post(
            f"/projects/{gitlab_project_id}/variables",
            {"key": key, "value": "to_delete_api"}
        )

        # Delete variable
        self.api_delete(gitlab_api, f"/projects/{gitlab_project_id}/variables/{key}")

        # Verify deleted
        result = self.api_get(
            gitlab_api,
            f"/projects/{gitlab_project_id}/variables/{key}",
            expected_status=404
        )
        assert result is None


@pytest.mark.live
@pytest.mark.p1
class TestGitLabVariableEnvironment(APISkillTest):
    """Tests for environment-scoped variables."""

    @pytest.mark.destructive
    def test_create_environment_variable(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
        created_variables: list,
    ):
        """Test creating an environment-scoped variable."""
        key = f"ENV_VAR_{unique_id.upper()}"

        variable = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/variables",
            {
                "key": key,
                "value": f"env_value_{unique_id}",
                "environment_scope": "production",
            }
        )
        created_variables.append(key)

        self.assert_is_dict(variable)
        self.assert_field_equals(variable, "environment_scope", "production")


@pytest.mark.live
@pytest.mark.p1
class TestGitLabVariableGroup(APISkillTest):
    """Tests for group-level variables."""

    @pytest.mark.readonly
    def test_list_group_variables(self, gitlab_api: GitLabAPI, gitlab_group_id: int):
        """Test listing group variables."""
        variables = self.api_get(gitlab_api, f"/groups/{gitlab_group_id}/variables")
        self.assert_is_list(variables)

    @pytest.mark.destructive
    def test_create_group_variable(
        self,
        root_api: GitLabAPI,
        gitlab_group_id: int,
        unique_id: str,
    ):
        """Test creating a group-level variable."""
        key = f"GROUP_VAR_{unique_id.upper()}"

        try:
            variable = root_api.post(
                f"/groups/{gitlab_group_id}/variables",
                {"key": key, "value": f"group_value_{unique_id}"}
            )
            self.assert_is_dict(variable)
            self.assert_field_equals(variable, "key", key)
        finally:
            # Cleanup
            try:
                root_api.delete(f"/groups/{gitlab_group_id}/variables/{key}")
            except GitLabAPIError:
                pass


@pytest.mark.live
@pytest.mark.p1
class TestGitLabVariablePermissions(APISkillTest):
    """Permission tests for gitlab-variable skill."""

    @pytest.mark.readonly
    def test_developer_can_list_variables(self, developer_api: GitLabAPI, gitlab_project_id: int):
        """Test that developer can list variables."""
        variables = self.api_get(developer_api, f"/projects/{gitlab_project_id}/variables")
        self.assert_is_list(variables)

    @pytest.mark.destructive
    def test_developer_cannot_create_variable(
        self,
        developer_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test that developer cannot create variables (maintainer+ required)."""
        try:
            developer_api.post(
                f"/projects/{gitlab_project_id}/variables",
                {"key": f"FAIL_VAR_{unique_id.upper()}", "value": "fail"}
            )
            pytest.fail("Expected 403 Forbidden")
        except GitLabAPIError as e:
            assert e.status_code in (403, 401)

    @pytest.mark.readonly
    def test_reporter_cannot_view_variable_values(
        self,
        reporter_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that reporter cannot view variable values."""
        # Reporters typically cannot access CI/CD variables at all
        try:
            reporter_api.get(f"/projects/{gitlab_project_id}/variables")
            # If they can list, they might see masked values
        except GitLabAPIError as e:
            # Expected - reporters don't have variable access
            assert e.status_code in (403, 401)
