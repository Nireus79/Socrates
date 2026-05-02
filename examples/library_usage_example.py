"""
Complete example of using SocratesAgentClient as a library.

This demonstrates how to use Socrates agents without any knowledge
of Socrates internals or dependencies.
"""

import asyncio
from socratic_system.api.client import SocratesAgentClient, SocratesAgentClientSync


async def async_example():
    """Example using async client."""
    print("=== Async Client Example ===\n")

    # Initialize client (no Socrates imports needed!)
    client = SocratesAgentClient(
        api_url="http://localhost:8000",
        auth_token="demo-token"
    )

    user_id = "user_demo_async"

    try:
        # 1. Create a new project
        print("1. Creating project...")
        project_response = await client.project_manager({
            "action": "create",
            "name": "Mobile App for Restaurant Reservations",
            "description": "A mobile-first app for making restaurant reservations",
            "user_id": user_id
        })

        if project_response.get("status") == "success":
            project = project_response.get("data", {})
            project_id = project.get("project_id") or project.get("id")
            print(f"   Created project: {project_id}")
        else:
            print(f"   Error: {project_response.get('message')}")
            return

        # 2. Ask Socratic questions
        print("\n2. Asking Socratic questions...")
        for i in range(3):
            q_response = await client.socratic_counselor({
                "action": "get_question",
                "project_id": project_id,
                "phase": "discovery",
                "user_id": user_id
            })

            if q_response.get("status") == "success":
                question_data = q_response.get("data", {})
                question_text = question_data.get("question", "")
                print(f"\n   Question {i+1}: {question_text}")

                # Simulate user response
                sample_response = "This is our project's approach to this question."
                print(f"   User response: {sample_response}")

                # Process the response
                resp_response = await client.socratic_counselor({
                    "action": "process_response",
                    "project_id": project_id,
                    "response": sample_response,
                    "user_id": user_id
                })

                if resp_response.get("status") == "success":
                    print(f"   Response processed successfully")

                    # Poll for analysis results
                    print("   Waiting for analysis...")
                    for attempt in range(5):
                        await asyncio.sleep(0.5)
                        analysis = await client.socratic_counselor({
                            "action": "get_analysis",
                            "project_id": project_id,
                            "user_id": user_id
                        })

                        if analysis.get("status") == "success":
                            analysis_data = analysis.get("data", {})
                            if analysis_data.get("ready"):
                                maturity = analysis_data.get("maturity", 0)
                                print(f"   Quality maturity: {maturity:.1f}%")
                                break
                else:
                    print(f"   Error processing response: {resp_response.get('message')}")
            else:
                print(f"   Error getting question: {q_response.get('message')}")

        # 3. Get quality metrics
        print("\n3. Checking quality metrics...")
        quality = await client.quality_controller({
            "action": "get_phase_maturity",
            "project_id": project_id,
            "user_id": user_id
        })

        if quality.get("status") == "success":
            quality_data = quality.get("data", {})
            print(f"   Overall maturity: {quality_data.get('overall_maturity', 0):.1f}%")
            print(f"   Phase scores: {quality_data.get('phase_maturity_scores', {})}")
        else:
            print(f"   Error: {quality.get('message')}")

        # 4. Generate code
        print("\n4. Generating code...")
        code = await client.code_generator({
            "action": "generate",
            "project_id": project_id,
            "language": "python",
            "user_id": user_id
        })

        if code.get("status") == "success":
            code_data = code.get("data", {})
            num_files = len(code_data.get("files", []))
            print(f"   Generated {num_files} files")
            for file_info in code_data.get("files", [])[:3]:
                print(f"   - {file_info.get('path', 'unknown')}")
        else:
            print(f"   Error: {code.get('message')}")

        # 5. Validate code
        print("\n5. Validating code...")
        validation = await client.code_validation({
            "action": "run_tests",
            "project_id": project_id,
            "user_id": user_id
        })

        if validation.get("status") == "success":
            val_data = validation.get("data", {})
            print(f"   Tests passed: {val_data.get('passed', 0)}/{val_data.get('total', 0)}")
        else:
            print(f"   Error: {validation.get('message')}")

        # 6. Detect conflicts
        print("\n6. Checking for conflicts...")
        conflicts = await client.conflict_detector({
            "action": "detect_conflicts",
            "project_id": project_id,
            "user_id": user_id
        })

        if conflicts.get("status") == "success":
            conflicts_data = conflicts.get("data", {})
            num_conflicts = len(conflicts_data.get("conflicts", []))
            print(f"   Found {num_conflicts} conflicts")
        else:
            print(f"   Error: {conflicts.get('message')}")

    except Exception as e:
        print(f"Error in async example: {e}")
    finally:
        await client.aclose()


def sync_example():
    """Example using synchronous client."""
    print("\n\n=== Sync Client Example ===\n")

    # Initialize synchronous client
    client = SocratesAgentClientSync(
        api_url="http://localhost:8000",
        auth_token="demo-token"
    )

    user_id = "user_demo_sync"

    try:
        # Create project
        print("1. Creating project...")
        project_response = client.project_manager({
            "action": "create",
            "name": "E-Commerce Platform",
            "description": "Full-featured online store",
            "user_id": user_id
        })

        if project_response.get("status") == "success":
            project = project_response.get("data", {})
            project_id = project.get("project_id") or project.get("id")
            print(f"   Created project: {project_id}")

            # Get a question
            print("\n2. Getting Socratic question...")
            q_response = client.socratic_counselor({
                "action": "get_question",
                "project_id": project_id,
                "phase": "discovery",
                "user_id": user_id
            })

            if q_response.get("status") == "success":
                question = q_response.get("data", {}).get("question", "")
                print(f"   Question: {question}")

            # Get quality metrics
            print("\n3. Getting quality metrics...")
            quality = client.quality_controller({
                "action": "get_phase_maturity",
                "project_id": project_id,
                "user_id": user_id
            })

            if quality.get("status") == "success":
                maturity = quality.get("data", {}).get("overall_maturity", 0)
                print(f"   Overall maturity: {maturity:.1f}%")

        else:
            print(f"   Error: {project_response.get('message')}")

    except Exception as e:
        print(f"Error in sync example: {e}")


def main():
    """Run examples."""
    print("SocratesAgentClient Library Usage Examples")
    print("=" * 50)

    # Run async example
    try:
        asyncio.run(async_example())
    except Exception as e:
        print(f"Async example failed: {e}")

    # Run sync example
    try:
        sync_example()
    except Exception as e:
        print(f"Sync example failed: {e}")

    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()
