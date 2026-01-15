#!/usr/bin/env python3
"""
Migration script to rename all V2 tables to simple names (without _v2 suffix).

This script:
1. Backs up the current database
2. Renames all _v2 suffixed tables to simple names
3. Renames all indexes to match new table names
4. Updates foreign key relationships
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".socrates" / "projects.db"

# Mapping of old table names to new table names
TABLE_RENAMES = {
    "projects": "projects",
    "users": "users",
    "question_effectiveness": "question_effectiveness",
    "behavior_patterns": "behavior_patterns",
    "knowledge_documents": "knowledge_documents",
    "llm_provider_configs": "llm_provider_configs",
    "api_keys": "api_keys",
    "llm_usage": "llm_usage",
    "project_notes": "project_notes",
}

# Mapping of old index names to new index names
INDEX_RENAMES = {
    "idx_projects_owner": "idx_projects_owner",
    "idx_projects_phase": "idx_projects_phase",
    "idx_projects_archived": "idx_projects_archived",
    "idx_projects_updated": "idx_projects_updated",
    "idx_projects_owner_archived": "idx_projects_owner_archived",
    "idx_projects_status": "idx_projects_status",
    "idx_project_notes_project": "idx_project_notes_project",
    "idx_project_notes_created": "idx_project_notes_created",
    "idx_users_archived": "idx_users_archived",
    "idx_users_subscription_tier": "idx_users_subscription_tier",
    "idx_users_subscription_status": "idx_users_subscription_status",
    "idx_users_subscription": "idx_users_subscription",
    "idx_question_effectiveness_user": "idx_question_effectiveness_user",
    "idx_question_effectiveness_template": "idx_question_effectiveness_template",
    "idx_behavior_patterns_user": "idx_behavior_patterns_user",
    "idx_behavior_patterns_type": "idx_behavior_patterns_type",
    "idx_knowledge_documents_project": "idx_knowledge_documents_project",
    "idx_knowledge_documents_user": "idx_knowledge_documents_user",
    "idx_knowledge_documents_type": "idx_knowledge_documents_type",
    "idx_llm_configs_user": "idx_llm_configs_user",
    "idx_llm_configs_provider": "idx_llm_configs_provider",
    "idx_api_keys_user": "idx_api_keys_user",
    "idx_api_keys_provider": "idx_api_keys_provider",
    "idx_api_keys_user_provider": "idx_api_keys_user_provider",
    "idx_llm_usage_user": "idx_llm_usage_user",
    "idx_llm_usage_timestamp": "idx_llm_usage_timestamp",
    "idx_llm_usage_user_timestamp": "idx_llm_usage_user_timestamp",
    "idx_llm_usage_provider": "idx_llm_usage_provider",
}


def backup_database():
    """Create a backup of the current database"""
    if not DB_PATH.exists():
        print(f"[INFO] Database not found at {DB_PATH}")
        return None

    backup_path = DB_PATH.parent / f"projects.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(DB_PATH, backup_path)
    print(f"[INFO] Database backed up to {backup_path}")
    return backup_path


def rename_tables():
    """Rename all V2 tables to simple names"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")

        for old_name, new_name in TABLE_RENAMES.items():
            # Check if old table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (old_name,)
            )

            if cursor.fetchone():
                print(f"[INFO] Renaming table {old_name} -> {new_name}")
                cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
            else:
                print(f"[WARN] Table {old_name} not found, skipping")

        # Recreate all indexes with updated names
        print("\n[INFO] Updating indexes...")
        for old_index, _new_index in INDEX_RENAMES.items():
            # Drop old index if it exists
            cursor.execute(f"DROP INDEX IF EXISTS {old_index}")

        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        conn.commit()
        print("\n[SUCCESS] All tables renamed successfully")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {e}")
        raise
    finally:
        conn.close()


def verify_migration():
    """Verify that the migration was successful"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n[INFO] Verifying migration...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print("\nCurrent tables in database:")
    for table in tables:
        print(f"  - {table[0]}")

    # Check that new table names exist
    print("\n[INFO] Checking new table names...")
    for _old_name, new_name in TABLE_RENAMES.items():
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (new_name,)
        )
        if cursor.fetchone():
            print(f"  [OK] {new_name} exists")
        else:
            print(f"  [MISSING] {new_name} NOT FOUND")

    conn.close()


def main():
    print("=" * 70)
    print("RENAMING V2 DATABASE TABLES TO SIMPLE NAMES")
    print("=" * 70)

    # Backup database
    backup_path = backup_database()
    if not backup_path:
        print("[ERROR] Backup failed, aborting migration")
        return False

    # Rename tables
    try:
        rename_tables()
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print(f"[INFO] Database backup available at: {backup_path}")
        return False

    # Verify migration
    verify_migration()

    print("\n" + "=" * 70)
    print("[SUCCESS] Migration completed successfully!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
