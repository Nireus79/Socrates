# Uninstall & Recovery Guide

Complete guide for safely uninstalling Socrates AI and recovering from data loss or corruption.

---

## Table of Contents

- [Before Uninstalling](#before-uninstalling)
- [Uninstallation Procedures](#uninstallation-procedures)
- [Data Recovery](#data-recovery)
- [Backup Restoration](#backup-restoration)
- [Emergency Procedures](#emergency-procedures)

---

## Before Uninstalling

### Backup Your Data

**⚠️ CRITICAL**: Always backup before uninstalling!

**Quick Backup** (5 minutes):

1. **Backup all projects**:
   ```bash
   cd ~/.socrates
   zip -r ~/socrates_backup_$(date +%Y%m%d).zip .
   ```

2. **Or backup by exporting projects**:
   ```bash
   for project in $(ls projects.db | awk '{print $1}'); do
     /project export "$project"
   done
   ```

3. **Or via API**:
   ```python
   from socratic_system.orchestration import AgentOrchestrator

   orch = AgentOrchestrator("sk-ant-...")
   projects = orch.process_request('project_manager', {
       'action': 'list_projects'
   })['projects']

   for proj in projects:
       export = orch.process_request('project_manager', {
           'action': 'export_project',
           'project_id': proj['id'],
           'format': 'json'
       })
       # Save export to file
   ```

### Export Critical Projects

**For important projects**:
```bash
# CLI
/project export <project_name> --format json

# Creates: <project_name>_export.json
```

### Verify Backups

**Test that backups work**:
```bash
# Check backup file
ls -lh ~/socrates_backup_*.zip

# Or check exports
ls -lh *_export.json
```

---

## Uninstallation Procedures

### Windows - Control Panel (Easiest)

1. **Open Settings**
   - Press Windows + I
   - Click "Apps" → "Apps & features"

2. **Find Socrates AI**
   - Scroll through list
   - Find "Socrates AI" or "Socrates"

3. **Uninstall**
   - Click on Socrates AI
   - Click "Uninstall"
   - Follow prompts
   - Click "Finish" to complete

4. **Verify Removal**
   - Check Programs files:
   - `C:\Program Files\Socrates` should be gone

### Windows - Manual Deletion

**If uninstaller doesn't work**:

1. **Stop the application**
   - Close Socrates completely
   - Close command prompt/PowerShell windows

2. **Delete program files**
   ```powershell
   # Navigate to installation directory
   cd "C:\Program Files\Socrates"

   # Remove directory
   Remove-Item -Recurse -Force .
   ```

3. **Remove shortcuts**
   ```powershell
   # Desktop shortcut
   Remove-Item "$env:USERPROFILE\Desktop\Socrates AI.lnk" -Force

   # Start Menu
   Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Socrates*" -Force
   ```

4. **Remove from Registry** (Optional, for cleanup)
   ```powershell
   # Remove app from Add/Remove Programs list
   Remove-Item "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Socrates*" -Force
   ```

### macOS - Application Removal

1. **Close Socrates**
   - Cmd+Q to quit

2. **Remove from Applications**
   ```bash
   # If installed via Homebrew
   brew uninstall socrates

   # Or delete manually
   rm -rf /Applications/Socrates.app
   ```

3. **Remove symbolic links**
   ```bash
   which socrates  # Find location
   rm /usr/local/bin/socrates  # Remove if there
   ```

### Linux - Package Manager

1. **Via Package Manager**
   ```bash
   # Ubuntu/Debian (if installed via APT)
   sudo apt remove socrates
   sudo apt purge socrates  # Remove config too

   # Fedora
   sudo dnf remove socrates

   # Arch
   sudo pacman -R socrates
   ```

2. **Manual Removal**
   ```bash
   # Remove installation
   sudo rm -rf /opt/socrates

   # Remove symlink
   sudo rm /usr/local/bin/socrates
   ```

### Remove Data Directory

**⚠️ WARNING**: This deletes all projects and settings!

**After uninstalling the application**:

```bash
# Linux/macOS
rm -rf ~/.socrates

# Windows PowerShell
Remove-Item "$env:USERPROFILE\.socrates" -Recurse -Force

# Windows CMD
rmdir %USERPROFILE%\.socrates /s /q
```

---

## Data Recovery

### Recover Deleted Project

**If you deleted a project but have backup**:

```bash
# Restore from export
/project import <project_name>_export.json

# Or programmatically
import json
with open('<project_name>_export.json', 'r') as f:
    project_data = json.load(f)
```

### Recover from Database Backup

**If you created `projects.db.backup`**:

1. **Stop Socrates**
   ```bash
   # Press Ctrl+C in the running terminal
   ```

2. **Restore backup**
   ```bash
   # Linux/macOS
   cp ~/.socrates/projects.db.corrupt ~/.socrates/projects.db.$(date +%s)
   cp ~/.socrates/projects.db.backup ~/.socrates/projects.db

   # Windows PowerShell
   Copy-Item "$env:USERPROFILE\.socrates\projects.db" -Destination "$env:USERPROFILE\.socrates\projects.db.corrupt"
   Copy-Item "$env:USERPROFILE\.socrates\projects.db.backup" -Destination "$env:USERPROFILE\.socrates\projects.db"
   ```

3. **Restart Socrates**
   ```bash
   python socrates.py
   ```

4. **Verify**
   ```bash
   /project list
   # Should show restored projects
   ```

### Recover from Full Directory Backup

**If you backed up entire `~/.socrates` directory**:

```bash
# Linux/macOS
cp -r ~/socrates_backup_20260115 ~/.socrates

# Windows PowerShell
Copy-Item -Path "C:\Users\YourName\socrates_backup_20260115" -Destination "$env:USERPROFILE\.socrates" -Recurse
```

### Recover Specific Documents from Vector DB

**If knowledge base was deleted**:

1. **Reimport documents**
   ```bash
   # Via CLI
   /document import path/to/documents

   # Or from API
   orchestrator.process_request('knowledge_manager', {
       'action': 'import_documents',
       'file_paths': ['/path/to/doc1.pdf', '/path/to/doc2.pdf']
   })
   ```

2. **Or rebuild from backups**
   ```python
   # If you have backed up exports with documents
   # Re-import all project exports
   for export_file in glob.glob("*_export.json"):
       orchestrator.process_request('project_manager', {
           'action': 'import_project',
           'data': export_data
       })
   ```

---

## Backup Restoration

### From Exported Projects

**Best method if you exported before issues**:

```bash
# Single project
/project import my_project_export.json

# Multiple projects
for file in *_export.json; do
  /project import "$file"
  echo "Imported: $file"
done
```

### From ZIP Backup

**If you backed up entire directory**:

```bash
# Linux/macOS
unzip -d ~/ ~/socrates_backup_20260115.zip

# Windows PowerShell
Expand-Archive -Path "C:\socrates_backup_20260115.zip" -DestinationPath "$env:USERPROFILE"
```

### Partial Restoration (Specific Projects)

**If you don't want to restore everything**:

```bash
# List what's in backup
unzip -l ~/socrates_backup.zip

# Extract specific files
unzip ~/socrates_backup.zip "projects.db"
# Then copy to ~/.socrates/
```

### From Version Control

**If you tracked exports in Git**:

```bash
git log --name-only -- "*_export.json"  # Find old exports
git checkout <commit-hash> -- <project_export.json>  # Restore old version
```

---

## Emergency Procedures

### Database Corruption Recovery

**Symptoms**: "Database disk image is malformed" errors

**Recovery**:

1. **Create new database from exports**
   ```bash
   # Backup corrupted database
   mv ~/.socrates/projects.db ~/.socrates/projects.db.corrupt

   # Stop and restart Socrates (creates empty DB)
   python socrates.py

   # Then import projects from backups
   /project import *_export.json
   ```

2. **Or attempt repair**
   ```bash
   # Linux/macOS
   sqlite3 ~/.socrates/projects.db "PRAGMA integrity_check;"

   # If issues found, try recovery
   sqlite3 ~/.socrates/projects.db ".recover" | sqlite3 ~/.socrates/projects.db.recovered
   ```

### Complete Data Loss

**If database and backups are gone**:

1. **Uninstall and reinstall**
   ```bash
   # Follow uninstallation procedures above
   # Then reinstall fresh
   pip install socrates-ai
   python socrates.py
   ```

2. **Manually recreate projects**
   - Start a new project
   - Re-enter specifications from memory/notes
   - Rebuild from scratch

3. **Recover from external sources**
   - Generated code (check file system)
   - Conversation records (check logs)
   - Exported documents (check file system)

### Vector Database Corruption

**Symptoms**: Strange search results or query errors

**Recovery**:

```bash
# Backup current vector DB
mv ~/.socrates/vector_db ~/.socrates/vector_db.corrupt

# Restart Socrates - it rebuilds automatically
python socrates.py

# Re-import documents if needed
/document import /path/to/documents
```

---

## Prevention Best Practices

### 1. Regular Backups

**Weekly**:
```bash
# Create automated backup
echo "zip -r ~/socrates_backup_\$(date +\%Y\%m\%d).zip ~/.socrates" | crontab -
```

**Monthly**:
```bash
# Full backup to external drive
cp -r ~/.socrates /mnt/backup/socrates_$(date +%Y%m)
```

### 2. Export Projects Regularly

```bash
# Automate exports
for project in $(/project list --quiet); do
  /project export "$project" --format json
done
```

### 3. Test Recovery

```bash
# Monthly: test backup restoration
# Extract backup to temp location
# Verify all projects restored correctly
```

### 4. Version Control Important Exports

```bash
# Track exported projects in Git
git add *_export.json
git commit -m "Backup project exports"
git push
```

### 5. Off-Site Backups

```bash
# Copy backups to cloud/external
aws s3 sync ~/socrates_backups/ s3://my-bucket/socrates-backups/
```

---

## Troubleshooting Uninstallation

### Can't Delete Directory

**Error**: "Permission denied" or "Access denied"

**Solutions**:

1. **Stop all processes**
   ```bash
   pkill -f socrates  # Linux/macOS
   taskkill /IM python.exe /F  # Windows
   ```

2. **Run as administrator**
   ```bash
   # Windows: Right-click PowerShell → Run as Administrator
   # macOS/Linux: Use sudo
   sudo rm -rf ~/.socrates
   ```

3. **Manually close applications**
   - Close text editor viewing files in directory
   - Close file manager browsing directory
   - Close any Python IDE accessing code

### Registry Issues (Windows)

**If uninstaller failed to clean registry**:

```powershell
# Remove orphaned registry entries
Get-Item -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" |
  Where {$_.GetValue('DisplayName') -like "*Socrates*"} |
  Remove-Item
```

### Leftover Files

**Check for remaining files**:

```bash
# Linux/macOS
find ~ -name "*socrates*" -type f 2>/dev/null

# Windows PowerShell
Get-ChildItem -Recurse -Filter "*socrates*"
```

---

## Verify Complete Removal

**After uninstalling**:

```bash
# Linux/macOS - should return nothing
which socrates
find ~ -name ".socrates" 2>/dev/null

# Windows PowerShell
Get-Command socrates -ErrorAction SilentlyContinue
```

---

## Getting Help

- **Backup issues?** See [PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md)
- **Data recovery?** Check troubleshooting above
- **Still having issues?** [Open GitHub Issue](https://github.com/Nireus79/Socrates/issues)

---

**Last Updated**: January 2026
**Version**: 1.3.0
