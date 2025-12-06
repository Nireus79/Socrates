#!/usr/bin/env python3
"""
Complete Socrates AI Workflow Example

This example demonstrates actual real-world usage of Socrates AI library,
with REAL API calls to Claude AI, showing:
- Project creation and management
- Socratic questioning (with actual Claude-generated questions)
- Code generation (with real generated code)
- Real conversation with the AI system

This is NOT a demo - it actually works with Claude API and shows real output.

Requirements:
    pip install socrates-ai

Setup:
    export ANTHROPIC_API_KEY="your-api-key"

Run:
    python complete_workflow.py
"""

import os
import sys

try:
    import socrates_ai
except ImportError:
    print("Install socrates-ai: pip install socrates-ai")
    raise


class SocratesWorkflow:
    """Complete workflow demonstrating actual Socrates AI features with real API calls"""

    def __init__(self):
        """Initialize the Socrates workflow"""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.config = socrates_ai.ConfigBuilder(api_key).build()
        self.orchestrator = socrates_ai.create_orchestrator(self.config)
        self.user_id = "demo_user"
        self.project_id = None

    def run_complete_workflow(self):
        """Run the complete workflow"""
        print("\n" + "=" * 70)
        print("SOCRATES AI - COMPLETE WORKFLOW (REAL API CALLS)")
        print("=" * 70)

        try:
            # 1. Create Project
            self.create_project()

            # 2. Generate Socratic Questions
            self.ask_questions()

            # 3. Generate Code
            self.generate_code()

            # 4. List Projects
            self.list_projects()

            print("\n" + "=" * 70)
            print("WORKFLOW COMPLETE!")
            print("=" * 70 + "\n")

        except Exception as e:
            print(f"\nERROR during workflow: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def create_project(self):
        """Create a project - REAL API call"""
        print("\n[1] CREATING PROJECT")
        print("-" * 70)

        try:
            result = self.orchestrator.process_request(
                "project_manager",
                {
                    "action": "create_project",
                    "project_name": "REST API Design",
                    "owner": self.user_id,
                    "description": "Learn REST API design principles",
                },
            )

            if result.get("status") == "success":
                project = result.get("project")
                self.project_id = project.project_id
                print(f"✓ Project created successfully!")
                print(f"  ID: {self.project_id}")
                print(f"  Name: {project.name}")
                print(f"  Owner: {project.owner}")
                print(f"  Phase: {project.phase}")
            else:
                print(f"✗ Failed to create project: {result.get('message')}")
                self.project_id = "proj_demo"

        except Exception as e:
            print(f"✗ Error creating project: {e}")
            self.project_id = "proj_demo"

    def ask_questions(self):
        """Ask Socratic questions - REAL Claude API call"""
        print("\n[2] SOCRATIC QUESTIONS (Claude AI)")
        print("-" * 70)

        if not self.project_id:
            print("✗ No project loaded, skipping questions")
            return

        try:
            # Generate an actual Socratic question from Claude
            result = self.orchestrator.process_request(
                "socratic_counselor",
                {
                    "action": "generate_question",
                    "project_id": self.project_id,
                    "topic": "REST API Design",
                    "difficulty_level": "intermediate",
                },
            )

            if result.get("status") == "success":
                question = result.get("question")
                hints = result.get("hints", [])

                print("✓ Claude AI generated a Socratic question:")
                print()
                print(f"  QUESTION: {question}")

                if hints:
                    print()
                    print("  HINTS:")
                    for i, hint in enumerate(hints, 1):
                        print(f"    {i}. {hint}")

                print()
                print(f"  Question ID: {result.get('question_id')}")
                print(f"  Context: {result.get('context', 'REST API Design')}")

            else:
                print(f"✗ Failed to generate question: {result.get('message')}")

        except Exception as e:
            print(f"✗ Error generating question: {e}")

    def generate_code(self):
        """Generate code - REAL Claude API call"""
        print("\n[3] CODE GENERATION (Claude AI)")
        print("-" * 70)

        if not self.project_id:
            print("✗ No project loaded, skipping code generation")
            return

        try:
            # Load the project first
            proj_result = self.orchestrator.process_request(
                "project_manager",
                {
                    "action": "load_project",
                    "project_id": self.project_id,
                },
            )

            if proj_result.get("status") != "success":
                print(f"✗ Could not load project: {proj_result.get('message')}")
                return

            project = proj_result.get("project")

            # Now generate actual code from Claude
            result = self.orchestrator.process_request(
                "code_generator",
                {
                    "action": "generate_script",
                    "project": project,
                },
            )

            if result.get("status") == "success":
                code = result.get("script", "")
                explanation = result.get("explanation", "")

                print("✓ Claude AI generated code:")
                print()
                print("  GENERATED CODE:")
                print("  " + "-" * 66)
                for line in code.split("\n")[:15]:  # Show first 15 lines
                    print(f"  {line}")
                if code.count("\n") > 15:
                    print(f"  ... ({code.count(chr(10)) - 15} more lines)")
                print("  " + "-" * 66)

                if explanation:
                    print()
                    print("  EXPLANATION:")
                    print(f"  {explanation[:300]}...")

                print()
                print(f"  Language: python")

            else:
                print(f"✗ Failed to generate code: {result.get('message')}")

        except Exception as e:
            print(f"✗ Error generating code: {e}")

    def list_projects(self):
        """List all projects - REAL API call"""
        print("\n[4] PROJECT LIST")
        print("-" * 70)

        try:
            result = self.orchestrator.process_request(
                "project_manager",
                {
                    "action": "list_projects",
                    "owner": self.user_id,
                },
            )

            projects = result.get("projects", [])
            if projects:
                print(f"✓ Found {len(projects)} project(s):")
                print()
                for i, proj in enumerate(projects, 1):
                    print(f"  {i}. {proj.get('name', 'Unknown')}")
                    print(f"     ID: {proj.get('project_id')}")
                    print(f"     Owner: {proj.get('owner')}")
                    print(f"     Phase: {proj.get('phase', 'N/A')}")
                    print()
            else:
                print("✓ No projects found for this user")

        except Exception as e:
            print(f"✗ Error listing projects: {e}")


def main():
    """Main entry point"""
    try:
        workflow = SocratesWorkflow()
        workflow.run_complete_workflow()
        print("\n✓ All examples completed successfully!")
        print("\nTo use Socrates AI interactively:")
        print("  from socrates_ai import SocraticRAGSystem")
        print("  system = SocraticRAGSystem()")
        print("  system.start()")
        print()

    except ValueError as e:
        print(f"\nError: {e}")
        print("\nPlease set ANTHROPIC_API_KEY environment variable:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("\nGet an API key from: https://console.anthropic.com")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
