#!/usr/bin/env bash
# Wait for GitLab to be fully ready
# Handles the 5-10 minute initial startup time
#
# Usage:
#   ./wait-for-gitlab.sh              # Wait with defaults
#   ./wait-for-gitlab.sh --timeout 900  # Custom timeout (15 min)

set -euo pipefail

# Configuration
GITLAB_URL="${GITLAB_URL:-http://localhost:8080}"
TIMEOUT="${TIMEOUT:-600}"  # 10 minutes default
INTERVAL="${INTERVAL:-10}"  # Check every 10 seconds

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --url)
            GITLAB_URL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--timeout SECONDS] [--interval SECONDS] [--url URL]"
            echo ""
            echo "Options:"
            echo "  --timeout   Maximum wait time in seconds (default: 600)"
            echo "  --interval  Check interval in seconds (default: 10)"
            echo "  --url       GitLab URL (default: http://localhost:8080)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo_error "curl is required but not installed"
    exit 1
fi

echo_info "Waiting for GitLab at ${GITLAB_URL}"
echo_info "Timeout: ${TIMEOUT}s, Check interval: ${INTERVAL}s"
echo ""

start_time=$(date +%s)
last_status=""

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))

    # Check timeout
    if [[ $elapsed -ge $TIMEOUT ]]; then
        echo ""
        echo_error "Timeout waiting for GitLab after ${TIMEOUT}s"
        echo_info "Try checking logs: docker compose logs gitlab"
        exit 1
    fi

    # Try the readiness endpoint
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "${GITLAB_URL}/-/readiness" 2>/dev/null || echo "000")

    # Show progress
    minutes=$((elapsed / 60))
    seconds=$((elapsed % 60))
    progress="[${minutes}m ${seconds}s / $((TIMEOUT / 60))m]"

    case $http_code in
        200)
            echo ""
            echo_success "GitLab is ready! ${progress}"

            # Additional check - verify the API is responding
            echo_info "Verifying API accessibility..."
            api_code=$(curl -s -o /dev/null -w "%{http_code}" "${GITLAB_URL}/api/v4/version" 2>/dev/null || echo "000")

            if [[ "$api_code" == "200" ]] || [[ "$api_code" == "401" ]]; then
                echo_success "API is accessible"
                echo ""
                echo_success "GitLab is fully operational!"
                echo_info "URL: ${GITLAB_URL}"
                exit 0
            else
                echo_info "API not ready yet (HTTP $api_code), continuing to wait..."
            fi
            ;;
        502|503)
            if [[ "$last_status" != "starting" ]]; then
                echo_info "GitLab is starting up (HTTP $http_code)... ${progress}"
                last_status="starting"
            else
                printf "."
            fi
            ;;
        000)
            if [[ "$last_status" != "connecting" ]]; then
                echo_info "Waiting for GitLab to accept connections... ${progress}"
                last_status="connecting"
            else
                printf "."
            fi
            ;;
        *)
            echo_info "Unexpected response (HTTP $http_code)... ${progress}"
            last_status="unexpected"
            ;;
    esac

    sleep "$INTERVAL"
done
