#!/usr/bin/env bash
# Setup GitLab test environment
# Creates test users and tokens via Rails console
#
# Usage:
#   ./setup-gitlab.sh              # Run setup
#   ./setup-gitlab.sh --reset      # Reset and re-run setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="${CONTAINER_NAME:-gitlab-live-test}"
GITLAB_URL="${GITLAB_URL:-http://localhost:8080}"
OUTPUT_FILE="${SCRIPT_DIR}/../.env.test"

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
RESET=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --reset)
            RESET=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--reset]"
            echo ""
            echo "Options:"
            echo "  --reset   Delete existing test users before setup"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo_error "Container '${CONTAINER_NAME}' is not running"
    echo_info "Start GitLab with: docker compose up -d"
    exit 1
fi

echo_step "Setting up GitLab test environment"
echo ""

# Function to run Rails command
run_rails() {
    local cmd="$1"
    docker exec -i "$CONTAINER_NAME" gitlab-rails runner "$cmd" 2>/dev/null
}

# Function to run Rails command and capture output
run_rails_output() {
    local cmd="$1"
    docker exec -i "$CONTAINER_NAME" gitlab-rails runner "$cmd" 2>/dev/null
}

# Get root password from initial_root_password file
echo_step "Retrieving root credentials..."
ROOT_PASSWORD=$(docker exec "$CONTAINER_NAME" cat /etc/gitlab/initial_root_password 2>/dev/null | grep "Password:" | awk '{print $2}' || echo "")

if [[ -z "$ROOT_PASSWORD" ]]; then
    echo_info "initial_root_password not found, setting default password"
    ROOT_PASSWORD="TestPassword123!"
    run_rails "user = User.find_by_username('root'); user.password = '${ROOT_PASSWORD}'; user.password_confirmation = '${ROOT_PASSWORD}'; user.save!"
fi

echo_success "Root password retrieved"

# Create test users
echo_step "Creating test users..."

USERS=(
    "test-maintainer:TestMaintainer123!:Test Maintainer:maintainer@test.local"
    "test-developer:TestDeveloper123!:Test Developer:developer@test.local"
    "test-reporter:TestReporter123!:Test Reporter:reporter@test.local"
)

for user_data in "${USERS[@]}"; do
    IFS=':' read -r username password name email <<< "$user_data"

    # Check if user exists
    exists=$(run_rails_output "puts User.exists?(username: '${username}')")

    if [[ "$exists" == "true" ]]; then
        if [[ "$RESET" == "true" ]]; then
            echo_info "Deleting existing user: $username"
            run_rails "User.find_by_username('${username}')&.destroy!"
        else
            echo_info "User already exists: $username"
            continue
        fi
    fi

    echo_info "Creating user: $username"
    run_rails "
        user = User.new(
            username: '${username}',
            email: '${email}',
            name: '${name}',
            password: '${password}',
            password_confirmation: '${password}',
            skip_confirmation: true,
            admin: false
        )
        user.save!
    "
done

echo_success "Test users created"

# Create personal access tokens
echo_step "Creating personal access tokens..."

declare -A TOKENS

# Token for root (admin)
echo_info "Creating token for root..."
ROOT_TOKEN=$(run_rails_output "
    user = User.find_by_username('root')
    token = user.personal_access_tokens.find_by(name: 'live-test-token')
    token&.destroy!
    new_token = user.personal_access_tokens.create!(
        name: 'live-test-token',
        scopes: [:api, :read_api, :read_user, :read_repository, :write_repository, :read_registry, :write_registry, :sudo],
        expires_at: 365.days.from_now
    )
    puts new_token.token
")
TOKENS[root]="$ROOT_TOKEN"
echo_success "Root token created"

# Tokens for test users
for username in test-maintainer test-developer test-reporter; do
    echo_info "Creating token for $username..."
    TOKEN=$(run_rails_output "
        user = User.find_by_username('${username}')
        token = user.personal_access_tokens.find_by(name: 'live-test-token')
        token&.destroy!
        new_token = user.personal_access_tokens.create!(
            name: 'live-test-token',
            scopes: [:api, :read_api, :read_user, :read_repository, :write_repository],
            expires_at: 365.days.from_now
        )
        puts new_token.token
    ")
    TOKENS[$username]="$TOKEN"
    echo_success "Token created for $username"
done

# Write environment file
echo_step "Writing environment file..."

cat > "$OUTPUT_FILE" << EOF
# GitLab Live Test Environment
# Generated by setup-gitlab.sh on $(date -Iseconds)
# DO NOT COMMIT THIS FILE

# GitLab URL
GITLAB_URL=${GITLAB_URL}
GITLAB_HOST=localhost:8080

# Root credentials (admin)
GITLAB_ROOT_USERNAME=root
GITLAB_ROOT_PASSWORD=${ROOT_PASSWORD}
GITLAB_ROOT_TOKEN=${TOKENS[root]}

# Test user tokens
GITLAB_MAINTAINER_TOKEN=${TOKENS[test-maintainer]}
GITLAB_DEVELOPER_TOKEN=${TOKENS[test-developer]}
GITLAB_REPORTER_TOKEN=${TOKENS[test-reporter]}

# Test user passwords (if needed for UI tests)
GITLAB_MAINTAINER_PASSWORD=TestMaintainer123!
GITLAB_DEVELOPER_PASSWORD=TestDeveloper123!
GITLAB_REPORTER_PASSWORD=TestReporter123!

# Default token for glab CLI
GITLAB_TOKEN=${TOKENS[test-maintainer]}
EOF

echo_success "Environment file written to: $OUTPUT_FILE"

# Configure glab CLI
echo_step "Configuring glab CLI..."

# Check if glab is installed
if command -v glab &> /dev/null; then
    # Login to glab
    echo "${TOKENS[test-maintainer]}" | glab auth login --hostname localhost:8080 --stdin 2>/dev/null || true
    echo_success "glab configured for localhost:8080"
else
    echo_info "glab not installed - skip CLI configuration"
    echo_info "Install glab and run: glab auth login --hostname localhost:8080 --token <TOKEN>"
fi

echo ""
echo_success "Setup complete!"
echo ""
echo "Environment:"
echo "  GitLab URL:     ${GITLAB_URL}"
echo "  Root token:     ${TOKENS[root]:0:10}..."
echo "  Maintainer:     ${TOKENS[test-maintainer]:0:10}..."
echo "  Developer:      ${TOKENS[test-developer]:0:10}..."
echo "  Reporter:       ${TOKENS[test-reporter]:0:10}..."
echo ""
echo "Next steps:"
echo "  1. Source the environment file: source ${OUTPUT_FILE}"
echo "  2. Create test data: ./create-test-data.sh"
echo "  3. Run tests: pytest tests/live/skills/ -v"
