"""
Base test classes for GitLab live integration tests.

Provides:
- CLISkillTest: Base class for glab CLI-based skill tests
- APISkillTest: Base class for direct API skill tests
"""

import os
import subprocess
from abc import ABC
from typing import Optional

import pytest

try:
    # When running under pytest, conftest is loaded directly
    from conftest import GitLabAPI, GitLabAPIError
except ImportError:
    # When running directly, use the full path
    from tests.live.conftest import GitLabAPI, GitLabAPIError


class BaseSkillTest(ABC):
    """
    Abstract base class for all skill tests.

    Provides common utilities and assertions.
    """

    @staticmethod
    def assert_contains(haystack: str, needle: str, msg: str = None):
        """Assert that needle is in haystack."""
        assert needle in haystack, msg or f"Expected '{needle}' in output"

    @staticmethod
    def assert_not_contains(haystack: str, needle: str, msg: str = None):
        """Assert that needle is not in haystack."""
        assert needle not in haystack, msg or f"Did not expect '{needle}' in output"

    @staticmethod
    def assert_json_field(data: dict, field: str, expected, msg: str = None):
        """Assert that a JSON field has the expected value."""
        actual = data.get(field)
        assert actual == expected, msg or f"Expected {field}={expected}, got {actual}"


class CLISkillTest(BaseSkillTest):
    """
    Base class for testing CLI-based skills (using glab).

    Provides helpers for running glab commands and asserting results.

    Usage:
        @pytest.mark.live
        class TestGitLabIssue(CLISkillTest):
            def test_list_issues(self, run_glab, gitlab_project):
                result = self.run_command(run_glab, "issue", "list", repo=gitlab_project)
                self.assert_success(result)
    """

    def run_command(
        self,
        run_glab,
        *args,
        repo: str = None,
        timeout: int = 30,
        expected_returncode: int = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a glab command and return the result.

        Args:
            run_glab: The run_glab fixture
            *args: Command arguments
            repo: Repository path (optional)
            timeout: Command timeout in seconds
            expected_returncode: If set, assert the return code matches

        Returns:
            CompletedProcess with stdout, stderr, and returncode
        """
        result = run_glab(*args, repo=repo, timeout=timeout)

        if expected_returncode is not None:
            assert result.returncode == expected_returncode, (
                f"Expected return code {expected_returncode}, got {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

        return result

    def assert_success(self, result: subprocess.CompletedProcess, msg: str = None):
        """Assert that the command succeeded (return code 0)."""
        assert result.returncode == 0, (
            msg or f"Command failed with code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def assert_failure(self, result: subprocess.CompletedProcess, msg: str = None):
        """Assert that the command failed (return code != 0)."""
        assert result.returncode != 0, (
            msg or f"Expected command to fail, but it succeeded\n"
            f"stdout: {result.stdout}"
        )

    def assert_output_contains(
        self,
        result: subprocess.CompletedProcess,
        expected: str,
        msg: str = None,
    ):
        """Assert that stdout or stderr contains expected string."""
        combined = result.stdout + result.stderr
        assert expected in combined, (
            msg or f"Expected '{expected}' in output\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def assert_output_not_contains(
        self,
        result: subprocess.CompletedProcess,
        unexpected: str,
        msg: str = None,
    ):
        """Assert that neither stdout nor stderr contains unexpected string."""
        combined = result.stdout + result.stderr
        assert unexpected not in combined, (
            msg or f"Did not expect '{unexpected}' in output\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class APISkillTest(BaseSkillTest):
    """
    Base class for testing API-based skills.

    Provides helpers for making API calls and asserting results.

    Usage:
        @pytest.mark.live
        class TestGitLabWebhook(APISkillTest):
            def test_list_webhooks(self, gitlab_api, gitlab_project_id):
                hooks = self.api_get(gitlab_api, f"/projects/{gitlab_project_id}/hooks")
                self.assert_is_list(hooks)
    """

    def api_get(
        self,
        api: GitLabAPI,
        endpoint: str,
        expected_status: int = None,
    ) -> dict | list | None:
        """
        Make a GET request and return the result.

        Args:
            api: GitLabAPI instance
            endpoint: API endpoint
            expected_status: If set to 404, expect and handle NotFound

        Returns:
            Parsed JSON response
        """
        try:
            return api.get(endpoint)
        except Exception as e:
            # Handle GitLabAPIError from any module path (pytest can load it differently)
            if type(e).__name__ == "GitLabAPIError":
                if expected_status and getattr(e, "status_code", 0) == expected_status:
                    return None
            raise

    def api_post(
        self,
        api: GitLabAPI,
        endpoint: str,
        data: dict,
        expected_status: int = None,
    ) -> dict | list | None:
        """
        Make a POST request and return the result.

        Args:
            api: GitLabAPI instance
            endpoint: API endpoint
            data: Request body
            expected_status: If set, expect this status code on error

        Returns:
            Parsed JSON response
        """
        try:
            return api.post(endpoint, data)
        except Exception as e:
            if type(e).__name__ == "GitLabAPIError":
                if expected_status and getattr(e, "status_code", 0) == expected_status:
                    return None
            raise

    def api_put(
        self,
        api: GitLabAPI,
        endpoint: str,
        data: dict,
        expected_status: int = None,
    ) -> dict | list | None:
        """Make a PUT request and return the result."""
        try:
            return api.put(endpoint, data)
        except Exception as e:
            if type(e).__name__ == "GitLabAPIError":
                if expected_status and getattr(e, "status_code", 0) == expected_status:
                    return None
            raise

    def api_delete(
        self,
        api: GitLabAPI,
        endpoint: str,
        expected_status: int = None,
    ) -> dict | list | None:
        """Make a DELETE request and return the result."""
        try:
            return api.delete(endpoint)
        except Exception as e:
            if type(e).__name__ == "GitLabAPIError":
                if expected_status and getattr(e, "status_code", 0) == expected_status:
                    return None
            raise

    def assert_is_list(self, data, min_length: int = 0, msg: str = None):
        """Assert that data is a list with at least min_length items."""
        assert isinstance(data, list), msg or f"Expected list, got {type(data)}"
        assert len(data) >= min_length, (
            msg or f"Expected at least {min_length} items, got {len(data)}"
        )

    def assert_is_dict(self, data, msg: str = None):
        """Assert that data is a dictionary."""
        assert isinstance(data, dict), msg or f"Expected dict, got {type(data)}"

    def assert_has_field(self, data: dict, field: str, msg: str = None):
        """Assert that dictionary has a specific field."""
        assert field in data, msg or f"Expected field '{field}' in {list(data.keys())}"

    def assert_field_equals(
        self,
        data: dict,
        field: str,
        expected,
        msg: str = None,
    ):
        """Assert that a field has the expected value."""
        self.assert_has_field(data, field)
        actual = data[field]
        assert actual == expected, (
            msg or f"Expected {field}={expected!r}, got {actual!r}"
        )

    def assert_field_contains(
        self,
        data: dict,
        field: str,
        expected: str,
        msg: str = None,
    ):
        """Assert that a string field contains expected substring."""
        self.assert_has_field(data, field)
        actual = data[field]
        assert isinstance(actual, str), f"Expected {field} to be string, got {type(actual)}"
        assert expected in actual, (
            msg or f"Expected '{expected}' in {field}='{actual}'"
        )


class CombinedSkillTest(CLISkillTest, APISkillTest):
    """
    Base class for tests that use both CLI and API.

    Useful for skills that have both CLI commands and API endpoints.
    """
    pass
