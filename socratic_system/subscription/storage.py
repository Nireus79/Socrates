"""Storage quota management and tracking."""

from typing import Optional, Tuple
from socratic_system.subscription.tiers import get_tier_limits
from socratic_system.models.user import User


class StorageQuotaManager:
    """Manages storage quotas and tracking for subscription tiers."""

    @staticmethod
    def get_storage_limit_gb(tier: str) -> Optional[float]:
        """
        Get storage limit in GB for a tier.

        Args:
            tier: Subscription tier (free, pro, enterprise)

        Returns:
            Storage limit in GB, or None for unlimited
        """
        limits = get_tier_limits(tier)
        # Storage limits are now centralized in TIER_LIMITS.storage_gb
        # Free: 5GB, Pro: 100GB, Enterprise: None (unlimited)
        return float(limits.storage_gb) if limits.storage_gb is not None else None

    @staticmethod
    def bytes_to_gb(bytes_size: int) -> float:
        """Convert bytes to gigabytes."""
        return bytes_size / (1024 ** 3)

    @staticmethod
    def gb_to_bytes(gb_size: float) -> int:
        """Convert gigabytes to bytes."""
        return int(gb_size * (1024 ** 3))

    @staticmethod
    def can_upload_document(
        user: User,
        database,
        document_size_bytes: int,
        testing_mode: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user can upload a document based on storage quota.

        Args:
            user: User object with subscription tier
            database: Database connection to calculate current storage usage
            document_size_bytes: Size of document to upload in bytes
            testing_mode: Whether testing mode is enabled (bypasses check)

        Returns:
            (can_upload: bool, error_message: Optional[str])
        """
        # Testing mode bypasses storage checks
        if user and user.testing_mode or testing_mode:
            return True, None

        if user is None:
            return False, "User not found"

        # Get user's tier and storage limit
        tier = user.subscription_tier.lower()
        limit_gb = StorageQuotaManager.get_storage_limit_gb(tier)

        # Unlimited storage for enterprise
        if limit_gb is None:
            return True, None

        # Calculate current storage usage
        current_usage_bytes = StorageQuotaManager.calculate_user_storage_usage(
            user.username, database
        )
        current_usage_gb = StorageQuotaManager.bytes_to_gb(current_usage_bytes)
        document_size_gb = StorageQuotaManager.bytes_to_gb(document_size_bytes)

        # Check if adding this document would exceed the limit
        new_total_gb = current_usage_gb + document_size_gb

        if new_total_gb > limit_gb:
            remaining_gb = limit_gb - current_usage_gb
            return (
                False,
                f"Storage quota exceeded. Current: {current_usage_gb:.2f}GB/{limit_gb:.2f}GB. "
                f"This document ({document_size_gb:.2f}GB) would exceed limit. "
                f"Remaining: {max(0, remaining_gb):.2f}GB",
            )

        return True, None

    @staticmethod
    def calculate_user_storage_usage(username: str, database) -> int:
        """
        Calculate total storage usage for a user across all projects in bytes.

        Args:
            username: Username
            database: Database connection

        Returns:
            Total storage usage in bytes
        """
        try:
            # Get all knowledge documents for user
            documents = database.get_user_knowledge_documents(username)

            if not documents:
                return 0

            total_bytes = 0
            for doc in documents:
                # Get file_size from document, default to content length if not available
                if isinstance(doc, dict):
                    file_size = doc.get("file_size", 0)
                    if file_size == 0 and "content" in doc:
                        # Estimate size from content if file_size not available
                        file_size = len(doc["content"].encode("utf-8"))
                else:
                    # Handle object attributes
                    file_size = getattr(doc, "file_size", 0)
                    if file_size == 0 and hasattr(doc, "content"):
                        file_size = len(doc.content.encode("utf-8"))

                total_bytes += file_size

            return total_bytes
        except Exception as e:
            # Log error but don't fail - assume 0 if error
            print(f"Error calculating storage usage for {username}: {e}")
            return 0

    @staticmethod
    def get_storage_usage_report(username: str, database) -> dict:
        """
        Get detailed storage usage report for a user.

        Args:
            username: Username
            database: Database connection

        Returns:
            Dict with storage usage details
        """
        try:
            user = database.load_user(username)
            if not user:
                return {"error": "User not found"}

            tier = user.subscription_tier.lower()
            limit_gb = StorageQuotaManager.get_storage_limit_gb(tier)
            used_bytes = StorageQuotaManager.calculate_user_storage_usage(
                username, database
            )
            used_gb = StorageQuotaManager.bytes_to_gb(used_bytes)

            report = {
                "username": username,
                "tier": tier,
                "storage_used_gb": round(used_gb, 2),
                "storage_used_bytes": used_bytes,
                "storage_limit_gb": limit_gb if limit_gb else None,
                "storage_limit_bytes": (
                    StorageQuotaManager.gb_to_bytes(limit_gb) if limit_gb else None
                ),
                "storage_limit_unlimited": limit_gb is None,
            }

            if limit_gb:
                report["storage_percentage_used"] = round(
                    (used_gb / limit_gb) * 100, 2
                )
                report["storage_remaining_gb"] = round(max(0, limit_gb - used_gb), 2)
            else:
                report["storage_percentage_used"] = 0
                report["storage_remaining_gb"] = None

            return report
        except Exception as e:
            return {"error": f"Failed to generate report: {str(e)}"}
