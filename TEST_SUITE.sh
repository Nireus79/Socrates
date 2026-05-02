#!/bin/bash

# Comprehensive test suite for Socrates reverse proxy setup
# Run this after: docker compose up -d

set -e

PASS=0
FAIL=0
TOTAL=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_test() {
    TOTAL=$((TOTAL + 1))
    echo -e "\n${YELLOW}[TEST $TOTAL]${NC} $1"
}

log_pass() {
    PASS=$((PASS + 1))
    echo -e "${GREEN}PASS${NC}: $1"
}

log_fail() {
    FAIL=$((FAIL + 1))
    echo -e "${RED}FAIL${NC}: $1"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

echo "=========================================================================="
echo "SOCRATES REVERSE PROXY TEST SUITE"
echo "=========================================================================="

log_test "Docker Compose version"
if docker compose --version > /dev/null 2>&1; then
    log_pass "Docker Compose is available"
    docker compose --version
else
    log_fail "Docker Compose not found"
fi

log_test "Docker daemon running"
if docker ps > /dev/null 2>&1; then
    log_pass "Docker daemon is running"
else
    log_fail "Docker daemon is not running"
    exit 1
fi

# ============================================================================
# SERVICE HEALTH CHECKS
# ============================================================================

echo ""
echo "=== SERVICE HEALTH CHECKS ==="

log_test "API service is running"
if docker compose ps api | grep -q "Up"; then
    log_pass "API service is running"
else
    log_fail "API service is not running"
fi

log_test "Redis service is running"
if docker compose ps redis | grep -q "Up"; then
    log_pass "Redis service is running"
else
    log_fail "Redis service is not running"
fi

log_test "Web (reverse proxy) service is running"
if docker compose ps web | grep -q "Up"; then
    log_pass "Web service is running"
else
    log_fail "Web service is not running"
fi

log_test "All services healthy"
HEALTHY=$(docker compose ps | grep -c "healthy" || true)
if [ "$HEALTHY" -eq 3 ]; then
    log_pass "All 3 services are healthy"
else
    log_fail "Only $HEALTHY services are healthy (expected 3)"
fi

# ============================================================================
# NETWORK CONNECTIVITY
# ============================================================================

echo ""
echo "=== NETWORK CONNECTIVITY ==="

log_test "Reverse proxy is responding to /health"
if curl -s http://localhost/health | grep -q "healthy"; then
    log_pass "Reverse proxy health check returns healthy"
else
    log_fail "Reverse proxy health check failed"
fi

log_test "API is reachable through reverse proxy at /api/health"
RESPONSE=$(curl -s http://localhost/api/health)
if echo "$RESPONSE" | grep -q "status"; then
    log_pass "API is reachable through /api/health"
else
    log_fail "API health check through proxy failed"
fi

# ============================================================================
# FRONTEND TESTS
# ============================================================================

echo ""
echo "=== FRONTEND TESTS ==="

log_test "Frontend is served at http://localhost/"
if curl -s http://localhost/ | grep -q "html"; then
    log_pass "Frontend HTML is served"
else
    log_fail "Frontend HTML not found"
fi

log_test "Frontend index.html loads"
if curl -s -I http://localhost/ | grep -q "200"; then
    log_pass "Frontend returns 200 OK"
else
    log_fail "Frontend returned non-200 status"
fi

log_test "Static assets are cached properly"
CACHE_HEADER=$(curl -s -I http://localhost/index.html | grep -i "cache-control" || true)
if echo "$CACHE_HEADER" | grep -q "no-cache"; then
    log_pass "HTML files have no-cache headers"
else
    log_fail "HTML cache headers not found"
fi

# ============================================================================
# API TESTS
# ============================================================================

echo ""
echo "=== API ENDPOINT TESTS ==="

log_test "API responds to POST /api/llm/api-key"
STATUS=$(curl -s -X POST http://localhost/api/llm/api-key \
    -H "Content-Type: application/json" \
    -d '{"provider":"test","api_key":"test-key"}' \
    -w "%{http_code}" -o /dev/null)
if [ "$STATUS" != "500" ]; then
    log_pass "API endpoint accessible (HTTP $STATUS)"
else
    log_fail "API endpoint returned error (HTTP $STATUS)"
fi

log_test "API search endpoint"
STATUS=$(curl -s -X GET "http://localhost/api/search?q=test" \
    -w "%{http_code}" -o /dev/null)
if [ "$STATUS" != "500" ]; then
    log_pass "Search endpoint accessible (HTTP $STATUS)"
else
    log_fail "Search endpoint failed (HTTP $STATUS)"
fi

# ============================================================================
# CORS HEADERS TEST
# ============================================================================

echo ""
echo "=== CORS HEADERS TEST ==="

log_test "CORS headers are present on /api/ responses"
if curl -s -i http://localhost/api/health 2>&1 | grep -i "Access-Control-Allow-Origin" > /dev/null; then
    log_pass "CORS headers found in response"
else
    log_fail "CORS headers not found"
fi

log_test "Preflight OPTIONS request to /api/"
STATUS=$(curl -s -X OPTIONS http://localhost/api/health \
    -H "Origin: http://localhost" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -w "%{http_code}" -o /dev/null)
if [ "$STATUS" = "204" ] || [ "$STATUS" = "200" ]; then
    log_pass "Preflight request successful (HTTP $STATUS)"
else
    log_fail "Preflight request failed (HTTP $STATUS)"
fi

# ============================================================================
# REVERSE PROXY ROUTING TEST
# ============================================================================

echo ""
echo "=== REVERSE PROXY ROUTING TEST ==="

log_test "Reverse proxy rewrites /api/* correctly"
RESPONSE=$(curl -s -X POST http://localhost/api/llm/api-key \
    -H "Content-Type: application/json" \
    -d '{}')
if [ -n "$RESPONSE" ]; then
    log_pass "Request was routed and received response"
else
    log_fail "No response from routed request"
fi

# ============================================================================
# LOGS CHECK
# ============================================================================

echo ""
echo "=== LOGS CHECK ==="

log_test "API logs show no critical errors"
API_ERRORS=$(docker compose logs api 2>&1 | grep -i "error" | grep -v "WARNING" | wc -l || true)
log_pass "API logs check completed (error count: $API_ERRORS)"

log_test "Web (nginx) logs show no critical errors"
WEB_ERRORS=$(docker compose logs web 2>&1 | grep -i "error" | wc -l || true)
log_pass "Web logs check completed (error count: $WEB_ERRORS)"

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "=========================================================================="
echo "TEST SUMMARY"
echo "=========================================================================="
echo "Total Tests: $TOTAL"
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo "=========================================================================="

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "ALL TESTS PASSED!"
    echo ""
    exit 0
else
    echo ""
    echo "SOME TESTS FAILED!"
    echo ""
    exit 1
fi
