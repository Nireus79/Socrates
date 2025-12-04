"""Direct query and answer commands - bypass Socratic mode for direct answers"""

from typing import Dict, Any, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class AskCommand(BaseCommand):
    """Ask a direct question and get an answer (not Socratic questioning)"""

    def __init__(self):
        super().__init__(
            name="ask",
            description="Ask a direct question and get an answer from the system",
            usage="ask <your question>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ask command"""
        if not self.validate_args(args, min_count=1):
            question = input(f"{Fore.WHITE}What would you like to know? ").strip()
        else:
            question = ' '.join(args)

        if not question:
            return self.error("Please provide a question")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator:
            return self.error("Orchestrator not available")

        print(f"\n{Fore.CYAN}Searching knowledge base...{Style.RESET_ALL}")

        try:
            # Get relevant knowledge from vector database
            relevant_context = ""
            if orchestrator.vector_db:
                knowledge_results = orchestrator.vector_db.search_similar(question, top_k=3)
                if knowledge_results:
                    relevant_context = "\n".join([
                        f"- {result.get('content', '')[:200]}..."
                        for result in knowledge_results
                    ])

            # Build prompt for direct answer
            prompt = self._build_answer_prompt(question, project, relevant_context)

            # Get direct answer from Claude
            answer = orchestrator.claude_client.generate_response(prompt)

            # Display answer
            print(f"\n{Fore.GREEN}Answer:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{answer}{Style.RESET_ALL}\n")

            # Optionally show sources
            if relevant_context:
                print(f"{Fore.CYAN}[Based on project knowledge]{Style.RESET_ALL}\n")

            return self.success(data={
                'question': question,
                'answer': answer,
                'has_context': bool(relevant_context)
            })

        except Exception as e:
            return self.error(f"Failed to get answer: {str(e)}")

    def _build_answer_prompt(self, question: str, project, context: str) -> str:
        """Build prompt for direct answer generation"""
        project_info = ""
        if project:
            project_info = f"""
Project Context:
- Name: {project.name}
- Phase: {project.phase}
- Goals: {project.goals}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
"""

        relevant_knowledge = ""
        if context:
            relevant_knowledge = f"""
Relevant Knowledge:
{context}
"""

        return f"""You are a helpful assistant for a software development project.

{project_info}

{relevant_knowledge}

User Question: {question}

Provide a clear, direct answer to the user's question. Be concise but thorough.
If the question relates to the project, use the project context and knowledge base.
If you don't have enough information, say so."""


class ExplainCommand(BaseCommand):
    """Get an explanation of a concept or topic"""

    def __init__(self):
        super().__init__(
            name="explain",
            description="Get an explanation of a concept or topic in detail",
            usage="explain <topic>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute explain command"""
        if not self.validate_args(args, min_count=1):
            topic = input(f"{Fore.WHITE}What would you like explained? ").strip()
        else:
            topic = ' '.join(args)

        if not topic:
            return self.error("Please provide a topic")

        orchestrator = context.get('orchestrator')
        project = context.get('project')

        if not orchestrator:
            return self.error("Orchestrator not available")

        print(f"\n{Fore.CYAN}Generating explanation...{Style.RESET_ALL}")

        try:
            # Get relevant knowledge from vector database
            relevant_context = ""
            if orchestrator.vector_db:
                knowledge_results = orchestrator.vector_db.search_similar(topic, top_k=5)
                if knowledge_results:
                    relevant_context = "\n".join([
                        f"- {result.get('content', '')[:200]}..."
                        for result in knowledge_results
                    ])

            # Build prompt for explanation
            prompt = self._build_explanation_prompt(topic, project, relevant_context)

            # Get explanation from Claude
            explanation = orchestrator.claude_client.generate_response(prompt)

            # Display explanation
            print(f"\n{Fore.GREEN}{topic}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-' * len(topic)}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{explanation}{Style.RESET_ALL}\n")

            return self.success(data={
                'topic': topic,
                'explanation': explanation,
                'has_context': bool(relevant_context)
            })

        except Exception as e:
            return self.error(f"Failed to generate explanation: {str(e)}")

    def _build_explanation_prompt(self, topic: str, project, context: str) -> str:
        """Build prompt for explanation generation"""
        project_info = ""
        if project:
            project_info = f"""
Project Context:
- Name: {project.name}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
"""

        relevant_knowledge = ""
        if context:
            relevant_knowledge = f"""
Related Information:
{context}
"""

        return f"""You are a technical educator explaining concepts clearly and thoroughly.

{project_info}

{relevant_knowledge}

Topic to Explain: {topic}

Provide a comprehensive explanation that:
1. Defines the concept clearly
2. Explains why it's important
3. Gives practical examples
4. Relates to the project context if applicable

Make it understandable but detailed."""


class SearchCommand(BaseCommand):
    """Search project knowledge base for information"""

    def __init__(self):
        super().__init__(
            name="search",
            description="Search the project knowledge base for information",
            usage="search <keywords>"
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search command"""
        if not self.validate_args(args, min_count=1):
            query = input(f"{Fore.WHITE}What would you like to search for? ").strip()
        else:
            query = ' '.join(args)

        if not query:
            return self.error("Please provide search terms")

        orchestrator = context.get('orchestrator')

        if not orchestrator or not orchestrator.vector_db:
            return self.error("Knowledge base not available")

        print(f"\n{Fore.CYAN}Searching knowledge base...{Style.RESET_ALL}")

        try:
            # Search vector database
            results = orchestrator.vector_db.search_similar(query, top_k=5)

            if not results:
                self.print_info("No matching knowledge found")
                return self.success(data={'query': query, 'results': []})

            # Display results
            print(f"\n{Fore.GREEN}Search Results for '{query}':{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-' * 50}{Style.RESET_ALL}")

            for i, result in enumerate(results, 1):
                content = result.get('content', '')
                source = result.get('metadata', {}).get('source', 'Unknown source')

                # Truncate long content
                if len(content) > 200:
                    content = content[:200] + "..."

                print(f"\n{Fore.YELLOW}[{i}] {source}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{content}{Style.RESET_ALL}")

            print()

            return self.success(data={
                'query': query,
                'results': len(results),
                'results_data': results
            })

        except Exception as e:
            return self.error(f"Search failed: {str(e)}")
