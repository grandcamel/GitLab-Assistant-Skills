#!/usr/bin/env bash
# Cleanup script for GitLab live integration tests
# Resets state between test runs
#
# Usage:
#   ./cleanup.sh              # Clean test data only
#   ./cleanup.sh --full       # Also remove users and groups
#   ./cleanup.sh --volumes    # Remove Docker volumes (full reset)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env.test"

# Load environment
if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE"
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
FULL_CLEANUP=false
VOLUME_CLEANUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_CLEANUP=true
            shift
            ;;
        --volumes)
            VOLUME_CLEANUP=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--full] [--volumes]"
            echo ""
            echo "Options:"
            echo "  --full      Also remove test users and groups"
            echo "  --volumes   Remove Docker volumes (complete reset)"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Volume cleanup (Docker)
if [[ "$VOLUME_CLEANUP" == "true" ]]; then
    echo_step "Removing Docker volumes..."

    cd "$SCRIPT_DIR/.."

    # Stop containers
    docker compose down 2>/dev/null || true

    # Remove volumes
    docker volume rm gitlab-live-test-config 2>/dev/null || true
    docker volume rm gitlab-live-test-logs 2>/dev/null || true
    docker volume rm gitlab-live-test-data 2>/dev/null || true

    # Remove env file
    rm -f "$ENV_FILE"

    echo_success "Docker volumes removed"
    echo_info "Run 'docker compose up -d' to start fresh"
    exit 0
fi

# Check GitLab is running
if ! curl -s -o /dev/null "${GITLAB_URL}/-/readiness"; then
    echo_error "GitLab is not running at ${GITLAB_URL}"
    exit 1
fi

# API helper
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

echo_step "Cleaning up test data..."
echo ""

# ============================================================================
# Delete projects created by tests (not the main test project)
# ============================================================================
echo_info "Cleaning up temporary test projects..."

# List all projects in test group
PROJECTS=$(api GET "/groups/live-test-group/projects?per_page=100" 2>/dev/null | jq -r '.[].path' 2>/dev/null || echo "")

for project in $PROJECTS; do
    # Keep main test projects
    if [[ "$project" == "test-project" ]] || [[ "$project" == "test-project-secondary" ]]; then
        continue
    fi

    # Delete temporary projects (created during tests)
    echo_info "Deleting project: $project"
    api DELETE "/projects/live-test-group%2F$project" > /dev/null 2>&1 || true
done

# ============================================================================
# Reset main test project
# ============================================================================
echo_info "Resetting test project state..."

PROJECT_ID=$(api GET "/projects/live-test-group%2Ftest-project" 2>/dev/null | jq -r '.id' 2>/dev/null || echo "")

if [[ -n "$PROJECT_ID" && "$PROJECT_ID" != "null" ]]; then
    # Close all open MRs
    MRS=$(api GET "/projects/$PROJECT_ID/merge_requests?state=opened&per_page=100" | jq -r '.[].iid' 2>/dev/null || echo "")
    for mr in $MRS; do
        api PUT "/projects/$PROJECT_ID/merge_requests/$mr" '{"state_event": "close"}' > /dev/null 2>&1 || true
    done
    echo_info "Closed open merge requests"

    # Delete test branches (keep main and feature/test-branch)
    BRANCHES=$(api GET "/projects/$PROJECT_ID/repository/branches?per_page=100" | jq -r '.[].name' 2>/dev/null || echo "")
    for branch in $BRANCHES; do
        if [[ "$branch" == "main" ]] || [[ "$branch" == "feature/test-branch" ]]; then
            continue
        fi
        api DELETE "/projects/$PROJECT_ID/repository/branches/$(echo "$branch" | sed 's/\//%2F/g')" > /dev/null 2>&1 || true
    done
    echo_info "Cleaned up branches"

    # Delete test releases
    RELEASES=$(api GET "/projects/$PROJECT_ID/releases?per_page=100" | jq -r '.[].tag_name' 2>/dev/null || echo "")
    for release in $RELEASES; do
        api DELETE "/projects/$PROJECT_ID/releases/$release" > /dev/null 2>&1 || true
    done
    echo_info "Cleaned up releases"

    # Delete test webhooks (keep the original one)
    HOOKS=$(api GET "/projects/$PROJECT_ID/hooks?per_page=100" | jq -r '.[] | select(.url != "https://example.com/webhook") | .id' 2>/dev/null || echo "")
    for hook in $HOOKS; do
        api DELETE "/projects/$PROJECT_ID/hooks/$hook" > /dev/null 2>&1 || true
    done
    echo_info "Cleaned up webhooks"

    # Delete extra badges
    BADGES=$(api GET "/projects/$PROJECT_ID/badges?per_page=100" | jq -r '.[1:] | .[].id' 2>/dev/null || echo "")
    for badge in $BADGES; do
        api DELETE "/projects/$PROJECT_ID/badges/$badge" > /dev/null 2>&1 || true
    done
    echo_info "Cleaned up badges"

    # Reset extra wiki pages (keep Home and Getting Started)
    WIKIS=$(api GET "/projects/$PROJECT_ID/wikis?per_page=100" | jq -r '.[] | select(.slug != "home" and .slug != "getting-started") | .slug' 2>/dev/null || echo "")
    for wiki in $WIKIS; do
        api DELETE "/projects/$PROJECT_ID/wikis/$wiki" > /dev/null 2>&1 || true
    done
    echo_info "Cleaned up wiki pages"

    # Reset issues to initial state (reopen closed test issues)
    # This is intentionally minimal - tests should handle their own issue cleanup
fi

# ============================================================================
# Full cleanup (optional)
# ============================================================================
if [[ "$FULL_CLEANUP" == "true" ]]; then
    echo_step "Performing full cleanup..."

    # Delete all projects in test group
    echo_info "Deleting all test projects..."
    for project in $PROJECTS; do
        api DELETE "/projects/live-test-group%2F$project" > /dev/null 2>&1 || true
    done

    # Delete subgroup
    echo_info "Deleting subgroup..."
    api DELETE "/groups/live-test-group%2Fsubgroup" > /dev/null 2>&1 || true

    # Delete main group
    echo_info "Deleting main group..."
    api DELETE "/groups/live-test-group" > /dev/null 2>&1 || true

    # Delete test users
    echo_info "Deleting test users..."
    for username in test-maintainer test-developer test-reporter; do
        USER_ID=$(api GET "/users?username=$username" | jq -r '.[0].id' 2>/dev/null || echo "")
        if [[ -n "$USER_ID" && "$USER_ID" != "null" ]]; then
            api DELETE "/users/$USER_ID" > /dev/null 2>&1 || true
        fi
    done

    # Remove environment file
    rm -f "$ENV_FILE"

    echo_success "Full cleanup complete"
    echo_info "Run setup-gitlab.sh and create-test-data.sh to recreate"
else
    echo_success "Cleanup complete"
    echo_info "Test environment is reset and ready for new test runs"
fi
