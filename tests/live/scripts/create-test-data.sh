#!/usr/bin/env bash
# Create test data for GitLab live integration tests
# Seeds groups, projects, issues, MRs, labels, etc.
#
# Usage:
#   ./create-test-data.sh              # Create all test data
#   ./create-test-data.sh --minimal    # Create minimal data (faster)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env.test"
FIXTURES_DIR="${SCRIPT_DIR}/../fixtures"

# Load environment
if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE"
else
    echo "Error: Environment file not found. Run setup-gitlab.sh first."
    exit 1
fi

GITLAB_URL="${GITLAB_URL:-http://localhost:8080}"
GITLAB_TOKEN="${GITLAB_ROOT_TOKEN:-$GITLAB_TOKEN}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[OK]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Parse arguments
MINIMAL=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --minimal)
            MINIMAL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--minimal]"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# API helper function
api() {
    local method="$1"
    local endpoint="$2"
    shift 2
    local data="${1:-}"

    local args=(
        -s
        -X "$method"
        -H "PRIVATE-TOKEN: $GITLAB_TOKEN"
        -H "Content-Type: application/json"
    )

    if [[ -n "$data" ]]; then
        args+=(-d "$data")
    fi

    curl "${args[@]}" "${GITLAB_URL}/api/v4${endpoint}"
}

# Check if resource exists
exists() {
    local endpoint="$1"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
        "${GITLAB_URL}/api/v4${endpoint}")
    [[ "$code" == "200" ]]
}

echo_step "Creating test data"
echo ""

# ============================================================================
# Groups
# ============================================================================
echo_step "Creating groups..."

# Main test group
if exists "/groups/live-test-group"; then
    echo_info "Group 'live-test-group' already exists"
    GROUP_ID=$(api GET "/groups/live-test-group" | jq -r '.id')
else
    echo_info "Creating group: live-test-group"
    GROUP_RESPONSE=$(api POST "/groups" '{
        "name": "Live Test Group",
        "path": "live-test-group",
        "description": "Group for live integration tests",
        "visibility": "private"
    }')
    GROUP_ID=$(echo "$GROUP_RESPONSE" | jq -r '.id')
    echo_success "Group created: ID=$GROUP_ID"
fi

# Subgroup
if exists "/groups/live-test-group%2Fsubgroup"; then
    echo_info "Subgroup 'subgroup' already exists"
else
    echo_info "Creating subgroup: subgroup"
    api POST "/groups" "{
        \"name\": \"Test Subgroup\",
        \"path\": \"subgroup\",
        \"parent_id\": $GROUP_ID,
        \"visibility\": \"private\"
    }" > /dev/null
    echo_success "Subgroup created"
fi

# Add test users to group
echo_info "Adding test users to group..."
for username in test-maintainer test-developer test-reporter; do
    USER_ID=$(api GET "/users?username=$username" | jq -r '.[0].id')
    if [[ "$USER_ID" != "null" ]]; then
        case $username in
            test-maintainer) ACCESS=40 ;;
            test-developer) ACCESS=30 ;;
            test-reporter) ACCESS=20 ;;
        esac
        api POST "/groups/$GROUP_ID/members" "{\"user_id\": $USER_ID, \"access_level\": $ACCESS}" > /dev/null 2>&1 || true
    fi
done
echo_success "Users added to group"

# ============================================================================
# Projects
# ============================================================================
echo_step "Creating projects..."

# Main test project
if exists "/projects/live-test-group%2Ftest-project"; then
    echo_info "Project 'test-project' already exists"
    PROJECT_ID=$(api GET "/projects/live-test-group%2Ftest-project" | jq -r '.id')
else
    echo_info "Creating project: test-project"
    PROJECT_RESPONSE=$(api POST "/projects" "{
        \"name\": \"Test Project\",
        \"path\": \"test-project\",
        \"namespace_id\": $GROUP_ID,
        \"description\": \"Main project for live integration tests\",
        \"visibility\": \"private\",
        \"initialize_with_readme\": true,
        \"default_branch\": \"main\"
    }")
    PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
    echo_success "Project created: ID=$PROJECT_ID"

    # Wait for project to be ready
    sleep 2
fi

# Secondary project for fork/transfer tests
if exists "/projects/live-test-group%2Ftest-project-secondary"; then
    echo_info "Secondary project already exists"
