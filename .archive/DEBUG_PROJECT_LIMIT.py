#!/usr/bin/env python3
"""
Debug script to verify project limit enforcement
"""

from socratic_system.database import ProjectDatabase
from socratic_system.subscription.storage import StorageQuotaManager

def debug_user_projects(username: str):
    """Debug project count for a user"""
    db = ProjectDatabase()

    print(f"\n{'='*60}")
    print(f"DEBUGGING PROJECT LIMITS FOR: {username}")
    print(f"{'='*60}\n")

    # Load user
    user = db.load_user(username)
    if not user:
        print(f"❌ User not found: {username}")
        return

    print(f"✓ User found")
    print(f"  Subscription Tier: {user.subscription_tier}")
    print(f"  Testing Mode: {user.testing_mode}")
    print(f"  Subscription Status: {user.subscription_status}")

    # Get all projects
    all_projects = db.get_user_projects(username)
    print(f"\n✓ Total projects retrieved: {len(all_projects)}")

    # Separate owned vs collaborated
    owned_projects = []
    collab_projects = []

    for proj in all_projects:
        if proj.owner == username:
            owned_projects.append(proj)
        else:
            collab_projects.append(proj)

    print(f"\n  OWNED PROJECTS: {len(owned_projects)}")
    for proj in owned_projects:
        print(f"    - {proj.project_id}: {proj.name} (owner: {proj.owner})")

    print(f"\n  COLLABORATED PROJECTS: {len(collab_projects)}")
    for proj in collab_projects:
        print(f"    - {proj.project_id}: {proj.name} (owner: {proj.owner})")

    # Check limit
    from socratic_system.subscription.checker import SubscriptionChecker

    can_create, error_msg = SubscriptionChecker.check_project_limit(
        user, len(owned_projects)
    )

    print(f"\n{'='*60}")
    print(f"LIMIT CHECK RESULT:")
    print(f"{'='*60}")
    print(f"Can create new project: {can_create}")
    if error_msg:
        print(f"Error message:\n{error_msg}")

    # Check tier limits
    from socratic_system.subscription.tiers import get_tier_limits
    limits = get_tier_limits(user.subscription_tier)
    print(f"\nTier Limits:")
    print(f"  Tier: {limits.name}")
    print(f"  Max Projects: {limits.max_projects}")
    print(f"  Max Team Members: {limits.max_team_members}")

    print(f"\nComparison:")
    print(f"  Owned projects: {len(owned_projects)}")
    print(f"  Max allowed: {limits.max_projects}")
    print(f"  Can add more: {len(owned_projects) < limits.max_projects}")

    # Check middleware version too
    from socrates_api.middleware.subscription import SubscriptionChecker as ApiSubscriptionChecker

    can_create_api, error_api = ApiSubscriptionChecker.can_create_projects(
        user.subscription_tier, len(owned_projects)
    )

    print(f"\nAPI Middleware Check:")
    print(f"  Can create: {can_create_api}")
    if error_api:
        print(f"  Error: {error_api}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python DEBUG_PROJECT_LIMIT.py <username>")
        sys.exit(1)

    debug_user_projects(sys.argv[1])
