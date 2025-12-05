"""
Socrates CLI - Command-line interface entry point

Provides a user-friendly command-line interface to the Socrates AI library.
Uses Click for command-line argument parsing and colorama for colored output.
"""

import sys
import logging
from pathlib import Path

import click
from colorama import Fore, Style, init

import socrates

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("socrates_cli")


@click.group()
@click.version_option(version="8.0.0", prog_name="socrates")
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
        # Test the configuration
        config = socrates.ConfigBuilder(api_key)
        if data_dir:
            config = config.with_data_dir(Path(data_dir))
        config = config.build()

        orchestrator = socrates.create_orchestrator(config)
        orchestrator.claude_client.test_connection()

        click.echo(f"{Fore.GREEN}✓ Socrates initialized successfully!{Style.RESET_ALL}")
        click.echo(f"  Data directory: {config.data_dir}")
        click.echo(f"  Model: {config.claude_model}")

    except socrates.APIError as e:
        click.echo(f"{Fore.RED}✗ API Error: {e.message}{Style.RESET_ALL}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}", err=True)
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
        config = socrates.SocratesConfig.from_env()
        orchestrator = socrates.create_orchestrator(config)

        result = orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": name,
                "owner": owner,
                "description": description,
            },
        )

        if result.get("status") == "success":
            project = result.get("project")
            click.echo(f"{Fore.GREEN}✓ Project created successfully!{Style.RESET_ALL}")
            click.echo(f"  Project ID: {project.project_id}")
            click.echo(f"  Name: {project.name}")
            click.echo(f"  Phase: {project.phase}")
        else:
            click.echo(
                f"{Fore.RED}✗ Failed to create project: {result.get('message')}{Style.RESET_ALL}",
                err=True,
            )
            sys.exit(1)

    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


@project.command("list")
@click.option("--owner", default=None, help="Filter by project owner")
def project_list(owner):
    """List projects."""
    try:
        config = socrates.SocratesConfig.from_env()
        orchestrator = socrates.create_orchestrator(config)

        result = orchestrator.process_request(
            "project_manager", {"action": "list_projects", "owner": owner}
        )

        projects = result.get("projects", [])

        if not projects:
            click.echo(f"{Fore.YELLOW}No projects found{Style.RESET_ALL}")
            return

        click.echo(
            f"{Fore.CYAN}{'ID':<8} {'Name':<20} {'Phase':<12} {'Owner':<15}{Style.RESET_ALL}"
        )
        click.echo("-" * 55)

        for project in projects:
            click.echo(
                f"{project['project_id']:<8} {project['name']:<20} {project['phase']:<12} {project['owner']:<15}"
            )

    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}", err=True)
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
        config = socrates.SocratesConfig.from_env()
        orchestrator = socrates.create_orchestrator(config)

        # Load the project
        project_result = orchestrator.process_request(
            "project_manager", {"action": "load_project", "project_id": project_id}
        )

        if project_result.get("status") != "success":
            click.echo(f"{Fore.RED}✗ Project not found{Style.RESET_ALL}", err=True)
            sys.exit(1)

        project = project_result["project"]

        # Generate code
        click.echo(f"{Fore.CYAN}Generating code for project '{project.name}'...{Style.RESET_ALL}")

        code_result = orchestrator.process_request(
            "code_generator", {"action": "generate_code", "project": project}
        )

        script = code_result.get("script", "")
        lines = len(script.split("\n"))

        click.echo(f"{Fore.GREEN}✓ Code generated successfully!{Style.RESET_ALL}")
        click.echo(f"  Lines of code: {lines}")
        click.echo("")
        click.echo(f"{Fore.CYAN}--- Generated Code ---{Style.RESET_ALL}")
        click.echo(script)

    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}", err=True)
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
        config = socrates.SocratesConfig.from_env()
        orchestrator = socrates.create_orchestrator(config)

        click.echo(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}Socrates AI System Information{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'=' * 50}{Style.RESET_ALL}")
        click.echo("")
        click.echo(f"Library Version: {socrates.__version__}")
        click.echo(f"Claude Model: {orchestrator.config.claude_model}")
        click.echo(f"Data Directory: {orchestrator.config.data_dir}")
        click.echo(f"Embedding Model: {orchestrator.config.embedding_model}")
        click.echo(f"Log Level: {log_level}")
        click.echo("")

        # Test API connection
        try:
            orchestrator.claude_client.test_connection()
            click.echo(f"{Fore.GREEN}✓ Claude API Connection: OK{Style.RESET_ALL}")
        except Exception:
            click.echo(f"{Fore.RED}✗ Claude API Connection: FAILED{Style.RESET_ALL}")

        click.echo("")

    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
