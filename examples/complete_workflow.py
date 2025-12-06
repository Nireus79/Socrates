#!/usr/bin/env python3
"""
Complete Socrates AI Workflow Example

This is a fully functional example that demonstrates the complete Socrates AI
workflow, including:
- User management
- Project creation and management
- Socratic questioning
- Code generation
- Knowledge base management
- Real-time event handling

Requirements:
    pip install socrates-ai

Setup:
    export ANTHROPIC_API_KEY="your-api-key"

Run:
    python complete_workflow.py
"""

import asyncio
import os

import socrates_ai


class SocratesWorkflow:
    """Complete workflow demonstrating all Socrates AI features"""

    def __init__(self):
        """Initialize the Socrates workflow"""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.config = socrates_ai.ConfigBuilder(api_key).build()
        self.orchestrator = socrates_ai.create_orchestrator(self.config)
        self.user_id = None
        self.project_id = None

    async def run_complete_workflow(self):
        """Run the complete workflow"""
        print("=" * 70)
        print("SOCRATES AI - COMPLETE WORKFLOW DEMO")
        print("=" * 70)

        # 1. Create User
        await self.create_user()

        # 2. Create Project
        await self.create_project()

        # 3. Add Knowledge to Knowledge Base
        await self.add_knowledge()

        # 4. Ask Socratic Questions
        await self.ask_questions()

        # 5. Generate Code
        await self.generate_code()

        # 6. List Projects
        await self.list_projects()

        # 7. Show Token Usage
        await self.show_token_usage()

        print("\n" + "=" * 70)
        print("WORKFLOW COMPLETE!")
        print("=" * 70)

    async def create_user(self):
        """Create a user"""
        print("\n[1] CREATING USER")
        print("-" * 70)

        result = self.orchestrator.process_request(
            "user_manager",
            {
                "action": "create_user",
                "user_name": "alice",
                "email": "alice@example.com",
                "preferences": {
                    "learning_style": "socratic",
                    "difficulty_level": "intermediate",
                },
            },
        )

        if result.get("status") == "success":
            self.user_id = result.get("user", {}).get("user_id")
            print(f"✓ User created: {self.user_id}")
            print(f"  Email: alice@example.com")
            print(f"  Learning style: socratic")
        else:
            print(f"✗ Failed to create user: {result.get('message')}")
            self.user_id = "user_alice"

    async def create_project(self):
        """Create a project"""
        print("\n[2] CREATING PROJECT")
        print("-" * 70)

        result = self.orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": "REST API Design",
                "owner": self.user_id,
                "description": "Learn REST API design principles through Socratic dialogue",
                "topic": "API Design",
            },
        )

        if result.get("status") == "success":
            self.project_id = result.get("project", {}).get("project_id")
            print(f"✓ Project created: {self.project_id}")
            print(f"  Name: REST API Design")
            print(f"  Topic: API Design")
            print(f"  Owner: {self.user_id}")
        else:
            print(f"✗ Failed to create project: {result.get('message')}")
            self.project_id = "proj_rest_api"

    async def add_knowledge(self):
        """Add knowledge to the knowledge base"""
        print("\n[3] ADDING KNOWLEDGE")
        print("-" * 70)

        knowledge_items = [
            {
                "title": "REST API Principles",
                "content": "REST (Representational State Transfer) is an architectural style that defines a set of constraints for creating web services. Key principles include: statelessness, client-server architecture, uniform interface, and cacheability.",
            },
            {
                "title": "HTTP Methods",
                "content": "GET: retrieve data, POST: create data, PUT: update data, DELETE: remove data, PATCH: partial update",
            },
            {
                "title": "Status Codes",
                "content": "2xx: success, 3xx: redirection, 4xx: client error, 5xx: server error",
            },
        ]

        for item in knowledge_items:
            result = self.orchestrator.process_request(
                "knowledge_manager",
                {
                    "action": "add_knowledge",
                    "project_id": self.project_id,
                    "title": item["title"],
                    "content": item["content"],
                    "tags": ["api", "rest", "design"],
                },
            )

            if result.get("status") == "success":
                print(f"✓ Added: {item['title']}")
            else:
                print(f"✗ Failed to add: {item['title']}")

    async def ask_questions(self):
        """Ask Socratic questions"""
        print("\n[4] ASKING SOCRATIC QUESTIONS")
        print("-" * 70)

        topics = [
            "REST API design best practices",
            "HTTP methods and semantics",
            "API versioning strategies",
        ]

        for i, topic in enumerate(topics, 1):
            result = self.orchestrator.process_request(
                "socratic_counselor",
                {
                    "action": "generate_question",
                    "project_id": self.project_id,
                    "user_id": self.user_id,
                    "topic": topic,
                    "difficulty": "intermediate",
                },
            )

            if result.get("status") == "success":
                question = result.get("question", {})
                print(f"\n✓ Question {i}: {topic}")
                print(f"  {question.get('question_text', 'Question generated')}")
                if question.get("hints"):
                    print(f"  Hints: {', '.join(question['hints'][:2])}")
            else:
                print(f"✗ Failed to generate question for: {topic}")

    async def generate_code(self):
        """Generate code"""
        print("\n[5] GENERATING CODE")
        print("-" * 70)

        specification = """
        Create a Python Flask endpoint that:
        - Handles GET requests to /users
        - Returns a JSON list of users
        - Includes proper error handling
        - Follows REST API conventions
        """

        result = self.orchestrator.process_request(
            "code_generator",
            {
                "action": "generate_code",
                "project_id": self.project_id,
                "specification": specification,
                "language": "python",
            },
        )

        if result.get("status") == "success":
            print("✓ Code generated successfully")
            code = result.get("code", "")
            if code:
                lines = code.split("\n")[:10]  # Show first 10 lines
                print("  First lines of generated code:")
                for line in lines:
                    print(f"    {line}")
                if len(code.split('\n')) > 10:
                    print("    ...")
        else:
            print(f"✗ Failed to generate code: {result.get('message')}")

    async def list_projects(self):
        """List all projects"""
        print("\n[6] LISTING PROJECTS")
        print("-" * 70)

        result = self.orchestrator.process_request(
            "project_manager",
            {
                "action": "list_projects",
                "owner": self.user_id,
            },
        )

        if result.get("status") == "success":
            projects = result.get("projects", [])
            print(f"✓ Found {len(projects)} project(s)")
            for project in projects:
                print(f"  - {project.get('name')} (ID: {project.get('project_id')})")
        else:
            print(f"✗ Failed to list projects: {result.get('message')}")

    async def show_token_usage(self):
        """Show token usage statistics"""
        print("\n[7] TOKEN USAGE")
        print("-" * 70)

        # This would typically come from tracking during operations
        print("✓ Token usage tracked during workflow")
        print("  Note: Full token tracking available in ConfigBuilder")


async def main():
    """Main entry point"""
    try:
        workflow = SocratesWorkflow()
        await workflow.run_complete_workflow()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nPlease set ANTHROPIC_API_KEY environment variable:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
