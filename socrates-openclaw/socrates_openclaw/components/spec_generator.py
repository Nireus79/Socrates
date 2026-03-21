class SpecificationGenerator:
    def __init__(self, socratic_agent: SocraticAgent):
        self.agent = socratic_agent

    def generate_spec(self, topic: str, session: Dict) -> Dict:
        """Generate complete specification"""
        context = self._format_context(session)

        # Generate using socrates-ai agent
        spec = self._generate_with_agent(topic, context)

        # Create structured output
        output = {
            "topic": topic,
            "spec": spec,
            "requirements": self._extract_requirements(spec),
            "architecture": self._extract_architecture(spec),
            "artifacts": {
                "PROJECT.md": spec,
                "REQUIREMENTS.md": self._generate_requirements(session),
                "ARCHITECTURE.md": self._generate_architecture(session)
            }
        }

        return output

    def _generate_with_agent(self, topic: str, context: str) -> str:
        """Use socrates-ai to synthesize spec"""
        try:
            spec = self.agent.synthesize_specification(
                topic=topic,
                context=context,
                knowledge_base=self.knowledge_base
            )
            return spec
        except Exception as e:
            # Fallback to template-based generation
            return self._generate_fallback_spec(topic, context)

    def _format_context(self, session: Dict) -> str:
        """Format session Q&A as context"""
        lines = [f"Topic: {session['topic']}\n"]
        for q, r in zip(session["questions"], session["responses"]):
            lines.append(f"Q: {q}\nA: {r}\n")
        return "\n".join(lines)

    def _generate_requirements(self, session: Dict) -> str:
        """Extract functional requirements"""
        # Parse responses for requirements
        requirements = "# Functional Requirements\n\n"
        for resp in session.get("responses", []):
            if "feature" in resp.lower() or "requirement" in resp.lower():
                requirements += f"- {resp}\n"
        return requirements if requirements != "# Functional Requirements\n\n" else "# Functional Requirements\n\n- TBD"

    def _generate_architecture(self, session: Dict) -> str:
        """Extract architectural insights"""
        return "# Architecture\n\n- Recommended: Modular design\n- Storage: Cloud-based\n- Scaling: Horizontal"

    def _generate_fallback_spec(self, topic: str, context: str) -> str:
        """Fallback spec template if synthesis fails"""
        spec = f"# {topic}\n\n"
        spec += "## Overview\n" + context + "\n\n"
        spec += "## Next Steps\n"
        spec += "- [ ] Validate requirements\n"
        spec += "- [ ] Design architecture\n"
        spec += "- [ ] Create technical spec\n"
        return spec