else
    echo_info "Creating secondary project"
    api POST "/projects" "{
        \"name\": \"Test Project Secondary\",
        \"path\": \"test-project-secondary\",
        \"namespace_id\": $GROUP_ID,
        \"visibility\": \"private\",
        \"initialize_with_readme\": true
    }" > /dev/null
    echo_success "Secondary project created"
fi

# ============================================================================
# Repository Files
# ============================================================================
echo_step "Creating repository files..."

# Create branch for MR tests
echo_info "Creating feature branch..."
api POST "/projects/$PROJECT_ID/repository/branches" '{
    "branch": "feature/test-branch",
    "ref": "main"
}' > /dev/null 2>&1 || echo_info "Branch may already exist"

# Create files
create_file() {
    local path="$1"
    local content="$2"
    local message="$3"
    local branch="${4:-main}"

    api POST "/projects/$PROJECT_ID/repository/files/$(echo "$path" | sed 's/\//%2F/g')" "{
        \"branch\": \"$branch\",
        \"content\": \"$content\",
        \"commit_message\": \"$message\"
    }" > /dev/null 2>&1 || true
}

create_file "src/main.py" "$(cat << 'EOF'
#!/usr/bin/env python3
"""Main application entry point."""

def main():
    """Run the application."""
    print("Hello from test project!")
    return 0

if __name__ == "__main__":
    exit(main())
EOF
)" "Add main.py"

create_file ".gitlab-ci.yml" "$(cat << 'EOF'
stages:
  - test
  - build

test:
  stage: test
  script:
    - echo "Running tests..."
    - python -m pytest tests/ -v || true

build:
  stage: build
  script:
    - echo "Building..."
    - python -m py_compile src/main.py
EOF
)" "Add CI configuration"

create_file "tests/__init__.py" "" "Add tests module"

create_file "tests/test_main.py" "$(cat << 'EOF'
"""Tests for main module."""

def test_main():
    """Test main function exists."""
    from src.main import main
    assert callable(main)
EOF
)" "Add test file"

echo_success "Repository files created"

# ============================================================================
# Labels
# ============================================================================
echo_step "Creating labels..."

LABELS=(
    "bug:ff0000:Bug report"
    "enhancement:00ff00:Feature enhancement"
    "documentation:0000ff:Documentation changes"
    "priority::high:ff6600:High priority"
    "priority::low:999999:Low priority"
    "status::todo:ededed:To do"
    "status::in-progress:fbca04:In progress"
    "status::done:0e8a16:Done"
)

for label_data in "${LABELS[@]}"; do
    IFS=':' read -r name color description <<< "$label_data"
    api POST "/projects/$PROJECT_ID/labels" "{
        \"name\": \"$name\",
        \"color\": \"#$color\",
        \"description\": \"$description\"
    }" > /dev/null 2>&1 || true
done

echo_success "Labels created"

# ============================================================================
# Milestones
# ============================================================================
echo_step "Creating milestones..."

api POST "/projects/$PROJECT_ID/milestones" '{
    "title": "v1.0.0",
    "description": "First release",
    "due_date": "2025-03-01"
}' > /dev/null 2>&1 || true

api POST "/projects/$PROJECT_ID/milestones" '{
    "title": "v1.1.0",
    "description": "Minor release",
    "due_date": "2025-06-01"
}' > /dev/null 2>&1 || true

api POST "/projects/$PROJECT_ID/milestones" '{
    "title": "v2.0.0",
    "description": "Major release",
    "due_date": "2025-12-01"
}' > /dev/null 2>&1 || true

echo_success "Milestones created"

# ============================================================================
# Issues
# ============================================================================
echo_step "Creating issues..."

# Create various issues
ISSUE1=$(api POST "/projects/$PROJECT_ID/issues" '{
    "title": "Bug: Application crashes on startup",
    "description": "When running main.py, the application crashes.\n\n## Steps to reproduce\n1. Run main.py\n2. Observe crash",
    "labels": "bug,priority::high"
}' | jq -r '.iid')
echo_info "Created issue #$ISSUE1"

ISSUE2=$(api POST "/projects/$PROJECT_ID/issues" '{
    "title": "Enhancement: Add logging support",
    "description": "We should add proper logging to the application.",
    "labels": "enhancement,priority::low"
}' | jq -r '.iid')
echo_info "Created issue #$ISSUE2"

