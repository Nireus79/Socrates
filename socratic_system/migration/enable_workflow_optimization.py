"""
Migration script to enable workflow optimization for specific projects.

Usage:
    python enable_workflow_optimization.py --project-id <project_id> [--all]
    python enable_workflow_optimization.py --all  # Enable for all projects

Options:
    --project-id    Enable optimization for specific project
    --all          Enable optimization for all projects
    --disable      Disable optimization (opposite of enable)
    --status       Show current optimization status for projects
"""

import argparse
import logging
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def enable_workflow_optimization_for_project(
    database,
    project_id: str,
    enable: bool = True,
) -> bool:
    """
    Enable or disable workflow optimization for a project.

    Args:
        database: Database instance
        project_id: Project ID to update
        enable: True to enable, False to disable

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load project
        project = database.load_project(project_id)
        if not project:
            logger.error(f"Project not found: {project_id}")
            return False

        # Get current status
        old_status = project.metadata.get("use_workflow_optimization", False)

        # Update metadata
        if project.metadata is None:
            project.metadata = {}

        project.metadata["use_workflow_optimization"] = enable

        # Save project
        database.save_project(project)

        action = "enabled" if enable else "disabled"
        logger.info(f"Workflow optimization {action} for project: {project.name} ({project_id})")
        logger.debug(f"  Previous status: {old_status}, New status: {enable}")

        return True

    except Exception as e:
        logger.error(f"Error updating project {project_id}: {e}")
        return False


def enable_workflow_optimization_for_all_projects(
    database,
    enable: bool = True,
) -> tuple:
    """
    Enable or disable workflow optimization for all projects.

    Args:
        database: Database instance
        enable: True to enable, False to disable

    Returns:
        Tuple of (successful_count, failed_count, total_count)
    """
    try:
        # Load all projects
        logger.info("Loading all projects from database...")
        all_projects = database.load_all_projects()

        if not all_projects:
            logger.warning("No projects found in database")
            return 0, 0, 0

        logger.info(f"Found {len(all_projects)} projects")

        successful = 0
        failed = 0

        for project in all_projects:
            if enable_workflow_optimization_for_project(database, project.project_id, enable):
                successful += 1
            else:
                failed += 1

        action = "enabled" if enable else "disabled"
        logger.info(
            f"\nMigration complete: Workflow optimization {action} for {successful} "
            f"projects ({failed} failed)"
        )

        return successful, failed, len(all_projects)

    except Exception as e:
        logger.error(f"Error during bulk migration: {e}")
        return 0, 0, 0


def show_optimization_status(database, project_id: Optional[str] = None) -> None:
    """
    Show workflow optimization status for project(s).

    Args:
        database: Database instance
        project_id: Optional specific project ID to check
    """
    try:
        if project_id:
            # Show status for specific project
            project = database.load_project(project_id)
            if not project:
                logger.error(f"Project not found: {project_id}")
                return

            status = project.metadata.get("use_workflow_optimization", False)
            logger.info(f"Project: {project.name} ({project_id})")
            logger.info(f"  Workflow optimization: {'ENABLED' if status else 'DISABLED'}")

        else:
            # Show status for all projects
            all_projects = database.load_all_projects()
            if not all_projects:
                logger.warning("No projects found in database")
                return

            logger.info(f"\nWorkflow Optimization Status ({len(all_projects)} projects):\n")

            enabled_count = 0
            disabled_count = 0

            for project in all_projects:
                status = project.metadata.get("use_workflow_optimization", False)
                status_str = "✓ ENABLED" if status else "✗ DISABLED"
                logger.info(f"  {project.name:<40} {status_str:<15} ({project.project_id})")

                if status:
                    enabled_count += 1
                else:
                    disabled_count += 1

            logger.info(f"\nSummary: {enabled_count} enabled, {disabled_count} disabled")

    except Exception as e:
        logger.error(f"Error showing status: {e}")


def main():
    """Main migration script entry point"""
    parser = argparse.ArgumentParser(
        description="Enable or disable workflow optimization for projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enable for specific project
  python enable_workflow_optimization.py --project-id abc123

  # Enable for all projects
  python enable_workflow_optimization.py --all

  # Disable for specific project
  python enable_workflow_optimization.py --project-id abc123 --disable

  # Show current status
  python enable_workflow_optimization.py --status
  python enable_workflow_optimization.py --status --project-id abc123
        """,
    )

    parser.add_argument(
        "--project-id",
        type=str,
        help="Project ID to update",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all projects",
    )

    parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable optimization (opposite of enable)",
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current optimization status",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.status:
        # Status check doesn't require database connection setup
        logger.info("Status check mode")
    elif not args.project_id and not args.all:
        parser.print_help()
        logger.error("Please specify --project-id, --all, or --status")
        return 1

    try:
        # Initialize database
        from socratic_system.database import Database

        logger.debug("Initializing database connection...")
        database = Database()

        if args.status:
            # Show status
            show_optimization_status(database, args.project_id)

        elif args.project_id:
            # Update specific project
            enable = not args.disable
            if enable_workflow_optimization_for_project(database, args.project_id, enable):
                logger.info("✓ Successfully updated project")
                return 0
            else:
                logger.error("✗ Failed to update project")
                return 1

        elif args.all:
            # Update all projects
            enable = not args.disable
            successful, failed, total = enable_workflow_optimization_for_all_projects(
                database, enable
            )

            if failed == 0:
                logger.info(f"✓ Successfully updated all {total} projects")
                return 0
            else:
                logger.warning(f"⚠ Partial update: {successful} succeeded, {failed} failed")
                return 1

    except ImportError as e:
        logger.error(f"Failed to import database module: {e}")
        logger.error("Make sure you're running this script from the project root")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
