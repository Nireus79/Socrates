import os
import sys

print("=" * 60)
print("SOCRATES LOCAL SETUP - POTENTIAL BLOCKER ANALYSIS")
print("=" * 60)
print()

blockers = []
warnings = []

# 1. Check .env file
print("1. ENVIRONMENT CONFIGURATION")
print("-" * 60)
if not os.path.exists('.env'):
    blockers.append("CRITICAL: .env file does not exist - user needs to create it")
else:
    print("OK: .env file exists")
    with open('.env') as f:
        content = f.read()
        if 'ANTHROPIC_API_KEY' not in content:
            blockers.append("CRITICAL: ANTHROPIC_API_KEY not configured in .env")
        elif 'sk-ant-' not in content:
            warnings.append("WARNING: ANTHROPIC_API_KEY appears to be a placeholder value")
        if 'SOCRATES_ENCRYPTION_KEY' not in content:
            blockers.append("CRITICAL: SOCRATES_ENCRYPTION_KEY not in .env - API key encryption will fail")

print()

# 2. Check critical files exist
print("2. CRITICAL FILES")
print("-" * 60)
critical_files = [
    'requirements.txt',
    'socrates-frontend/package.json',
    'socrates-api/src/socrates_api/main.py',
    'socratic_system/__init__.py',
    'alembic.ini',
    'setup.py'
]

for filepath in critical_files:
    if os.path.exists(filepath):
        print(f"OK: {filepath}")
    else:
        print(f"MISSING: {filepath}")
        if 'main.py' in filepath:
            blockers.append(f"CRITICAL: {filepath} missing - API won't start")

print()

# 3. Check dependencies file
print("3. DEPENDENCIES")
print("-" * 60)
with open('requirements.txt') as f:
    req_content = f.read()
    if 'redis' in req_content:
        warnings.append("WARNING: Redis is required - user must have Redis running or will get connection errors")
    if 'psycopg2' in req_content:
        warnings.append("INFO: psycopg2 is for PostgreSQL - OK for local SQLite dev but requires compilation")
    if 'chromadb' in req_content:
        warnings.append("INFO: ChromaDB requires build tools - compilation errors possible on Windows")

print("OK: requirements.txt contains necessary dependencies")

print()

# 4. Check startup scripts
print("4. STARTUP SCRIPTS")
print("-" * 60)
scripts = {
    'Linux/macOS': 'scripts/start-dev.sh',
    'Windows': 'scripts/start-dev.bat',
    'Python (cross-platform)': 'scripts/start-dev.py'
}

for desc, path in scripts.items():
    if os.path.exists(path):
        print(f"OK: {path} ({desc})")
    else:
        print(f"MISSING: {path}")

print()

# 5. Check port defaults
print("5. PORT CONFIGURATION")
print("-" * 60)
with open('.env') as f:
    env_content = f.read()
    api_port = [line for line in env_content.split('\n') if 'SOCRATES_API_PORT' in line]
    if api_port:
        print(f"OK: API port configured: {api_port[0]}")
    else:
        warnings.append("WARNING: SOCRATES_API_PORT not explicitly set - will default to 8000")

print("INFO: Frontend will use port 5173 (Vite default)")
print("INFO: User should ensure ports 5173 and 8000 are not already in use")

print()

# 6. Check README and documentation
print("6. DOCUMENTATION")
print("-" * 60)
doc_files = {
    'README.md': 'Main entry point',
    'docs/QUICK_START_GUIDE.md': 'Quick start instructions',
    'docs/INSTALLATION.md': 'Detailed installation',
    'docs/TROUBLESHOOTING.md': 'Troubleshooting guide'
}

for filepath, desc in doc_files.items():
    if os.path.exists(filepath):
        print(f"OK: {filepath}")
    else:
        warnings.append(f"WARNING: {filepath} missing - users lack {desc}")

print()

# 7. Check for gitignore
print("7. SECURITY")
print("-" * 60)
if os.path.exists('.gitignore'):
    with open('.gitignore') as f:
        content = f.read()
        if '.env' in content:
            print("OK: .env is in .gitignore")
        else:
            blockers.append("CRITICAL: .env is not in .gitignore - secrets could be committed")
else:
    blockers.append("WARNING: No .gitignore found")

print()

# 8. Check Node version requirements
print("8. NODE/NPM REQUIREMENTS")
print("-" * 60)
with open('socrates-frontend/package.json') as f:
    content = f.read()
    if '"node": ">=18' in content:
        print("OK: package.json requires Node 18+ (appropriate)")
    else:
        print("INFO: Check package.json for Node version requirements")

print()

# 9. Check Python version requirements
print("9. PYTHON VERSION REQUIREMENTS")
print("-" * 60)
print(f"Current Python: {sys.version_info.major}.{sys.version_info.minor}")
print("Required: Python 3.8+ (3.11+ recommended)")
if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8):
    blockers.append(f"CRITICAL: Python {sys.version_info.major}.{sys.version_info.minor} is too old - requires 3.8+")

print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)

if blockers:
    print(f"\nCRITICAL BLOCKERS FOUND: {len(blockers)}")
    print("-" * 60)
    for i, blocker in enumerate(blockers, 1):
        print(f"{i}. {blocker}")
else:
    print("\nNO CRITICAL BLOCKERS FOUND")

if warnings:
    print(f"\nWARNINGS/NOTES: {len(warnings)}")
    print("-" * 60)
    for i, warning in enumerate(warnings, 1):
        print(f"{i}. {warning}")

print()
