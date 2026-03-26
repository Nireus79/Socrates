"""
Socrates CLI - Complete command-line interface for Socrates AI

Provides Click-based commands that call the Socrates API server.
All commands require a running Socrates API server at SOCRATES_API_URL
(default: http://localhost:8000)
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import httpx
from colorama import Fore, Style, init

from socratic_core import ConfigBuilder, SocratesConfig

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("socrates_cli")

# Global API client
_api_client: Optional[httpx.Client] = None
_api_url: str = os.getenv("SOCRATES_API_URL", "http://localhost:8000")


def get_api_client() -> httpx.Client:
    """Get or create the API client."""
    global _api_client
    if _api_client is None:
        _api_client = httpx.Client(base_url=_api_url, timeout=30.0)
    return _api_client


def api_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    **kwargs,
) -> dict:
    """Make a request to the Socrates API."""
    try:
        client = get_api_client()
        response = client.request(method, endpoint, json=json_data, **kwargs)
        response.raise_for_status()
        return response.json() if response.text else {}
    except httpx.HTTPStatusError as e:
        error_msg = f"API Error: {e.response.status_code}"
        try:
            error_data = e.response.json()
            if "message" in error_data:
                error_msg += f" - {error_data['message']}"
        except (ValueError, KeyError):
            pass
        raise click.ClickException(error_msg)
    except httpx.RequestError as e:
        raise click.ClickException(
            f"Connection error: {e}. Is the API server running at {_api_url}?"
        )


def execute_command(command: str, args: List[str] = None, **context) -> Dict[str, Any]:
    """Execute a command via the API."""
    payload = {
        "command": command,
        "args": args or [],
    }
    payload.update(context)
    response = api_request("POST", "/commands/execute", json_data=payload)
    return response


def print_response(response: Dict[str, Any], json_output: bool = False) -> None:
    """Pretty-print an API response."""
    if json_output:
        click.echo(json.dumps(response.get("data", response), indent=2))
    else:
        status = response.get("status", "unknown")
        message = response.get("message", "")
        data = response.get("data", {})

        if status == "success":
            click.echo(f"{Fore.GREEN}✓ Success{Style.RESET_ALL}")
            if message:
                click.echo(f"  {message}")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        click.echo(f"  {key}:")
                        click.echo(f"    {json.dumps(value, indent=6)}")
                    else:
                        click.echo(f"  {key}: {value}")
            elif isinstance(data, list):
                for item in data:
                    click.echo(f"  - {item}")
            else:
                click.echo(f"  {data}")
        elif status == "error":
            click.echo(f"{Fore.RED}✗ Error{Style.RESET_ALL}")
            if message:
                click.echo(f"  {message}")
            sys.exit(1)
        else:
            click.echo(f"{Fore.YELLOW}ℹ {status.upper()}{Style.RESET_ALL}")
            if message:
                click.echo(f"  {message}")


@click.group()
@click.version_option(version="0.1.1", prog_name="socrates-cli")
@click.option("--api-url", envvar="SOCRATES_API_URL", default="http://localhost:8000",
              help="Socrates API server URL")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def main(ctx, api_url, json_output):
    """
    Socrates AI - A Socratic method tutoring system powered by Claude AI

    Connect to a running Socrates API server to manage projects, generate code,
    and track your learning progress.

    Examples:
        socrates init                      Initialize CLI configuration
        socrates project create            Create a new project
        socrates project list              List your projects
        socrates chat                      Start interactive chat
        socrates code generate             Generate code for your project
        socrates docs import PATH          Import documentation

    API Configuration:
        Set SOCRATES_API_URL to change the API server
        Default: http://localhost:8000
    """
    global _api_url
    _api_url = api_url
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json_output


# ============================================================================
# System Commands
# ============================================================================

@main.command()
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", prompt=False,
              hide_input=True, help="Claude API key")
@click.option("--data-dir", type=click.Path(), default=None,
              help="Data directory for projects")
def init(api_key, data_dir):
    """Initialize Socrates configuration."""
    if not api_key:
        api_key = click.prompt("Enter your Claude API key", hide_input=True)

    try:
        config = ConfigBuilder(api_key)
        if data_dir:
            config = config.with_data_dir(Path(data_dir))
        config = config.build()

        try:
            api_request("GET", "/health")
            click.echo(f"{Fore.GREEN}API Server: OK{Style.RESET_ALL}")
        except click.ClickException:
            click.echo(f"{Fore.YELLOW}Warning: Could not connect to API server{Style.RESET_ALL}")

        click.echo(f"{Fore.GREEN}Socrates initialized successfully!{Style.RESET_ALL}")
        click.echo(f"  Data directory: {config.data_dir}")
        click.echo(f"  Model: {config.claude_model}")
        click.echo(f"  API Server: {_api_url}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@main.command()
@click.option("--command", help="Specific command to get help for")
@click.pass_context
def help(ctx, command):
    """Show help documentation."""
    try:
        if command:
            response = api_request("GET", "/commands/help", params={"command": command})
        else:
            response = api_request("GET", "/commands/help")
        print_response(response, ctx.obj.get("json_output", False))
    except click.ClickException:
        raise


@main.command()
def info():
    """Show system information."""
    try:
        response = execute_command("info")
        print_response(response)
    except click.ClickException:
        raise


@main.command()
def status():
    """Show system status."""
    try:
        response = execute_command("status")
        print_response(response)
    except click.ClickException:
        raise


@main.command("exit")
def exit_cmd():
    """Exit the application."""
    click.echo("Goodbye!")
    sys.exit(0)


# ============================================================================
# User Commands
# ============================================================================

@main.group()
def user():
    """Manage user account."""
    pass


@user.command("login")
def user_login():
    """Login to your account."""
    try:
        response = execute_command("user login")
        print_response(response)
    except click.ClickException:
        raise


@user.command("create")
def user_create():
    """Create a new account."""
    try:
        response = execute_command("user create")
        print_response(response)
    except click.ClickException:
        raise


@user.command("logout")
def user_logout():
    """Logout from your account."""
    try:
        response = execute_command("user logout")
        print_response(response)
    except click.ClickException:
        raise


@user.command("archive")
def user_archive():
    """Archive your account."""
    try:
        response = execute_command("user archive")
        print_response(response)
    except click.ClickException:
        raise


@user.command("delete")
def user_delete():
    """Permanently delete your account."""
    if click.confirm("Are you sure? This cannot be undone."):
        try:
            response = execute_command("user delete")
            print_response(response)
        except click.ClickException:
            raise


@user.command("restore")
def user_restore():
    """Restore an archived account."""
    try:
        response = execute_command("user restore")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Subscription Commands
# ============================================================================

@main.group()
def subscription():
    """Manage subscription."""
    pass


@subscription.command("status")
def subscription_status():
    """Show subscription status and usage."""
    try:
        response = execute_command("subscription status")
        print_response(response)
    except click.ClickException:
        raise


@subscription.command("upgrade")
@click.argument("tier", required=False)
def subscription_upgrade(tier):
    """Upgrade your subscription."""
    args = [tier] if tier else []
    try:
        response = execute_command("subscription upgrade", args)
        print_response(response)
    except click.ClickException:
        raise


@subscription.command("downgrade")
@click.argument("tier", required=False)
def subscription_downgrade(tier):
    """Downgrade your subscription."""
    args = [tier] if tier else []
    try:
        response = execute_command("subscription downgrade", args)
        print_response(response)
    except click.ClickException:
        raise


@subscription.command("compare")
def subscription_compare():
    """Compare subscription tiers."""
    try:
        response = execute_command("subscription compare")
        print_response(response)
    except click.ClickException:
        raise


@subscription.command("testing-mode")
@click.argument("action", type=click.Choice(["on", "off", "status"]), default="status")
def subscription_testing_mode(action):
    """Enable/disable testing mode."""
    args = [action]
    try:
        response = execute_command("subscription testing-mode", args)
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Project Commands
# ============================================================================

@main.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.option("--name", prompt="Project name", help="Name of the project")
@click.option("--type", "project_type", help="Project type (software, business, etc.)")
@click.option("--description", default="", help="Project description")
def project_create(name, project_type, description):
    """Create a new project."""
    args = [name]
    if project_type:
        args.append(project_type)
    if description:
        args.append(description)
    try:
        response = execute_command("project create", args)
        print_response(response)
    except click.ClickException:
        raise


@project.command("list")
@click.option("--json", "json_format", is_flag=True, help="Output as JSON")
def project_list(json_format):
    """List all projects."""
    try:
        response = execute_command("project list")
        print_response(response, json_format)
    except click.ClickException:
        raise


@project.command("load")
def project_load():
    """Load an existing project."""
    try:
        response = execute_command("project load")
        print_response(response)
    except click.ClickException:
        raise


@project.command("archive")
def project_archive():
    """Archive the current project."""
    try:
        response = execute_command("project archive")
        print_response(response)
    except click.ClickException:
        raise


@project.command("restore")
def project_restore():
    """Restore an archived project."""
    try:
        response = execute_command("project restore")
        print_response(response)
    except click.ClickException:
        raise


@project.command("delete")
def project_delete():
    """Permanently delete a project."""
    if click.confirm("Are you sure? This cannot be undone."):
        try:
            response = execute_command("project delete")
            print_response(response)
        except click.ClickException:
            raise


@project.command("analyze")
@click.argument("project_id", required=False)
def project_analyze(project_id):
    """Analyze project code comprehensively."""
    args = [project_id] if project_id else []
    try:
        response = execute_command("project analyze", args)
        print_response(response)
    except click.ClickException:
        raise


@project.command("test")
@click.argument("project_id", required=False)
def project_test(project_id):
    """Run project test suite."""
    args = [project_id] if project_id else []
    try:
        response = execute_command("project test", args)
        print_response(response)
    except click.ClickException:
        raise


@project.command("validate")
@click.argument("project_id", required=False)
def project_validate(project_id):
    """Validate project structure."""
    args = [project_id] if project_id else []
    try:
        response = execute_command("project validate", args)
        print_response(response)
    except click.ClickException:
        raise


@project.command("fix")
@click.argument("issue_type", required=False, default="all",
                type=click.Choice(["all", "syntax", "dependencies"]))
def project_fix(issue_type):
    """Apply automated fixes to project."""
    args = [issue_type]
    try:
        response = execute_command("project fix", args)
        print_response(response)
    except click.ClickException:
        raise


@project.command("review")
@click.argument("project_id", required=False)
def project_review(project_id):
    """Get comprehensive code review."""
    args = [project_id] if project_id else []
    try:
        response = execute_command("project review", args)
        print_response(response)
    except click.ClickException:
        raise


@project.command("diff")
@click.argument("project_id", required=False)
def project_diff(project_id):
    """Compare validation runs."""
    args = [project_id] if project_id else []
    try:
        response = execute_command("project diff", args)
        print_response(response)
    except click.ClickException:
        raise


@project.command("status")
def project_status():
    """Show project status."""
    try:
        response = execute_command("project status")
        print_response(response)
    except click.ClickException:
        raise


@project.command("progress")
def project_progress():
    """Show project progress metrics."""
    try:
        response = execute_command("project progress")
        print_response(response)
    except click.ClickException:
        raise


@project.command("stats")
def project_stats():
    """View comprehensive project statistics."""
    try:
        response = execute_command("project stats")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Code Commands
# ============================================================================

@main.group()
def code():
    """Generate and manage code."""
    pass


@code.command("generate")
@click.argument("prompt", required=False)
@click.option("--output", "-o", type=click.Path(), help="Save to file")
def code_generate(prompt, output):
    """Generate code for your project."""
    args = [prompt] if prompt else []
    if output:
        args.append(f"--output={output}")
    try:
        response = execute_command("code generate", args)
        print_response(response)
        if output:
            click.echo(f"{Fore.GREEN}Code saved to: {output}{Style.RESET_ALL}")
    except click.ClickException:
        raise


@code.command("docs")
def code_docs():
    """Generate code documentation."""
    try:
        response = execute_command("code docs")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Documentation Commands
# ============================================================================

@main.group()
def docs():
    """Manage documentation."""
    pass


@docs.command("list")
def docs_list():
    """List imported documents."""
    try:
        response = execute_command("docs list")
        print_response(response)
    except click.ClickException:
        raise


@docs.command("import")
@click.argument("path", type=click.Path(exists=True))
def docs_import(path):
    """Import a document file."""
    args = [path]
    try:
        response = execute_command("docs import", args)
        print_response(response)
    except click.ClickException:
        raise


@docs.command("import-dir")
@click.argument("path", type=click.Path(exists=True))
def docs_import_dir(path):
    """Import a directory of documents."""
    args = [path]
    try:
        response = execute_command("docs import-dir", args)
        print_response(response)
    except click.ClickException:
        raise


@docs.command("import-url")
@click.argument("url")
def docs_import_url(url):
    """Import documentation from a URL."""
    args = [url]
    try:
        response = execute_command("docs import-url", args)
        print_response(response)
    except click.ClickException:
        raise


@docs.command("paste")
def docs_paste():
    """Paste content into knowledge base."""
    try:
        response = execute_command("docs paste")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Chat Commands
# ============================================================================

@main.command()
@click.option("--mode", type=click.Choice(["socratic", "direct"]), default="socratic",
              help="Chat mode")
def chat(mode):
    """Start interactive chat."""
    args = [mode]
    try:
        response = execute_command("chat", args)
        print_response(response)
    except click.ClickException:
        raise


@main.command()
def done():
    """Finish current session."""
    try:
        response = execute_command("done")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Collaboration Commands
# ============================================================================

@main.group()
def collab():
    """Manage collaboration."""
    pass


@collab.command("add")
@click.argument("username")
@click.argument("role", required=False, default="contributor")
def collab_add(username, role):
    """Add a collaborator to the project."""
    args = [username, role]
    try:
        response = execute_command("collab add", args)
        print_response(response)
    except click.ClickException:
        raise


@collab.command("remove")
@click.argument("username", required=False)
def collab_remove(username):
    """Remove a collaborator from the project."""
    args = [username] if username else []
    try:
        response = execute_command("collab remove", args)
        print_response(response)
    except click.ClickException:
        raise


@collab.command("list")
def collab_list():
    """List project collaborators."""
    try:
        response = execute_command("collab list")
        print_response(response)
    except click.ClickException:
        raise


@collab.command("role")
@click.argument("username")
@click.argument("role")
def collab_role(username, role):
    """Update collaborator role."""
    args = [username, role]
    try:
        response = execute_command("collab role", args)
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# GitHub Commands
# ============================================================================

@main.group()
def github():
    """Manage GitHub integration."""
    pass


@github.command("import")
@click.argument("url")
@click.argument("name", required=False)
def github_import(url, name):
    """Import a GitHub repository as a project."""
    args = [url]
    if name:
        args.append(name)
    try:
        response = execute_command("github import", args)
        print_response(response)
    except click.ClickException:
        raise


@github.command("pull")
def github_pull():
    """Pull latest changes from GitHub."""
    try:
        response = execute_command("github pull")
        print_response(response)
    except click.ClickException:
        raise


@github.command("push")
def github_push():
    """Push changes to GitHub."""
    try:
        response = execute_command("github push")
        print_response(response)
    except click.ClickException:
        raise


@github.command("sync")
def github_sync():
    """Sync with GitHub (bidirectional)."""
    try:
        response = execute_command("github sync")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Note Commands
# ============================================================================

@main.group()
def note():
    """Manage project notes."""
    pass


@note.command("add")
@click.argument("type_")
@click.argument("title")
@click.option("--category", type=click.Choice(["design", "bug", "idea", "task", "general"]),
              default="general")
def note_add(type_, title, category):
    """Add a note to the project."""
    args = [type_, title, category]
    try:
        response = execute_command("note add", args)
        print_response(response)
    except click.ClickException:
        raise


@note.command("list")
def note_list():
    """List all project notes."""
    try:
        response = execute_command("note list")
        print_response(response)
    except click.ClickException:
        raise


@note.command("search")
@click.argument("query")
def note_search(query):
    """Search notes."""
    args = [query]
    try:
        response = execute_command("note search", args)
        print_response(response)
    except click.ClickException:
        raise


@note.command("delete")
@click.argument("note_id")
def note_delete(note_id):
    """Delete a note."""
    args = [note_id]
    try:
        response = execute_command("note delete", args)
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Analytics Commands
# ============================================================================

@main.group()
def analytics():
    """View analytics and metrics."""
    pass


@analytics.command("analyze")
@click.argument("phase", required=False)
@click.option("--category", type=click.Choice(["discovery", "analysis", "design", "implementation"]))
def analytics_analyze(phase, category):
    """Analyze metrics for a phase."""
    args = []
    if phase:
        args.append(phase)
    if category:
        args.append(f"--category={category}")
    try:
        response = execute_command("analytics analyze", args)
        print_response(response)
    except click.ClickException:
        raise


@analytics.command("summary")
def analytics_summary():
    """Get analytics summary."""
    try:
        response = execute_command("analytics summary")
        print_response(response)
    except click.ClickException:
        raise


@analytics.command("trends")
def analytics_trends():
    """View progression trends."""
    try:
        response = execute_command("analytics trends")
        print_response(response)
    except click.ClickException:
        raise


@analytics.command("recommend")
def analytics_recommend():
    """Get improvement recommendations."""
    try:
        response = execute_command("analytics recommend")
        print_response(response)
    except click.ClickException:
        raise


@analytics.command("breakdown")
def analytics_breakdown():
    """Detailed metrics breakdown."""
    try:
        response = execute_command("analytics breakdown")
        print_response(response)
    except click.ClickException:
        raise


@analytics.command("status")
def analytics_status():
    """Show analytics status."""
    try:
        response = execute_command("analytics status")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Maturity Commands
# ============================================================================

@main.group()
def maturity():
    """Track project maturity."""
    pass


@maturity.command("status")
def maturity_status():
    """Show current maturity status."""
    try:
        response = execute_command("maturity status")
        print_response(response)
    except click.ClickException:
        raise


@maturity.command("summary")
def maturity_summary():
    """Get maturity summary."""
    try:
        response = execute_command("maturity summary")
        print_response(response)
    except click.ClickException:
        raise


@maturity.command("history")
def maturity_history():
    """View maturity history."""
    try:
        response = execute_command("maturity history")
        print_response(response)
    except click.ClickException:
        raise


# ============================================================================
# Utility Commands
# ============================================================================

@main.command("version")
def version_cmd():
    """Show version information."""
    click.echo("socrates-cli version 0.1.1")


if __name__ == "__main__":
    main()
