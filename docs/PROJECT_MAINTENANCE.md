# Project Maintenance & Cleanup Guide

Complete guide for managing, maintaining, and cleaning up Socrates AI projects and data.

## Table of Contents

- [Project Management](#project-management)
- [Data Storage & Quotas](#data-storage--quotas)
- [Archiving Projects](#archiving-projects)
- [Deleting Projects](#deleting-projects)
- [Database Maintenance](#database-maintenance)
- [Data Backup & Export](#data-backup--export)
- [Cleanup Procedures](#cleanup-procedures)
- [Storage Optimization](#storage-optimization)

---

## Project Management

### Viewing All Projects

**Via CLI:**
```bash
/project list
```

**Via Web UI:**
- Navigate to "Projects" or "Dashboard"
- View all your projects with creation dates and last modified

**Via API:**
```python
from socratic_system.orchestration import AgentOrchestrator

orchestrator = AgentOrchestrator("sk-ant-...")
result = orchestrator.process_request('project_manager', {
    'action': 'list_projects',
    'owner': 'alice'
})
projects = result['projects']
```

### Project Metadata

Each project tracks:
- **Name** - Display name
- **Owner** - User who created it
- **Created** - Timestamp of creation
- **Last Modified** - When last updated
- **Phase** - Current phase (discovery, analysis, design, implementation)
- **Status** - Active, archived, or deleted
- **Size** - Storage used (KB)
- **Context** - Full project specification

---

## Data Storage & Quotas

### Storage Location

**Default data directory:**
- Linux/macOS: `~/.socrates`
- Windows: `%USERPROFILE%\.socrates`
- Custom: Set `SOCRATES_DATA_DIR` environment variable

**Directory contents:**
```
~/.socrates/
├── projects.db              # All project data
├── vector_db/               # Knowledge base vectors
│   ├── chroma.sqlite3       # Vector metadata
│   └── [collections]/       # Embedded documents
├── logs/
│   └── socratic.log         # Application logs
└── [imports]/               # Cached imported documents
```

### Storage Usage

**Check storage usage:**
```bash
# Via CLI
/status

# Via API
result = orchestrator.process_request('system_monitor', {
    'action': 'get_storage_info'
})

# Manual: Check disk space
du -sh ~/.socrates  # Linux/macOS
dir /s %USERPROFILE%\.socrates  # Windows
```

### Storage Quotas

**Default quotas:**
- Free tier: 100 MB storage, 5 projects
- Sponsored tier: 500 MB storage, 20 projects
- Enterprise: Custom

**Check your quota:**
```bash
/subscription status
```

**If quota exceeded:**
1. Archive old projects (see below)
2. Delete unnecessary projects
3. Export and remove large documents
4. Upgrade to higher tier

---

## Archiving Projects

### Why Archive?

- Keep projects for reference without active use
- Free up quota space
- Reduce clutter in active project list
- Maintain historical record

### Archive a Project

**Via CLI:**
```bash
/project archive <project_name>
```

**Via Web UI:**
- Click "..." menu on project card
- Select "Archive"
- Confirm

**Via API:**
```python
result = orchestrator.process_request('project_manager', {
    'action': 'archive_project',
    'project_id': 'proj_123'
})
```

### View Archived Projects

**Via CLI:**
```bash
/project list --archived
```

**Via Web UI:**
- Filter dropdown: Select "Archived Projects"

**Via API:**
```python
result = orchestrator.process_request('project_manager', {
    'action': 'list_projects',
    'status': 'archived'
})
```

### Restore Archived Project

**Via CLI:**
```bash
/project restore <project_name>
```

**Via Web UI:**
- Filter to "Archived Projects"
- Click "..." menu
- Select "Restore"

**Via API:**
```python
result = orchestrator.process_request('project_manager', {
    'action': 'restore_project',
    'project_id': 'proj_123'
})
```

---

## Deleting Projects

### Before Deletion

**⚠️ WARNING: Deletion is permanent!**

**Always backup first:**
```bash
# Export project before deletion
/project export <project_name> --format json
```

This creates `<project_name>_export.json` with all project data.

### Delete a Project

**Via CLI:**
```bash
/project delete <project_name>
# Confirm: Y
```

**Via Web UI:**
- Right-click project card or use "..." menu
- Select "Delete"
- Confirm in dialog

**Via API:**
```python
result = orchestrator.process_request('project_manager', {
    'action': 'delete_project',
    'project_id': 'proj_123'
})
```

### Bulk Delete (Advanced)

Delete multiple projects:

```python
projects_to_delete = ['Old Project 1', 'Old Project 2', 'Test Project']

for project_name in projects_to_delete:
    result = orchestrator.process_request('project_manager', {
        'action': 'delete_project',
        'project_name': project_name
    })
    print(f"Deleted: {project_name}")
```

### Recover Deleted Project

**From backup:**
```bash
# If you exported before deletion
/project import old_project_export.json
```

**From database backup:**
1. Restore `projects.db.backup` to `projects.db`
2. Restart Socrates
3. Project will be restored

---

## Database Maintenance

### Database Integrity Check

**Check database health:**
```bash
# Via CLI
/debug on
/status

# Via API
result = orchestrator.process_request('system_monitor', {
    'action': 'check_database_integrity'
})
```

### Optimize Database

**Reduce file size:**
```bash
# Linux/macOS/Windows (PowerShell)
python -c "
import sqlite3
db = sqlite3.connect('~/.socrates/projects.db')
db.execute('VACUUM')
db.close()
print('Database optimized')
"
```

This recovers space from deleted records.

### Repair Corrupted Database

**If corrupted:**

1. **Stop Socrates**
   - Close the application completely

2. **Backup current database**
   ```bash
   cp ~/.socrates/projects.db ~/.socrates/projects.db.corrupt
   ```

3. **Try recovery**
   ```bash
   python -c "
   import sqlite3
   db = sqlite3.connect('~/.socrates/projects.db')
   db.execute('PRAGMA integrity_check')
   result = db.fetchone()
   print(f'Integrity check: {result}')
   db.close()
   "
   ```

4. **If recovery fails, rebuild**
   ```bash
   rm ~/.socrates/projects.db
   # Restart Socrates - it will recreate empty database
   ```

### Rebuild Vector Database

**If vector search is slow or broken:**

```bash
# Delete vector database
rm -rf ~/.socrates/vector_db

# Restart Socrates
python socrates.py

# It will rebuild automatically
```

This may take time depending on knowledge base size.

---

## Data Backup & Export

### Manual Backup

**Create backups regularly:**

```bash
# Weekly backup
cp -r ~/.socrates ~/.socrates.backup.$(date +%Y%m%d)

# Or via ZIP (compressed)
zip -r socrates_backup_$(date +%Y%m%d).zip ~/.socrates
```

### Automated Backup (Windows)

**Create scheduled task:**

1. Open Task Scheduler
2. Create Basic Task: "Socrates Daily Backup"
3. Trigger: Daily at 2:00 AM
4. Action: Run script:
   ```powershell
   $source = $env:USERPROFILE + '\.socrates'
   $dest = $env:USERPROFILE + '\Backups\socrates_' + (Get-Date -Format 'yyyyMMdd')
   Copy-Item -Path $source -Destination $dest -Recurse
   ```

### Export Individual Project

**Export as JSON:**

```bash
/project export <project_name> --format json
# Creates: <project_name>_export.json
```

**Export as CSV (requirements only):**

```bash
/project export <project_name> --format csv
# Creates: <project_name>_requirements.csv
```

**Export via API:**

```python
result = orchestrator.process_request('project_manager', {
    'action': 'export_project',
    'project_id': 'proj_123',
    'format': 'json'
})
export_data = result['export']
```

### Export All Projects

**Bulk export:**

```python
import json
from pathlib import Path

result = orchestrator.process_request('project_manager', {
    'action': 'list_projects',
    'owner': 'alice'
})

for project in result['projects']:
    export_result = orchestrator.process_request('project_manager', {
        'action': 'export_project',
        'project_id': project['id']
    })

    with open(f"{project['name']}_export.json", "w") as f:
        json.dump(export_result['export'], f, indent=2)
```

### Import Project from Backup

**Restore from export:**

```bash
/project import <project_name>_export.json
```

This creates a new project with the exported data.

---

## Cleanup Procedures

### Weekly Cleanup

1. **Review and archive old projects**
   ```bash
   /project list
   # Archive projects not used in 30+ days
   ```

2. **Check storage usage**
   ```bash
   /status
   ```

3. **Review logs**
   ```bash
   tail -n 100 ~/.socrates/logs/socratic.log
   ```

### Monthly Deep Cleanup

1. **Delete unnecessary test projects**
   ```bash
   /project delete "Test Project 1"
   ```

2. **Optimize database**
   ```bash
   # Manual optimization
   python -c "import sqlite3; sqlite3.connect('~/.socrates/projects.db').execute('VACUUM')"
   ```

3. **Remove old logs**
   ```bash
   # Keep only last 5 log files
   cd ~/.socrates/logs
   ls -t socratic.log* | tail -n +6 | xargs rm
   ```

4. **Check vector DB size**
   ```bash
   du -sh ~/.socrates/vector_db
   # If >500MB, consider reducing knowledge base
   ```

### Quarterly Maintenance

1. **Full database backup**
   ```bash
   zip -r socrates_backup_q1_2026.zip ~/.socrates
   ```

2. **Review project quotas**
   ```bash
   /subscription status
   ```

3. **Update knowledge base**
   - Remove stale documents
   - Add new standards/guidelines

4. **Security audit**
   - Verify API key is still valid
   - Check access logs
   - Rotate passwords if needed

---

## Storage Optimization

### Reduce Vector Database Size

**Remove old documents:**

```python
# List all imported documents
result = orchestrator.process_request('knowledge_manager', {
    'action': 'list_documents'
})

# Remove a specific document
result = orchestrator.process_request('knowledge_manager', {
    'action': 'delete_document',
    'doc_id': 'doc_123'
})
```

### Limit Knowledge Base

**Set max knowledge base size:**

```python
config = ConfigBuilder("sk-ant-...") \
    .with_max_knowledge_size(100)  # MB
    .build()
```

### Compress Old Projects

**Archive projects to ZIP:**

```bash
# Create archive
mkdir ~/.socrates/archived
# Move old project exports to archive
mv *_old_export.json ~/.socrates/archived/
zip -r ~/.socrates/archived/exports_2025.zip ~/.socrates/archived/*.json
```

### Monitor Storage Trends

**Track storage over time:**

```bash
# Create monitoring script
echo "$(date +%Y-%m-%d) - $(du -sh ~/.socrates | cut -f1)" >> ~/socrates_storage_log.txt
tail -n 30 ~/socrates_storage_log.txt
```

---

## Troubleshooting Maintenance Tasks

### "Project not found" on deletion

**Cause**: Project name typo or already deleted

**Solution**:
```bash
/project list  # Get exact names
/project delete "<exact_name>"
```

### Database locked during operation

**Cause**: Another Socrates instance is running

**Solution**:
```bash
# Find running process
ps aux | grep socrates  # Linux/macOS
tasklist | findstr socrates  # Windows

# Kill it
pkill -f socrates
# Then retry operation
```

### Export file too large

**Cause**: Project has years of conversation history

**Solution**:
1. Split into multiple smaller projects
2. Or specify date range (if supported):
   ```bash
   /project export <name> --from "2025-01-01"
   ```

### Insufficient disk space for backup

**Solution**:
1. Delete old backups first
2. Export to external drive
3. Or upgrade disk storage

---

## Best Practices

1. **Backup before major actions** - Always export before deleting
2. **Archive instead of delete** - Keeps historical record
3. **Regular maintenance** - Weekly cleanup keeps system healthy
4. **Monitor quotas** - Know your storage limits
5. **Document your projects** - Add notes about purpose/status
6. **Test recovery** - Periodically test restoring from backup
7. **Automate backups** - Set up scheduled task

---

## Related Documentation

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common problems
- [CONFIGURATION.md](CONFIGURATION.md) - Storage configuration
- [USER_GUIDE.md](USER_GUIDE.md) - Project creation and management
- [API_REFERENCE.md](API_REFERENCE.md) - Programmatic API

---

**Last Updated**: January 2026
**Version**: 1.3.0
