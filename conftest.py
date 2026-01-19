"""
Root test fixtures for GitLab-Assistant-Skills.

This file contains shared fixtures used across all skill tests.
"""

import pytest
from pathlib import Path
from typing import Generator
import tempfile
import shutil


@pytest.fixture
def temp_path() -> Generator[Path, None, None]:
    """Create a temporary directory as Path object."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def temp_dir(temp_path: Path) -> str:
    """Create a temporary directory as string."""
    return str(temp_path)


@pytest.fixture
def mock_gitlab_client():
    """Mock gitlab client for offline testing."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.get.return_value = {"items": [], "total": 0}
    client.post.return_value = {"id": "123", "status": "created"}
    client.put.return_value = {"id": "123", "status": "updated"}
    client.delete.return_value = None

    return client


@pytest.fixture
def sample_resource():
    """Sample resource data for testing."""
    return {
        "id": "RESOURCE-123",
        "name": "Test Resource",
        "description": "A test resource",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_resource_list(sample_resource):
    """Sample list of resources for testing."""
    return [sample_resource]


@pytest.fixture
def claude_project_structure(temp_path: Path) -> Path:
    """Create a minimal Claude plugin project structure."""
    # Create .claude-plugin directory
    plugin_dir = temp_path / ".claude-plugin"
    plugin_dir.mkdir()

    # Create plugin.json
    (plugin_dir / "plugin.json").write_text('''{
        "name": "test-plugin",
        "version": "1.0.0",
        "skills": ["../skills/test-skill/SKILL.md"]
    }''')

    # Create skills directory
    skills_dir = temp_path / "skills" / "test-skill"
    skills_dir.mkdir(parents=True)

    # Create SKILL.md
    (skills_dir / "SKILL.md").write_text('''---
name: test-skill
description: Test skill for testing.
---

# Test Skill

Test content.
''')

    return temp_path
