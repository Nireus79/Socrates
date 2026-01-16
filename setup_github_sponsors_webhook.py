#!/usr/bin/env python3
"""
Setup script to register GitHub Sponsors webhook with your repository.

This script uses your GITHUB_API_KEY to register the webhook endpoint
with GitHub so that sponsorship events are sent to your Socrates API.

Usage:
    python setup_github_sponsors_webhook.py --url http://localhost:8000 --secret <your-secret>

Or with ngrok:
    python setup_github_sponsors_webhook.py --url https://abc123.ngrok.io --secret <your-secret>
"""

import argparse
import os
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


class GitHubWebhookSetup:
    """Helper class to register webhook with GitHub."""

    def __init__(self, github_token: str, repo_owner: str = "Nireus79", repo_name: str = "Socrates"):
        """
        Initialize setup helper.

        Args:
            github_token: GitHub personal access token
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
        """
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/hooks"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_webhook(self, webhook_url: str, secret: str) -> bool:
        """
        Create a webhook for GitHub Sponsors events.

        Args:
            webhook_url: Full URL where GitHub will send webhook events
            secret: Webhook signature secret (must match GITHUB_WEBHOOK_SECRET)

        Returns:
            True if successful, False otherwise
        """
        payload = {
            "name": "web",
            "active": True,
            "events": ["sponsorship"],
            "config": {
                "url": f"{webhook_url}/sponsorships/webhooks/github-sponsors",
                "content_type": "json",
                "secret": secret,
                "insecure_ssl": "0",
            },
        }

        try:
            print(f"\n📡 Registering webhook with GitHub...")
            print(f"   Webhook URL: {payload['config']['url']}")
            print(f"   Events: {payload['events']}")

            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=10)

            if response.status_code == 201:
                webhook_data = response.json()
                webhook_id = webhook_data.get("id")
                print(f"✅ Webhook registered successfully!")
                print(f"   Webhook ID: {webhook_id}")
                print(f"   View at: https://github.com/{self.repo_owner}/{self.repo_name}/settings/hooks/{webhook_id}")
                return True
            elif response.status_code == 422:
                # Likely webhook already exists
                print("⚠️  Webhook may already exist (422 Unprocessable Entity)")
                print(f"   Check existing webhooks at: https://github.com/{self.repo_owner}/{self.repo_name}/settings/hooks")
                print(f"   Response: {response.json()}")
                return False
            else:
                print(f"❌ Failed to create webhook (HTTP {response.status_code})")
                print(f"   Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to GitHub API: {e}")
            return False

    def list_webhooks(self) -> Optional[list]:
        """
        List all webhooks for the repository.

        Returns:
            List of webhook data or None if error
        """
        try:
            print(f"\n📋 Fetching existing webhooks...")
            response = requests.get(self.api_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                webhooks = response.json()
                if not webhooks:
                    print("   No webhooks found")
                    return []

                print(f"   Found {len(webhooks)} webhook(s):")
                for hook in webhooks:
                    hook_id = hook.get("id")
                    hook_url = hook.get("config", {}).get("url", "N/A")
                    hook_events = hook.get("events", [])
                    hook_active = "✅" if hook.get("active") else "❌"
                    print(f"     {hook_active} [{hook_id}] {hook_url}")
                    print(f"        Events: {', '.join(hook_events)}")

                return webhooks
            else:
                print(f"❌ Failed to list webhooks (HTTP {response.status_code})")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to GitHub API: {e}")
            return None

    def delete_webhook(self, webhook_id: int) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: GitHub webhook ID

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n🗑️  Deleting webhook {webhook_id}...")
            response = requests.delete(f"{self.api_url}/{webhook_id}", headers=self.headers, timeout=10)

            if response.status_code == 204:
                print(f"✅ Webhook deleted successfully")
                return True
            else:
                print(f"❌ Failed to delete webhook (HTTP {response.status_code})")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to GitHub API: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Setup GitHub Sponsors webhook for Socrates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Local development with ngrok
  python setup_github_sponsors_webhook.py --url https://abc123.ngrok.io --secret <your-secret>

  # Production deployment
  python setup_github_sponsors_webhook.py --url https://api.yourdomain.com --secret <your-secret>

  # List existing webhooks
  python setup_github_sponsors_webhook.py --list

  # Delete a webhook
  python setup_github_sponsors_webhook.py --delete 12345
        """,
    )

    parser.add_argument("--url", help="Webhook URL (e.g., https://api.yourdomain.com)")
    parser.add_argument("--secret", help="Webhook secret (must match GITHUB_WEBHOOK_SECRET)")
    parser.add_argument("--list", action="store_true", help="List existing webhooks")
    parser.add_argument("--delete", type=int, help="Delete webhook by ID")
    parser.add_argument("--token", help="GitHub API token (or use GITHUB_API_KEY env var)")
    parser.add_argument("--owner", default="Nireus79", help="GitHub repo owner (default: Nireus79)")
    parser.add_argument("--repo", default="Socrates", help="GitHub repo name (default: Socrates)")

    args = parser.parse_args()

    # Get GitHub token
    github_token = args.token or os.getenv("GITHUB_API_KEY")
    if not github_token:
        print("❌ Error: GITHUB_API_KEY environment variable not set or --token not provided")
        print("   Set with: export GITHUB_API_KEY=your_token_here")
        sys.exit(1)

    # Create setup helper
    setup = GitHubWebhookSetup(github_token, args.owner, args.repo)

    # Handle different commands
    if args.list:
        setup.list_webhooks()
    elif args.delete:
        setup.delete_webhook(args.delete)
    elif args.url and args.secret:
        if setup.create_webhook(args.url, args.secret):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("❌ Error: Must provide either --url/--secret, --list, or --delete")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
