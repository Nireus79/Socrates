"""
Socrates CLI - Command-line interface for Socrates AI

Provides a user-friendly command-line interface to the Socrates AI platform.
Can operate in two modes:
1. API mode (recommended): Connects to a running Socrates API server
2. Standalone mode: Uses local orchestrator (requires socrates-ai package)

Uses Click for command-line argument parsing and colorama for colored output.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
import httpx
from colorama import Fore, Style, init

from socratic_core import SocratesConfig, ConfigBuilder

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
    method: str, endpoint: str, json_data: Optional[dict] = None, **kwargs
) -> dict:
    """
    Make a request to the Socrates API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        json_data: JSON payload for POST/PUT requests
        **kwargs: Additional httpx.Client.request arguments

    Returns:
        Response data as dictionary

    Raises:
        click.ClickException: If API request fails
    """
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


@click.group()
@click.version_option(version="1.3.3", prog_name="socrates")
@click.pass_context
def main(ctx):
    """
    Socrates AI - A Socratic method tutoring system powered by Claude AI

    Use 'socrates COMMAND --help' for more information on a command.

    Examples:
        socrates init                  Initialize a new Socrates project
        socrates project create        Create a new project
        socrates ask                   Ask a Socratic question
        socrates generate-code         Generate code for your project

    API Configuration:
        Set SOCRATES_API_URL to change the API server (default: http://localhost:8000)
    """
    ctx.ensure_object(dict)


@main.command()
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    prompt=False,
    hide_input=True,
    help="Claude API key (or set ANTHROPIC_API_KEY env var)",
)
@click.option(
    "--data-dir",
    type=click.Path(),
    default=None,
    help="Data directory for storing projects (defaults to ~/.socrates)",
)
def init(api_key, data_dir):
    """
    Initialize Socrates configuration.

    Creates necessary directories and validates your Claude API key.
    """
    if not api_key:
        api_key = click.prompt("Enter your Claude API key", hide_input=True)

    try:
        # Test the configuration locally
        config = ConfigBuilder(api_key)
        if data_dir:
            config = config.with_data_dir(Path(data_dir))
        config = config.build()

        # Test API connection
        try:
            result = api_request("GET", "/health")
            click.echo(f"{Fore.GREEN}API Server: OK{Style.RESET_ALL}")
        except click.ClickException as e:
            click.echo(f"{Fore.YELLOW}Warning: {e}{Style.RESET_ALL}")

        click.echo(f"{Fore.GREEN}Socrates initialized successfully!{Style.RESET_ALL}")
        click.echo(f"  Data directory: {config.data_dir}")
        click.echo(f"  Model: {config.claude_model}")
        click.echo(f"  API Server: {_api_url}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@main.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.option("--name", prompt="Project name", help="Name of the project")
@click.option("--owner", prompt="Owner username", help="Project owner")
@click.option("--description", default="", help="Project description")
def project_create(name, owner, description):
    """Create a new project."""
    try:
        result = api_request(
            "POST",
            "/projects",
            json_data={
                "name": name,
                "owner": owner,
                "description": description,
            },
        )

        if result.get("status") == "success":
            project = result.get("data", {})
            click.echo(f"{Fore.GREEN}Project created successfully!{Style.RESET_ALL}")
            click.echo(f"  Project ID: {project.get('project_id', 'N/A')}")
            click.echo(f"  Name: {project.get('name', 'N/A')}")
        else:
            message = result.get("message", "Unknown error")
            click.echo(
                f"{Fore.RED}Failed to create project: {message}{Style.RESET_ALL}",
                err=True,
            )
            sys.exit(1)

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@project.command("list")
@click.option("--owner", default=None, help="Filter by project owner")
def project_list(owner):
    """List projects."""
    try:
        params = {}
        if owner:
            params["owner"] = owner

        result = api_request("GET", "/projects", params=params)

        projects = result.get("data", [])

        if not projects:
            click.echo(f"{Fore.YELLOW}No projects found{Style.RESET_ALL}")
            return

        click.echo(
            f"{Fore.CYAN}{'ID':<8} {'Name':<20} {'Owner':<15}{Style.RESET_ALL}"
        )
        click.echo("-" * 43)

        for project in projects:
            click.echo(
                f"{project.get('project_id', 'N/A'):<8} {project.get('name', 'N/A'):<20} {project.get('owner', 'N/A'):<15}"
            )

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@main.group()
def code():
    """Generate and manage code."""
    pass


@code.command("generate")
@click.option("--project-id", prompt="Project ID", help="Project ID to generate code for")
def generate_code(project_id):
    """Generate code for a project."""
    try:
        # Load the project first
        result = api_request("GET", f"/projects/{project_id}")

        if not result.get("status") == "success":
            click.echo(f"{Fore.RED}Project not found{Style.RESET_ALL}", err=True)
            sys.exit(1)

        project = result.get("data", {})

        # Generate code
        click.echo(
            f"{Fore.CYAN}Generating code for project '{project.get('name')}'...{Style.RESET_ALL}"
        )

        code_result = api_request(
            "POST",
            f"/projects/{project_id}/code/generate",
            json_data={},
        )

        script = code_result.get("data", {}).get("code", "")
        lines = len(script.split("\n"))

        click.echo(f"{Fore.GREEN}Code generated successfully!{Style.RESET_ALL}")
        click.echo(f"  Lines of code: {lines}")
        click.echo("")
        click.echo(f"{Fore.CYAN}--- Generated Code ---{Style.RESET_ALL}")
        click.echo(script)

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
def info(log_level):
    """Show Socrates system information."""
    try:
        result = api_request("GET", "/info")

        click.echo(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}Socrates AI System Information{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
        click.echo("")

        info_data = result.get("data", {})
        click.echo(f"Library Version: {info_data.get('version', 'N/A')}")
        click.echo(f"Claude Model: {info_data.get('claude_model', 'N/A')}")
        click.echo(f"Data Directory: {info_data.get('data_dir', 'N/A')}")
        click.echo(f"Log Level: {log_level}")
        click.echo("")

        # Test API connection
        try:
            health = api_request("GET", "/health")
            click.echo(f"{Fore.GREEN}API Connection: OK{Style.RESET_ALL}")
        except Exception:
            click.echo(f"{Fore.RED}API Connection: FAILED{Style.RESET_ALL}")

        click.echo("")

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


def cleanup():
    """Clean up resources on exit."""
    global _api_client
    if _api_client:
        try:
            _api_client.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup()
