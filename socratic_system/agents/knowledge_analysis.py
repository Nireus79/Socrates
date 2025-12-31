"""
Knowledge Analysis Agent for dynamic knowledge-based question regeneration

When new knowledge is imported (PDFs, code repos, web pages, notes), this agent:
1. Analyzes the imported knowledge
2. Identifies gaps and new learning opportunities
3. Triggers question regeneration to adapt the Socratic dialogue
4. Emits events for UI updates
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from socratic_system.agents.base import Agent
from socratic_system.events import EventType

if TYPE_CHECKING:
    from socratic_system.orchestration.orchestrator import AgentOrchestrator


class KnowledgeAnalysisAgent(Agent):
    """
    Analyzes imported knowledge and triggers adaptive question regeneration.

    When documents are imported, this agent:
    - Extracts key concepts from the imported knowledge
    - Analyzes relevance to current project goals
    - Identifies gaps the new knowledge fills
    - Triggers regeneration of upcoming questions
    - Emits QUESTIONS_REGENERATED events
    """

    def __init__(self, orchestrator: "AgentOrchestrator"):
        """
        Initialize Knowledge Analysis Agent.

        Args:
            orchestrator: Reference to the orchestrator
        """
        super().__init__("KnowledgeAnalysis", orchestrator)
        self.logger = logging.getLogger("socrates.agents.knowledge_analysis")

        # Register for document import events
        self.orchestrator.event_emitter.on(
            EventType.DOCUMENT_IMPORTED, self._handle_document_imported
        )

        self.logger.info("Knowledge Analysis Agent initialized")

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process knowledge analysis requests.

        Args:
            request: Request dictionary with action and parameters

        Returns:
            Response dictionary with status and analysis results
        """
        action = request.get("action")

        if action == "analyze_knowledge":
            return self._analyze_knowledge(request)
        elif action == "regenerate_questions":
            return self._regenerate_questions(request)
        elif action == "get_knowledge_gaps":
            return self._get_knowledge_gaps(request)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_document_imported(self, data: Dict[str, Any]) -> None:
        """
        Handle document import events and trigger question regeneration.

        Args:
            data: Event data containing document import details
        """
        try:
            project_id = data.get("project_id")
            document_name = data.get("file_name", "unknown")
            source_type = data.get("source_type", "unknown")
            words_extracted = data.get("words_extracted", 0)

            self.logger.info(
                f"Document imported: {document_name} ({source_type}), "
                f"{words_extracted} words, project: {project_id}"
            )

            # Only proceed if we have a project ID
            if not project_id:
                self.logger.debug("No project_id in document import event, skipping analysis")
                return

            # Trigger analysis and question regeneration
            analysis_result = self._analyze_knowledge(
                {
                    "action": "analyze_knowledge",
                    "project_id": project_id,
                    "document_name": document_name,
                    "source_type": source_type,
                    "words_extracted": words_extracted,
                }
            )

            if analysis_result.get("status") == "success":
                # Trigger question regeneration
                regen_result = self._regenerate_questions(
                    {
                        "action": "regenerate_questions",
                        "project_id": project_id,
                        "knowledge_analysis": analysis_result.get("analysis"),
                    }
                )

                if regen_result.get("status") == "success":
                    self.logger.info(
                        f"Questions regenerated for project {project_id} "
                        f"after importing {document_name}"
                    )
                    # Emit event for UI updates
                    self.emit_event(
                        EventType.QUESTIONS_REGENERATED,
                        {
                            "project_id": project_id,
                            "document": document_name,
                            "new_focus_areas": regen_result.get("new_focus_areas", []),
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

        except Exception as e:
            self.logger.error(f"Error handling document import: {str(e)}", exc_info=True)

    def _analyze_knowledge(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze imported knowledge in context of project goals.

        Args:
            request: Analysis request with project_id and document details

        Returns:
            Analysis results with key concepts and gaps
        """
        try:
            project_id = request.get("project_id")
            document_name = request.get("document_name")
            source_type = request.get("source_type", "unknown")

            if not project_id:
                return {"status": "error", "message": "project_id is required"}

            # Load project context
            project = self.orchestrator.database.load_project(project_id)
            if not project:
                return {"status": "error", "message": f"Project not found: {project_id}"}

            self.logger.debug(f"Analyzing knowledge for project: {project.name}")

            # Search for the newly imported document in vector database
            search_results = self.orchestrator.vector_db.search_similar(
                query=f"{document_name} {source_type}",
                project_id=project_id,
                limit=1,
                strategy="full",
            )

            # Analyze the knowledge content
            analysis = {
                "document": document_name,
                "source_type": source_type,
                "project_phase": project.phase,
                "key_concepts": self._extract_key_concepts(search_results),
                "relevance_to_goals": self._assess_relevance(project, search_results),
                "gaps_filled": self._identify_gaps(project, search_results),
                "suggested_focus_areas": self._suggest_focus_areas(project, search_results),
                "timestamp": datetime.now().isoformat(),
            }

            self.logger.info(
                f"Knowledge analysis complete for {document_name}: "
                f"{len(analysis['key_concepts'])} concepts, "
                f"gaps in {len(analysis['gaps_filled'])} areas"
            )

            return {
                "status": "success",
                "analysis": analysis,
                "message": f"Analyzed {document_name} in context of project goals",
            }

        except Exception as e:
            self.logger.error(f"Error analyzing knowledge: {str(e)}")
            return {"status": "error", "message": f"Analysis failed: {str(e)}"}

    def _regenerate_questions(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Regenerate questions based on new knowledge analysis.

        Args:
            request: Regeneration request with project_id and knowledge_analysis

        Returns:
            Updated question plan with new focus areas
        """
        try:
            project_id = request.get("project_id")
            knowledge_analysis = request.get("knowledge_analysis", {})

            if not project_id:
                return {"status": "error", "message": "project_id is required"}

            # Load project
            project = self.orchestrator.database.load_project(project_id)
            if not project:
                return {"status": "error", "message": f"Project not found: {project_id}"}

            self.logger.debug(f"Regenerating questions for project: {project.name}")

            # Get new focus areas from analysis
            new_focus_areas = knowledge_analysis.get("suggested_focus_areas", [])
            gaps_filled = knowledge_analysis.get("gaps_filled", [])

            # Extract insight from the newly available knowledge

            # Extract insights from the knowledge to inform question generation
            insight_result = self.orchestrator.counselor.process(
                {
                    "action": "extract_insights_only",
                    "project": project,
                    "knowledge_context": knowledge_analysis,
                }
            )

            # Log the knowledge-aware question regeneration
            self.logger.info(
                f"Question regeneration triggered for {project.name} "
                f"with {len(new_focus_areas)} new focus areas and "
                f"{len(gaps_filled)} filled knowledge gaps"
            )

            return {
                "status": "success",
                "message": f"Questions regenerated for {len(new_focus_areas)} new focus areas",
                "new_focus_areas": new_focus_areas,
                "knowledge_gaps_addressed": gaps_filled,
                "insights": insight_result.get("insights", []) if insight_result else [],
            }

        except Exception as e:
            self.logger.error(f"Error regenerating questions: {str(e)}")
            return {"status": "error", "message": f"Regeneration failed: {str(e)}"}

    def _get_knowledge_gaps(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify knowledge gaps for a project.

        Args:
            request: Request with project_id

        Returns:
            List of identified knowledge gaps
        """
        try:
            project_id = request.get("project_id")
            if not project_id:
                return {"status": "error", "message": "project_id is required"}

            project = self.orchestrator.database.load_project(project_id)
            if not project:
                return {"status": "error", "message": f"Project not found: {project_id}"}

            # Analyze project goals and current knowledge
            gaps = self._identify_gaps(project, [])

            return {
                "status": "success",
                "project_id": project_id,
                "phase": project.phase,
                "knowledge_gaps": gaps,
                "count": len(gaps),
            }

        except Exception as e:
            self.logger.error(f"Error identifying knowledge gaps: {str(e)}")
            return {"status": "error", "message": f"Gap analysis failed: {str(e)}"}

    def _extract_key_concepts(self, search_results: list) -> list:
        """
        Extract key concepts from knowledge search results.

        Args:
            search_results: Results from vector database search

        Returns:
            List of identified key concepts
        """
        concepts = []
        if not search_results:
            return concepts

        try:
            # Extract concepts from document metadata and content
            for result in search_results[:3]:  # Top 3 results
                metadata = result.get("metadata", {})
                content = result.get("content", "")

                # Extract source and structure info
                source = metadata.get("source", "")
                if source:
                    concepts.append(source.replace(".pdf", "").replace(".py", ""))

                # Extract code structure if available
                if "Code Structure" in content:
                    structure_part = content.split("Code Structure:")[1].split("]")[0]
                    concepts.extend([s.strip() for s in structure_part.split(",") if s.strip()])

            return list(set(concepts))[:5]  # Return unique concepts, max 5

        except Exception as e:
            self.logger.debug(f"Error extracting concepts: {e}")
            return concepts

    def _assess_relevance(self, project, search_results: list) -> str:
        """
        Assess relevance of new knowledge to project goals.

        Args:
            project: Project context
            search_results: Knowledge search results

        Returns:
            Relevance assessment (high, medium, low)
        """
        if not search_results:
            return "medium"

        try:
            # Simple relevance check based on search score
            # In a full implementation, this would use semantic similarity
            avg_score = sum(r.get("score", 0.5) for r in search_results) / len(search_results)

            if avg_score > 0.7:
                return "high"
            elif avg_score > 0.4:
                return "medium"
            else:
                return "low"

        except Exception:
            return "medium"

    def _identify_gaps(self, project, search_results: list) -> list:
        """
        Identify knowledge gaps based on project goals.

        Args:
            project: Project context
            search_results: Knowledge search results

        Returns:
            List of identified gaps
        """
        gaps = []

        try:
            # Check for missing areas based on project requirements
            if project.goals:
                {str(g).lower().split() for g in project.goals}
            else:
                pass

            # Common knowledge areas to check
            common_areas = {
                "architecture": "System design and structure",
                "testing": "Testing and QA strategies",
                "deployment": "Deployment and DevOps",
                "documentation": "Code and API documentation",
                "security": "Security and authentication",
                "performance": "Performance optimization",
            }

            # Identify which areas are not covered
            covered_areas = set()
            if search_results:
                for result in search_results:
                    content = result.get("content", "").lower()
                    for area in common_areas:
                        if area in content:
                            covered_areas.add(area)

            # Gaps are areas mentioned in goals but not in knowledge
            for area, description in common_areas.items():
                if area not in covered_areas:
                    gaps.append({"area": area, "description": description})

            return gaps[:3]  # Return top 3 gaps

        except Exception as e:
            self.logger.debug(f"Error identifying gaps: {e}")
            return gaps

    def _suggest_focus_areas(self, project, search_results: list) -> list:
        """
        Suggest question focus areas based on new knowledge.

        Args:
            project: Project context
            search_results: Knowledge search results

        Returns:
            List of suggested focus areas
        """
        focus_areas = []

        try:
            # Identify focus areas based on document content and project phase
            phase = project.phase

            if search_results:
                # Extract focus from document content
                for result in search_results[:2]:
                    result.get("content", "")
                    source = result.get("metadata", {}).get("source", "")

                    # Create phase-specific focus areas
                    if phase == "discovery":
                        focus_areas.append(f"How does {source} align with your vision?")
                        focus_areas.append(f"What specific features from {source} do you need?")
                    elif phase == "analysis":
                        focus_areas.append(f"What challenges from {source} apply to your project?")
                        focus_areas.append(f"How will {source} influence your architecture?")
                    elif phase == "design":
                        focus_areas.append(f"How will you implement concepts from {source}?")
                        focus_areas.append(f"What design patterns does {source} suggest?")
                    elif phase == "implementation":
                        focus_areas.append(f"How does {source} guide your implementation?")
                        focus_areas.append(f"What testing strategies from {source} will you use?")

            # Ensure we have focus areas even without search results
            if not focus_areas:
                focus_areas = [
                    "How can you apply the new knowledge to your current phase?",
                    "What new considerations does this knowledge bring?",
                ]

            return focus_areas[:3]  # Return top 3 focus areas

        except Exception as e:
            self.logger.debug(f"Error suggesting focus areas: {e}")
            return []

    def emit_event(self, event_type, data: Dict[str, Any]) -> None:
        """
        Emit an event to the event system.

        Args:
            event_type: Type of event to emit
            data: Event data
        """
        try:
            self.orchestrator.event_emitter.emit(event_type, data)
        except Exception as e:
            self.logger.debug(f"Error emitting event: {e}")
