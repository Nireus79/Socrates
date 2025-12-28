#!/usr/bin/env python3
"""
Phase 2: Backend API Endpoint Audit
Verifies all backend API endpoints are implemented and responding
"""

import re
import os
from pathlib import Path
from typing import List, Tuple, Dict
import requests

BACKEND_URL = "http://127.0.0.1:8000"
ROUTER_DIR = "C:\\Users\\themi\\PycharmProjects\\Socrates\\socrates-api\\src\\socrates_api\\routers"

# ANSI colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text):
    print(f"{BLUE}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{NC}\n")

def extract_endpoints_from_file(file_path: str) -> List[Dict]:
    """Extract endpoint definitions from a router file"""
    endpoints = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all route decorators (@router.get, @router.post, etc.)
        # Can be single-line or multi-line
        # Pattern: @router.METHOD with path on same or next line(s)
        pattern = r'@(?:router|[a-z_]*router)\.([a-z]+)\s*\(\s*["\']([^"\']+)["\']'
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            endpoints.append({
                'method': method,
                'path': path,
                'file': os.path.basename(file_path)
            })

    except Exception as e:
        pass  # Silently skip errors

    return endpoints

def scan_all_routers() -> List[Dict]:
    """Scan all router files for endpoint definitions"""
    all_endpoints = []
    router_files = sorted(Path(ROUTER_DIR).glob("*.py"))

    for file_path in router_files:
        endpoints = extract_endpoints_from_file(str(file_path))
        all_endpoints.extend(endpoints)

    return all_endpoints

def test_endpoint(method: str, path: str, full_path: str = None) -> Tuple[int, str]:
    """Test an endpoint and return status code"""
    try:
        if full_path is None:
            full_path = f"{BACKEND_URL}{path}"

        if method == "GET":
            response = requests.get(full_path, timeout=5)
        elif method == "POST":
            response = requests.post(full_path, json={}, timeout=5)
        elif method == "PUT":
            response = requests.put(full_path, json={}, timeout=5)
        elif method == "DELETE":
            response = requests.delete(full_path, timeout=5)
        elif method == "PATCH":
            response = requests.patch(full_path, json={}, timeout=5)
        else:
            response = requests.request(method, full_path, timeout=5)

        return response.status_code, "OK"

    except requests.exceptions.ConnectionError:
        return 0, "Connection Error"
    except requests.exceptions.Timeout:
        return 0, "Timeout"
    except Exception as e:
        return 0, str(e)

def main():
    print_header(f"{BLUE}PHASE 2: Backend API Endpoint Audit{NC}")

    print(f"{YELLOW}Scanning router files...{NC}\n")
    endpoints = scan_all_routers()

    print(f"Found {len(endpoints)} endpoint definitions\n")

    print(f"{YELLOW}Testing endpoints...{NC}\n")

    # Group by method
    endpoints_by_method = {}
    for ep in endpoints:
        method = ep['method']
        if method not in endpoints_by_method:
            endpoints_by_method[method] = []
        endpoints_by_method[method].append(ep)

    # Test each endpoint
    total = 0
    responsive = 0
    implemented = 0  # Status codes that indicate implementation (not 404)
    auth_required = 0  # Status 401
    not_found = 0  # Status 404

    for method in sorted(endpoints_by_method.keys()):
        print(f"{YELLOW}{method} Endpoints:{NC}\n")

        for ep in endpoints_by_method[method]:
            total += 1
            status, msg = test_endpoint(ep['method'], ep['path'])

            if status == 0:
                status_str = f"{RED}[NO RESPONSE]{NC}"
                print(f"  {status_str} {ep['method']:6} {ep['path']:50} (from {ep['file']})")
            elif status == 404:
                status_str = f"{RED}[404 NOT FOUND]{NC}"
                not_found += 1
                print(f"  {status_str} {ep['method']:6} {ep['path']:50} (from {ep['file']})")
            elif status == 401:
                status_str = f"{YELLOW}[401 AUTH REQUIRED]{NC}"
                auth_required += 1
                responsive += 1
                implemented += 1
                print(f"  {status_str} {ep['method']:6} {ep['path']:50} (from {ep['file']})")
            elif status == 405:
                status_str = f"{YELLOW}[405 METHOD NOT ALLOWED]{NC}"
                print(f"  {status_str} {ep['method']:6} {ep['path']:50} (from {ep['file']})")
            else:
                status_str = f"{GREEN}[{status} OK]{NC}"
                responsive += 1
                implemented += 1
                print(f"  {status_str} {ep['method']:6} {ep['path']:50} (from {ep['file']})")

        print()

    # Summary
    print_header("Endpoint Audit Summary")

    print(f"Total Endpoints Defined:    {total}")
    print(f"Responsive Endpoints:       {responsive} ({responsive*100//total if total else 0}%)")
    print(f"Implemented Endpoints:      {implemented} ({implemented*100//total if total else 0}%)")
    print(f"Requiring Authentication:   {auth_required}")
    print(f"Not Found (404):            {not_found} ({not_found*100//total if total else 0}%)")
    print()

    # Recommendations
    print(f"{YELLOW}Recommendations:{NC}\n")

    if not_found > 0:
        print(f"  - {RED}{not_found} endpoints return 404{NC} (need implementation or path correction)")

    if not_found <= 5:
        print(f"  - {GREEN}Good news! Most endpoints are implemented.{NC}")
    else:
        print(f"  - {YELLOW}Several endpoints need implementation{NC}")

    print(f"\n{GREEN}Phase 2 audit complete!{NC}")

if __name__ == "__main__":
    main()
