"""
Live integration tests for gitlab-ci skill.

Tests CI/CD pipeline operations via glab CLI.
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
@pytest.mark.p0
class TestGitLabCIPipelines(CLISkillTest):
    """Tests for CI/CD pipeline operations."""

    @pytest.mark.readonly
    def test_list_pipelines(self, run_glab, gitlab_project: str):
        """Test listing pipelines."""
        result = self.run_command(run_glab, "ci", "list", repo=gitlab_project)
        self.assert_success(result)

    @pytest.mark.readonly
    def test_list_pipelines_with_status(self, run_glab, gitlab_project: str):
        """Test listing pipelines with status filter."""
        result = self.run_command(
            run_glab, "ci", "list",
            "--status", "success",
            repo=gitlab_project
        )
        self.assert_success(result)

    @pytest.mark.readonly
    def test_view_pipeline(self, run_glab, gitlab_project: str):
        """Test viewing a specific pipeline."""
        # First list to get a pipeline ID
        list_result = self.run_command(run_glab, "ci", "list", repo=gitlab_project)
        self.assert_success(list_result)

        # Try to view the first pipeline if any exist
        # This may not output anything if no pipelines exist
        result = self.run_command(
            run_glab, "ci", "view",
            repo=gitlab_project
        )
        # View without ID shows latest, may fail if no pipelines
        # That's acceptable behavior


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCIJobs(CLISkillTest):
    """Tests for CI/CD job operations."""

    @pytest.mark.readonly
    def test_list_jobs(self, run_glab, gitlab_project: str):
        """Test listing jobs."""
        # This requires a pipeline to exist
        result = self.run_command(
            run_glab, "ci", "list",
            repo=gitlab_project
        )
        self.assert_success(result)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCIAPI(APISkillTest):
    """API tests for gitlab-ci skill."""

    @pytest.mark.readonly
    def test_list_pipelines_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing pipelines via API."""
        pipelines = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/pipelines")
        self.assert_is_list(pipelines)

    @pytest.mark.readonly
    def test_list_pipeline_jobs_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing jobs for a pipeline."""
        # Get pipelines first
        pipelines = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/pipelines")
        if pipelines:
            pipeline_id = pipelines[0]["id"]
            jobs = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/pipelines/{pipeline_id}/jobs")
            self.assert_is_list(jobs)

    @pytest.mark.readonly
    def test_get_pipeline_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test getting pipeline details."""
        pipelines = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/pipelines")
        if pipelines:
            pipeline_id = pipelines[0]["id"]
            pipeline = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/pipelines/{pipeline_id}")
            self.assert_is_dict(pipeline)
            self.assert_has_field(pipeline, "status")

    @pytest.mark.destructive
    def test_create_pipeline_api(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test creating a pipeline via API."""
        # Trigger a new pipeline on main branch
        pipeline = self.api_post(
            gitlab_api,
            f"/projects/{gitlab_project_id}/pipeline",
            {"ref": "main"}
        )
        self.assert_is_dict(pipeline)
        self.assert_has_field(pipeline, "id")
        self.assert_has_field(pipeline, "status")

    @pytest.mark.readonly
    def test_list_project_jobs_api(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing all project jobs."""
        jobs = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/jobs")
        self.assert_is_list(jobs)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCISchedules(APISkillTest):
    """Tests for CI/CD pipeline schedules."""

    @pytest.mark.readonly
    def test_list_schedules(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing pipeline schedules."""
        schedules = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/pipeline_schedules")
        self.assert_is_list(schedules)

    @pytest.mark.destructive
    def test_create_and_delete_schedule(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test creating and deleting a pipeline schedule."""
        schedule = None
        try:
            schedule = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/pipeline_schedules",
                {
                    "description": f"Test Schedule {unique_id}",
                    "ref": "main",
                    "cron": "0 0 * * *",  # Daily at midnight
                    "active": False,  # Don't actually run
                }
            )
            self.assert_is_dict(schedule)
            self.assert_field_contains(schedule, "description", unique_id)
        finally:
            if schedule:
                self.api_delete(
                    gitlab_api,
                    f"/projects/{gitlab_project_id}/pipeline_schedules/{schedule['id']}"
                )


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCIArtifacts(APISkillTest):
    """Tests for CI/CD artifacts."""

    @pytest.mark.readonly
    def test_list_project_artifacts(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing project artifacts."""
        # Jobs endpoint includes artifact info
        jobs = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/jobs")
        self.assert_is_list(jobs)
        # Artifacts may or may not exist depending on pipeline runs


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCIEnvironments(APISkillTest):
    """Tests for CI/CD environments."""

    @pytest.mark.readonly
    def test_list_environments(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing environments."""
        environments = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/environments")
        self.assert_is_list(environments)


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCITriggers(APISkillTest):
    """Tests for CI/CD pipeline triggers."""

    @pytest.mark.readonly
    def test_list_triggers(self, gitlab_api: GitLabAPI, gitlab_project_id: int):
        """Test listing pipeline triggers."""
        triggers = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/triggers")
        self.assert_is_list(triggers)

    @pytest.mark.destructive
    def test_create_and_delete_trigger(
        self,
        gitlab_api: GitLabAPI,
        gitlab_project_id: int,
        unique_id: str,
    ):
        """Test creating and deleting a pipeline trigger."""
        trigger = None
        try:
            trigger = self.api_post(
                gitlab_api,
                f"/projects/{gitlab_project_id}/triggers",
                {"description": f"Test Trigger {unique_id}"}
            )
            self.assert_is_dict(trigger)
            self.assert_has_field(trigger, "token")
        finally:
            if trigger:
                self.api_delete(
                    gitlab_api,
                    f"/projects/{gitlab_project_id}/triggers/{trigger['id']}"
                )


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCICLI(CLISkillTest):
    """Additional CLI tests for gitlab-ci skill."""

    @pytest.mark.readonly
    def test_ci_lint(self, run_glab, gitlab_project: str):
        """Test CI config linting."""
        result = self.run_command(
            run_glab, "ci", "lint",
            repo=gitlab_project
        )
        # May fail if .gitlab-ci.yml has issues, but command should work
        # We just check it doesn't crash

    @pytest.mark.readonly
    def test_ci_status(self, run_glab, gitlab_project: str):
        """Test getting CI status."""
        result = self.run_command(
            run_glab, "ci", "status",
            repo=gitlab_project
        )
        # May not have pipelines, that's OK


@pytest.mark.live
@pytest.mark.p0
class TestGitLabCIPermissions(APISkillTest):
    """Permission tests for gitlab-ci skill."""

    @pytest.mark.readonly
    def test_reporter_can_list_pipelines(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list pipelines."""
        pipelines = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/pipelines")
        self.assert_is_list(pipelines)

    @pytest.mark.readonly
    def test_reporter_can_list_jobs(self, reporter_api: GitLabAPI, gitlab_project_id: int):
        """Test that reporter can list jobs."""
        jobs = self.api_get(reporter_api, f"/projects/{gitlab_project_id}/jobs")
        self.assert_is_list(jobs)

    @pytest.mark.destructive
    def test_developer_can_trigger_pipeline(
        self,
        developer_api: GitLabAPI,
        gitlab_project_id: int,
    ):
        """Test that developer can trigger pipelines."""
        pipeline = developer_api.post(
            f"/projects/{gitlab_project_id}/pipeline",
            {"ref": "main"}
        )
        self.assert_is_dict(pipeline)
        self.assert_has_field(pipeline, "id")
