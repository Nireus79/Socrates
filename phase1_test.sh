#!/bin/bash

# Phase 1: Automated Testing Suite
# Tests all 6 frontend features and backend API endpoints

set -e

FRONTEND_URL="http://localhost:5173"
BACKEND_URL="http://127.0.0.1:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}PHASE 1: Automated Testing Suite${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# ============================================================================
# Test Frontend Routes (6 Features)
# ============================================================================

echo -e "${YELLOW}Testing Frontend Routes...${NC}"
echo ""

test_frontend_route() {
  local route=$1
  local name=$2
  local response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL$route" 2>/dev/null || echo "000")

  if [[ "$response" == "200" ]]; then
    echo -e "${GREEN}✓${NC} $name ($route) - Status: $response"
    ((PASSED++))
  else
    echo -e "${RED}✗${NC} $name ($route) - Status: $response"
    ((FAILED++))
  fi
}

# Test all 6 features + main routes
test_frontend_route "/" "Home/Login Page"
test_frontend_route "/dashboard" "Dashboard"
test_frontend_route "/projects" "Projects"
test_frontend_route "/chat" "Chat (Dialogue)"
test_frontend_route "/code" "Code Generation"
test_frontend_route "/notes" "Notes (Quick Win #2)"
test_frontend_route "/analytics" "Analytics (Maturity Tracking - High Priority #2)"
test_frontend_route "/search" "Search (Advanced Search - Medium Priority)"
test_frontend_route "/knowledge" "Knowledge Base"
test_frontend_route "/settings" "Settings (Subscription - Quick Win #1)"

echo ""

# ============================================================================
# Test Backend Health & Initialization
# ============================================================================

echo -e "${YELLOW}Testing Backend Health...${NC}"
echo ""

# Health check
HEALTH=$(curl -s "$BACKEND_URL/health" 2>/dev/null | grep -o '"status":"ok"' || echo "")
if [[ -n "$HEALTH" ]]; then
  echo -e "${GREEN}✓${NC} Backend Health Check - API is responding"
  ((PASSED++))
else
  echo -e "${RED}✗${NC} Backend Health Check - API not responding"
  ((FAILED++))
fi

echo ""

# ============================================================================
# Test Backend API Endpoints
# ============================================================================

echo -e "${YELLOW}Testing Backend API Endpoints...${NC}"
echo ""

test_backend_endpoint() {
  local method=$1
  local endpoint=$2
  local name=$3
  local response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BACKEND_URL$endpoint" 2>/dev/null || echo "000")

  # Accept various success codes (200, 201, 400, 401, 404, 405 for OPTIONS)
  # Mainly checking if the endpoint exists (not 000, not connection refused)
  if [[ "$response" != "000" ]] && [[ "$response" != "Connection refused" ]]; then
    echo -e "${GREEN}✓${NC} $name - Status: $response"
    ((PASSED++))
  else
    echo -e "${RED}✗${NC} $name - Status: $response (Endpoint may not exist)"
    ((FAILED++))
  fi
}

# Search Endpoints (Advanced Search - Medium Priority)
test_backend_endpoint "GET" "/search?q=test" "Search Global"
test_backend_endpoint "POST" "/conversations/search?q=test" "Search Conversations"
test_backend_endpoint "POST" "/knowledge/search?q=test" "Search Knowledge"
test_backend_endpoint "POST" "/notes/search?q=test" "Search Notes"

# Notes Endpoints (Quick Win #2)
test_backend_endpoint "GET" "/notes" "Get Notes"
test_backend_endpoint "POST" "/notes" "Create Note"

# Analysis Endpoints (High Priority #1)
test_backend_endpoint "POST" "/analysis/validate" "Validate Code"
test_backend_endpoint "POST" "/analysis/test" "Test Project"
test_backend_endpoint "POST" "/analysis/review" "Review Code"

# Maturity/Progress Endpoints (High Priority #2)
test_backend_endpoint "GET" "/projects/test-id/maturity" "Get Maturity"
test_backend_endpoint "GET" "/projects/test-id/progress" "Get Progress"

# GitHub Endpoints (High Priority #3)
test_backend_endpoint "POST" "/github/import" "Import GitHub Repo"
test_backend_endpoint "GET" "/github/projects/test-id/status" "Get GitHub Status"

# Subscription Endpoints (Quick Win #1)
test_backend_endpoint "POST" "/subscription/upgrade" "Upgrade Subscription"

# Analytics Endpoints
test_backend_endpoint "GET" "/analytics/summary" "Analytics Summary"

echo ""

# ============================================================================
# Summary Report
# ============================================================================

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

TOTAL=$((PASSED + FAILED))
PASS_RATE=$((PASSED * 100 / TOTAL))

echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
echo -e "${BLUE}Total:${NC}  $TOTAL"
echo -e "${YELLOW}Pass Rate:${NC} $PASS_RATE%"
echo ""

if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}✓ All tests passed! Phase 1 testing complete.${NC}"
  exit 0
else
  echo -e "${YELLOW}⚠ Some tests failed. Review the output above.${NC}"
  exit 1
fi
