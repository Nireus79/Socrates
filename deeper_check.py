import os
import re

print("DEEPER BLOCKER ANALYSIS")
print("=" * 60)
print()

# Check if Redis is actually required or optional
print("1. REDIS REQUIREMENT ANALYSIS")
print("-" * 60)
redis_essential = False

# Check main code
for root, dirs, files in os.walk('socratic_system'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                    # Check for redis imports without try/except
                    if 'import redis' in content or 'from redis' in content:
                        if 'try:' not in content[:content.find('import redis') + 200]:
                            print(f"Found: redis imported in {path}")
            except:
                pass

# Check if Redis can be optional
with open('requirements.txt') as f:
    if 'redis' in f.read().lower():
        print("Redis is listed in requirements.txt (might be optional)")
        
print()

# Check for compilation requirements
print("2. WINDOWS BUILD TOOLS REQUIREMENT")
print("-" * 60)
c_extension_packages = {
    'chromadb': 'Vector database - needs compilation',
    'sentence-transformers': 'ML library - needs compilation', 
    'cryptography': 'Encryption - needs compilation',
    'psycopg2': 'PostgreSQL driver - needs compilation'
}

with open('requirements.txt') as f:
    reqs = f.read()
    
has_c_extensions = False
for pkg, desc in c_extension_packages.items():
    if pkg in reqs:
        has_c_extensions = True
        print(f"Found: {pkg} - {desc}")

if has_c_extensions:
    print("\nWARNING: Package installation may fail on Windows without:")
    print("- Visual C++ Build Tools")
    print("- Python development headers")
    print("- Sometimes: Rust compiler (for some packages)")

print()

# Check for hardcoded paths
print("3. HARDCODED PATHS CHECK")
print("-" * 60)
hardcoded_found = False

for root, dirs, files in os.walk('socratic_system'):
    # Skip cache and build dirs
    if '__pycache__' in root or '.egg' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        # Look for hardcoded absolute paths
                        if '/home/' in line or '/Users/' in line or 'C:\' in line:
                            if '#' not in line[:line.find('/')]:  # Not a comment
                                print(f"{path}:{i+1}: {line.strip()}")
                                hardcoded_found = True
            except:
                pass

if not hardcoded_found:
    print("No hardcoded absolute paths detected")

print()

# Check for missing imports or dependencies
print("4. IMPORT VERIFICATION")
print("-" * 60)
try:
    import fastapi
    print("OK: FastAPI can be imported")
except:
    print("MISSING: FastAPI - required for API")

try:
    import pydantic
    print("OK: Pydantic can be imported")
except:
    print("MISSING: Pydantic - required for validation")

try:
    import sqlite3
    print("OK: SQLite is available (built-in)")
except:
    print("MISSING: SQLite - required for local dev")

print()

# Check startup script content
print("5. STARTUP SCRIPT ANALYSIS")
print("-" * 60)

with open('scripts/start-dev.bat', 'r') as f:
    bat_content = f.read()
    
with open('scripts/start-dev.sh', 'r') as f:
    sh_content = f.read()

# Check for node_modules handling
if 'npm install' in sh_content:
    print("OK: start-dev.sh handles npm install")
if 'pip install' in sh_content or 'Requirements' in sh_content:
    print("Note: start-dev.sh does not auto-install Python dependencies")
    print("      User must manually: pip install -r requirements.txt")

print()

# Check for .env file setup
print("6. .ENV SETUP IN STARTUP SCRIPTS")
print("-" * 60)

if '.env' in sh_content and 'copy' in sh_content.lower():
    print("Note: startup script expects .env to already exist")
    print("      Must be created before running scripts")
elif '.env' not in sh_content:
    print("WARNING: Scripts don't mention .env setup")
    print("         Users must create .env manually")

print()

# Check database initialization
print("7. DATABASE INITIALIZATION")
print("-" * 60)

if os.path.exists('alembic.ini'):
    print("OK: alembic.ini exists for migrations")
    print("Note: User should run 'alembic upgrade head' before starting")
    
    # Check if startup scripts run migrations
    if 'alembic' not in sh_content and 'alembic' not in bat_content:
        print("WARNING: Startup scripts do NOT run database migrations")
        print("         Database may not be initialized properly")