ISSUE3=$(api POST "/projects/$PROJECT_ID/issues" '{
    "title": "Documentation: Update README",
    "description": "The README needs to be updated with installation instructions.",
    "labels": "documentation"
}' | jq -r '.iid')
echo_info "Created issue #$ISSUE3"

# Closed issue
ISSUE4=$(api POST "/projects/$PROJECT_ID/issues" '{
    "title": "Bug: Fixed typo in output",
    "description": "Fixed a typo.",
    "labels": "bug",
    "state_event": "close"
}' | jq -r '.iid')
echo_info "Created closed issue #$ISSUE4"

echo_success "Issues created"

# ============================================================================
# Merge Requests
# ============================================================================
echo_step "Creating merge requests..."

# Create a file change on the feature branch
api POST "/projects/$PROJECT_ID/repository/files/src%2Ffeature.py" '{
    "branch": "feature/test-branch",
    "content": "# New feature\ndef feature():\n    return True\n",
    "commit_message": "Add new feature"
}' > /dev/null 2>&1 || true

# Create MR
MR1=$(api POST "/projects/$PROJECT_ID/merge_requests" '{
    "source_branch": "feature/test-branch",
    "target_branch": "main",
    "title": "Add new feature",
    "description": "This MR adds a new feature.\n\nCloses #2"
}' 2>/dev/null | jq -r '.iid' 2>/dev/null || echo "")

if [[ -n "$MR1" && "$MR1" != "null" ]]; then
    echo_info "Created MR !$MR1"
else
    echo_info "MR may already exist or branch not found"
fi

echo_success "Merge requests created"

# ============================================================================
# Webhooks (project level)
# ============================================================================
if [[ "$MINIMAL" != "true" ]]; then
    echo_step "Creating webhooks..."

    api POST "/projects/$PROJECT_ID/hooks" '{
        "url": "https://example.com/webhook",
        "push_events": true,
        "merge_requests_events": true,
        "issues_events": true
    }' > /dev/null 2>&1 || true

    echo_success "Webhooks created"
fi

# ============================================================================
# Wiki (if available)
# ============================================================================
if [[ "$MINIMAL" != "true" ]]; then
    echo_step "Creating wiki pages..."

    api POST "/projects/$PROJECT_ID/wikis" '{
        "title": "Home",
        "content": "# Welcome\n\nThis is the test project wiki.\n\n## Pages\n- [Getting Started](getting-started)",
        "format": "markdown"
    }' > /dev/null 2>&1 || true

    api POST "/projects/$PROJECT_ID/wikis" '{
        "title": "Getting Started",
        "content": "# Getting Started\n\n## Installation\n\n```bash\npip install test-project\n```",
        "format": "markdown"
    }' > /dev/null 2>&1 || true

    echo_success "Wiki pages created"
fi

# ============================================================================
# CI/CD Variables
# ============================================================================
echo_step "Creating CI/CD variables..."

api POST "/projects/$PROJECT_ID/variables" '{
    "key": "TEST_VAR",
    "value": "test_value",
    "protected": false,
    "masked": false
}' > /dev/null 2>&1 || true

api POST "/projects/$PROJECT_ID/variables" '{
    "key": "SECRET_VAR",
    "value": "secret_value",
    "protected": true,
    "masked": true
}' > /dev/null 2>&1 || true

echo_success "CI/CD variables created"

# ============================================================================
# Badges
# ============================================================================
if [[ "$MINIMAL" != "true" ]]; then
    echo_step "Creating badges..."

    api POST "/projects/$PROJECT_ID/badges" '{
        "link_url": "https://example.com/coverage",
        "image_url": "https://img.shields.io/badge/coverage-80%25-green"
    }' > /dev/null 2>&1 || true

    echo_success "Badges created"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo_success "Test data creation complete!"
echo ""
echo "Created resources:"
echo "  - Group: live-test-group (ID: $GROUP_ID)"
echo "  - Project: test-project (ID: $PROJECT_ID)"
echo "  - Issues: 4"
echo "  - Merge Requests: 1"
echo "  - Labels: ${#LABELS[@]}"
echo "  - Milestones: 3"
echo ""
echo "Run tests with:"
echo "  pytest tests/live/skills/ -v"
