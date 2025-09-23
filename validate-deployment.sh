#!/bin/bash

echo "=== Deployment Validation Script ==="
echo "This script validates that all services are running correctly after deployment"
echo ""

# Configuration
BASE_URL=${FIREFLY_BASE_URL:-"http://localhost:8080"}
TIMEOUT=${TIMEOUT:-60}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }

# Test service health
test_service() {
    local url=$1
    local service_name=$2
    local expected_status=${3:-200}
    local timeout=${4:-30}
    
    log_info "Testing $service_name at $url"
    
    for i in $(seq 1 $timeout); do
        response=$(curl -s -w "%{http_code}" -o /tmp/response "$url" 2>/dev/null)
        
        if [ "$response" = "$expected_status" ] || [ "$response" = "302" ] || [ "$response" = "200" ]; then
            log_info "✅ $service_name: HTTP $response"
            return 0
        fi
        
        if [ $i -eq $timeout ]; then
            log_error "❌ $service_name: Timeout after ${timeout}s (last status: $response)"
            return 1
        fi
        
        echo -n "."
        sleep 2
    done
}

# Test API endpoint with token
test_api_with_token() {
    local endpoint=$1
    local service_name=$2
    local token=$3
    
    if [ -z "$token" ]; then
        log_warn "No token provided for $service_name API test"
        return 1
    fi
    
    log_info "Testing $service_name API: $endpoint"
    
    response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $token" \
        -H "Accept: application/json" \
        -o /tmp/api_response \
        "$endpoint")
    
    if [ "$response" = "200" ]; then
        log_info "✅ $service_name API: Success"
        log_debug "Response: $(cat /tmp/api_response | head -100)"
        return 0
    else
        log_error "❌ $service_name API: HTTP $response"
        log_debug "Response: $(cat /tmp/api_response)"
        return 1
    fi
}

# Test Docker containers
test_containers() {
    log_info "Checking Docker containers..."
    
    local containers=("firefly_iii_core" "firefly_iii_db" "firefly_iii_ai_service" "firefly_iii_webhook_service" "firefly_iii_importer")
    local failed=0
    
    for container in "${containers[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
            status=$(docker ps --format "{{.Names}}\t{{.Status}}" | grep "^${container}" | cut -f2)
            log_info "✅ $container: $status"
        else
            log_error "❌ $container: Not running"
            failed=1
        fi
    done
    
    return $failed
}

# Test network connectivity
test_network() {
    log_info "Testing network connectivity..."
    
    local ports=("8080" "8082" "8001" "81")
    local host=$(echo $BASE_URL | sed 's|http[s]*://||' | cut -d':' -f1)
    
    for port in "${ports[@]}"; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log_info "✅ Port $port: Open"
        else
            log_error "❌ Port $port: Closed or unreachable"
        fi
    done
}

# Load environment tokens
load_tokens() {
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
}

# Main validation
main() {
    log_info "Starting deployment validation..."
    log_info "Target URL: $BASE_URL"
    
    local tests_passed=0
    local total_tests=0
    
    # Load environment
    load_tokens
    
    # Test 1: Docker containers
    total_tests=$((total_tests + 1))
    if test_containers; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 2: Network connectivity
    total_tests=$((total_tests + 1))
    if test_network; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 3: Firefly III Core
    total_tests=$((total_tests + 1))
    if test_service "$BASE_URL" "Firefly III Core" "302"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 4: AI Categorizer
    total_tests=$((total_tests + 1))
    ai_url=$(echo $BASE_URL | sed 's/:8080/:8082/')/health
    if test_service "$ai_url" "AI Categorizer" "200"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 5: Webhook Service
    total_tests=$((total_tests + 1))
    webhook_url=$(echo $BASE_URL | sed 's/:8080/:8001/')/health
    if test_service "$webhook_url" "Webhook Service" "200"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 6: Data Importer
    total_tests=$((total_tests + 1))
    importer_url=$(echo $BASE_URL | sed 's/:8080/:81/')
    if test_service "$importer_url" "Data Importer" "302"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 7: Firefly III API
    total_tests=$((total_tests + 1))
    if test_api_with_token "$BASE_URL/api/v1/about" "Firefly III" "$FIREFLY_TOKEN2"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Results
    echo ""
    echo "=================================================="
    echo "📊 VALIDATION RESULTS"
    echo "=================================================="
    echo "Tests Passed: $tests_passed/$total_tests"
    echo "Success Rate: $(( tests_passed * 100 / total_tests ))%"
    echo ""
    
    if [ $tests_passed -eq $total_tests ]; then
        log_info "🎉 All validation tests passed! Deployment is successful."
        echo ""
        echo "🌐 Services are available at:"
        echo "   Firefly III: $BASE_URL"
        echo "   AI Service: $(echo $BASE_URL | sed 's/:8080/:8082/')"
        echo "   Webhook Service: $(echo $BASE_URL | sed 's/:8080/:8001/')"
        echo "   Data Importer: $(echo $BASE_URL | sed 's/:8080/:81/')"
        return 0
    else
        log_error "❌ Some validation tests failed. Please check the logs above."
        echo ""
        echo "🔧 Troubleshooting steps:"
        echo "1. Check container logs: docker compose logs"
        echo "2. Verify environment files: .env, .db.env"
        echo "3. Run debug script: ./ec2-debug.sh"
        return 1
    fi
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi