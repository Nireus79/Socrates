"""
Conversation Storage Consolidation Utility

Migrates from dual conversation storage (conversation_history + chat_sessions)
to unified conversation_history model.

CRITICAL FIX #3: Consolidate conversation storage to single source of truth.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def migrate_chat_sessions_to_conversation_history(project: Any) -> None:
    """
    Migrate messages from chat_sessions to conversation_history.

    Converts chat_sessions messages into conversation_history format,
    adding session metadata for tracking.

    Args:
        project: ProjectContext object to migrate
    """
    try:
        if not hasattr(project, "chat_sessions") or not project.chat_sessions:
            logger.debug("No chat_sessions to migrate")
            return

        if not hasattr(project, "conversation_history"):
            project.conversation_history = []

        initial_count = len(project.conversation_history)
        migrated_count = 0

        # Process each session in chat_sessions
        for session_id, session_data in project.chat_sessions.items():
            session_messages = session_data.get("messages", [])
            session_title = session_data.get("title", f"Session {session_id}")

            for message in session_messages:
                # Skip if message already exists (check by content and timestamp)
                msg_content = message.get("content") or message.get("message", "")
                msg_timestamp = message.get("timestamp")

                # Check for duplicates
                is_duplicate = False
                for existing_msg in project.conversation_history:
                    if (
                        existing_msg.get("content") == msg_content
                        and existing_msg.get("timestamp") == msg_timestamp
                    ):
                        is_duplicate = True
                        break

                if is_duplicate:
                    logger.debug(f"Skipping duplicate message from session {session_id}")
                    continue

                # Convert to conversation_history format
                history_entry = {
                    "role": message.get("role", "user"),
                    "content": msg_content,
                    "timestamp": msg_timestamp or datetime.now(timezone.utc).isoformat(),
                    # Preserve session metadata for tracking
                    "session_id": session_id,
                    "session_title": session_title,
                    # Preserve original message ID if present
                    "message_id": message.get("id"),
                }

                project.conversation_history.append(history_entry)
                migrated_count += 1
                logger.debug(f"Migrated message from session {session_id}")

        logger.info(
            f"Migration complete: {migrated_count} messages migrated "
            f"(total history: {initial_count} → {len(project.conversation_history)})"
        )

    except Exception as e:
        logger.error(f"Error during conversation migration: {e}", exc_info=True)
        raise


def merge_conversation_history(
    primary: List[Dict],
    secondary: List[Dict],
    dedup_key: str = "timestamp",
) -> List[Dict]:
    """
    Merge two conversation histories without duplicates.

    Args:
        primary: Primary conversation history list
        secondary: Secondary conversation history to merge
        dedup_key: Field to use for deduplication

    Returns:
        Merged conversation history without duplicates
    """
    if not primary:
        return secondary or []
    if not secondary:
        return primary or []

    merged = list(primary)
    seen_keys = {msg.get(dedup_key) for msg in primary if msg.get(dedup_key)}

    for msg in secondary:
        key = msg.get(dedup_key)
        if key and key not in seen_keys:
            merged.append(msg)
            seen_keys.add(key)
        elif not key:
            # If no dedup key, check full equality
            if msg not in merged:
                merged.append(msg)

    return merged


def validate_conversation_consolidation(project: Any) -> Dict[str, Any]:
    """
    Validate that conversation storage is properly consolidated.

    Args:
        project: ProjectContext to validate

    Returns:
        Validation report with status and issues
    """
    report = {
        "valid": True,
        "issues": [],
        "conversation_history_count": 0,
        "chat_sessions_count": 0,
        "has_duplicates": False,
    }

    # Check conversation_history
    if hasattr(project, "conversation_history") and project.conversation_history:
        report["conversation_history_count"] = len(project.conversation_history)

    # Check chat_sessions (should be empty after migration)
    if hasattr(project, "chat_sessions") and project.chat_sessions:
        report["chat_sessions_count"] = len(project.chat_sessions)
        if report["chat_sessions_count"] > 0:
            report["issues"].append("Deprecated chat_sessions still present")
            report["valid"] = False

    # Check for duplicates in conversation_history
    if report["conversation_history_count"] > 0:
        seen = set()
        for msg in project.conversation_history:
            key = (msg.get("timestamp"), msg.get("content"))
            if key in seen:
                report["has_duplicates"] = True
                report["issues"].append(f"Duplicate message found: {key}")
                report["valid"] = False
            seen.add(key)

    if report["conversation_history_count"] == 0 and report["chat_sessions_count"] == 0:
        report["issues"].append("No conversation data found")
        report["valid"] = False

    return report


# Consolidation status tracking
class ConsolidationTracker:
    """Track consolidation progress across migrations."""

    def __init__(self):
        self.projects_processed = 0
        self.messages_migrated = 0
        self.duplicates_skipped = 0
        self.errors = []

    def record_migration(self, project_id: str, migrated: int, skipped: int):
        """Record migration results for a project."""
        self.projects_processed += 1
        self.messages_migrated += migrated
        self.duplicates_skipped += skipped

    def record_error(self, project_id: str, error: str):
        """Record an error during migration."""
        self.errors.append({"project_id": project_id, "error": error})

    def get_summary(self) -> Dict[str, Any]:
        """Get consolidation summary."""
        return {
            "projects_processed": self.projects_processed,
            "messages_migrated": self.messages_migrated,
            "duplicates_skipped": self.duplicates_skipped,
            "errors": len(self.errors),
            "error_details": self.errors if self.errors else None,
        }
