"""
Socratic counselor agent for guided questioning and response processing
"""

import datetime
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from colorama import Fore

from socratic_system.agents.document_context_analyzer import DocumentContextAnalyzer
from socratic_system.events import EventType
from socratic_system.models import ROLE_FOCUS_AREAS, ConflictInfo, ProjectContext
from socratic_system.services import DocumentUnderstandingService

from .base import Agent

if TYPE_CHECKING:
    from socratic_system.orchestration import AgentOrchestrator


class SocraticCounselorAgent(Agent):
    """Core agent that guides users through Socratic questioning about their project"""

    def __init__(self, orchestrator: "AgentOrchestrator") -> None:
        super().__init__("SocraticCounselor", orchestrator)
        self.use_dynamic_questions = True  # Toggle for dynamic vs static questions
        self.max_questions_per_phase = 5
        self.phase_docs_cache = {}  # Cache document context per phase to reduce vector DB calls

        # Fallback static questions if Claude is unavailable
        self.static_questions = {
            "discovery": [
                "What specific problem does your project solve?",
                "Who is your target audience or user base?",
                "What are the core features you envision?",
                "Are there similar solutions that exist? How will yours differ?",
                "What are your success criteria for this project?",
            ],
            "analysis": [
                "What technical challenges do you anticipate?",
                "What are your performance requirements?",
                "How will you handle user authentication and security?",
                "What third-party integrations might you need?",
                "How will you test and validate your solution?",
            ],
            "design": [
                "How will you structure your application architecture?",
                "What design patterns will you use?",
                "How will you organize your code and modules?",
                "What development workflow will you follow?",
                "How will you handle error cases and edge scenarios?",
            ],
            "implementation": [
                "What will be your first implementation milestone?",
                "How will you handle deployment and DevOps?",
                "What monitoring and logging will you implement?",
                "How will you document your code and API?",
                "What's your plan for maintenance and updates?",
            ],
        }

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process Socratic questioning requests"""
        action = request.get("action")

        if action == "generate_question":
            return self._generate_question(request)
        elif action == "process_response":
            return self._process_response(request)
        elif action == "extract_insights_only":
            return self._extract_insights_only(request)
        elif action == "advance_phase":
            return self._advance_phase(request)
        elif action == "explain_document":
            return self._explain_document(request)
        elif action == "generate_hint":
            return self._generate_hint(request)
        elif action == "toggle_dynamic_questions":
            self.use_dynamic_questions = not self.use_dynamic_questions
            return {"status": "success", "dynamic_mode": self.use_dynamic_questions}
        elif action == "answer_question":
            return self._answer_question(request)
        elif action == "skip_question":
            return self._skip_question(request)
        elif action == "reopen_question":
            return self._reopen_question(request)
        elif action == "generate_answer_suggestions":
            return self._generate_answer_suggestions(request)

        return {"status": "error", "message": "Unknown action"}

    def _generate_question(self, request: Dict) -> Dict:
        """Generate the next Socratic question with usage tracking"""
        project = request.get("project")
        current_user = request.get("current_user")  # NEW: Accept current user for role context

        # Validate that project exists
        if not project:
            return {
                "status": "error",
                "message": "Project context is required to generate questions",
            }

        import datetime

        # HYBRID APPROACH: Check for existing unanswered question before generating new one
        # This prevents double question generation
        if project.pending_questions:
            unanswered = [q for q in project.pending_questions if q.get("status") == "unanswered"]
            if unanswered:
                # Return the first unanswered question instead of generating new
                return {"status": "success", "question": unanswered[0].get("question"), "existing": True}

        context = self.orchestrator.context_analyzer.get_context_summary(project)

        # NEW: Check question limit
        from socratic_system.subscription.checker import SubscriptionChecker

        # Get or create user (auto-create for CLI/local users)
        user = self.orchestrator.database.load_user(current_user)
        if user is None:
            # Auto-create user with pro tier for local/CLI use
            from socratic_system.models.user import User

            user = User(
                username=current_user,
                email=f"{current_user}@localhost",
                passcode_hash="",
                created_at=datetime.datetime.now(),
                projects=[],
                subscription_tier="pro",  # Unlimited for local use
            )
            self.orchestrator.database.save_user(user)
            logging.debug(f"Auto-created user: {current_user}")

        can_ask, error_message = SubscriptionChecker.check_question_limit(user)
        if not can_ask:
            return {
                "status": "error",
                "message": error_message,
            }

        # Count questions already asked in this phase
        phase_questions = [
            msg
            for msg in project.conversation_history
            if msg.get("type") == "assistant" and msg.get("phase") == project.phase
        ]

        if self.use_dynamic_questions:
            question = self._generate_dynamic_question(
                project, context, len(phase_questions), current_user
            )
        else:
            question = self._generate_static_question(project, len(phase_questions))

        # Store the question in conversation history
        project.conversation_history.append(
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "assistant",
                "content": question,
                "phase": project.phase,
                "question_number": len(phase_questions) + 1,
            }
        )

        # HYBRID APPROACH: Also store in pending_questions for unified tracking
        import uuid
        project.pending_questions.append(
            {
                "id": f"q_{uuid.uuid4().hex[:8]}",
                "question": question,
                "phase": project.phase,
                "status": "unanswered",
                "created_at": datetime.datetime.now().isoformat(),
                "answer": None,
                "skipped_at": None,
                "answered_at": None,
            }
        )

        # NEW: Increment usage counter
        user.increment_question_usage()
        self.orchestrator.database.save_user(user)

        return {"status": "success", "question": question}

    def _generate_dynamic_question(
        self, project: ProjectContext, context: str, question_count: int, current_user: str = None
    ) -> str:
        """Generate contextual questions using Claude with role-aware context"""
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")

        # Get conversation history for context
        recent_conversation = ""
        previously_asked_questions = []
        if project.conversation_history:
            recent_messages = project.conversation_history[-4:]  # Last 4 messages
            for msg in recent_messages:
                role = "Assistant" if msg["type"] == "assistant" else "User"
                recent_conversation += f"{role}: {msg['content']}\n"
            logger.debug(f"Using {len(recent_messages)} recent messages for context")

            # Extract ALL previously asked questions in this phase to avoid repeats
            for msg in project.conversation_history:
                if msg.get("type") == "assistant" and msg.get("phase") == project.phase:
                    previously_asked_questions.append(msg.get("content", ""))
            logger.debug(f"Found {len(previously_asked_questions)} previously asked questions in {project.phase} phase")

        # Get relevant knowledge from vector database with adaptive loading strategy
        # OPTIMIZATION: Cache document results per phase to reduce vector DB calls
        relevant_knowledge = ""
        knowledge_results = []
        doc_understanding = None
        strategy = "snippet"  # Default strategy
        if context:
            logger.debug("Analyzing question context for adaptive document loading...")

            # Check if we have cached results for this phase
            phase_key = f"{project.project_id}:{project.phase}"
            if phase_key in self.phase_docs_cache:
                logger.debug(f"Using cached document results for {project.phase} phase")
                cache_data = self.phase_docs_cache[phase_key]
                knowledge_results = cache_data.get("results", [])
                strategy = cache_data.get("strategy", "snippet")
            else:
                # Use DocumentContextAnalyzer to determine loading strategy
                doc_analyzer = DocumentContextAnalyzer()

                # Convert project context to dict format for analyzer
                project_context_dict = {"current_phase": project.phase, "goals": project.goals or ""}

                # Determine loading strategy based on conversation context
                strategy = doc_analyzer.analyze_question_context(
                    project_context=project_context_dict,
                    conversation_history=project.conversation_history,
                    question_count=question_count,
                )

                logger.debug(f"Using '{strategy}' document loading strategy")

                # Get top_k based on strategy
                top_k = 5 if strategy == "full" else 3

                # Use adaptive search
                knowledge_results = self.orchestrator.vector_db.search_similar_adaptive(
                    query=context, strategy=strategy, top_k=top_k, project_id=project.project_id
                )

                # Cache the results for this phase
                self.phase_docs_cache[phase_key] = {
                    "results": knowledge_results,
                    "strategy": strategy
                }
                logger.debug(f"Cached document results for {project.phase} phase")

            if knowledge_results:
                # Build knowledge context based on strategy
                if strategy == "full":
                    relevant_knowledge = self._build_full_knowledge_context(knowledge_results)
                else:
                    relevant_knowledge = self._build_snippet_knowledge_context(knowledge_results)

                # Generate document understanding if we have document results
                doc_understanding = self._generate_document_understanding(
                    knowledge_results, project
                )

                logger.debug(
                    f"Found {len(knowledge_results)} relevant knowledge items with strategy '{strategy}'"
                )

        logger.debug(
            f"Building question prompt for {project.phase} phase (question #{question_count + 1})"
        )
        prompt = self._build_question_prompt(
            project,
            context,
            recent_conversation,
            relevant_knowledge,
            question_count,
            current_user,
            knowledge_results=knowledge_results if knowledge_results else [],
            doc_understanding=doc_understanding if "doc_understanding" in locals() else None,
            previously_asked_questions=previously_asked_questions,
        )

        try:
            logger.info(f"Generating dynamic question for {project.phase} phase")

            # Generate cache key based on project context to avoid redundant Claude calls
            # Cache key includes project ID, phase, and question number to ensure variety
            cache_key = f"{project.project_id}:{project.phase}:{question_count}"

            question = self.orchestrator.claude_client.generate_socratic_question(
                prompt, cache_key=cache_key
            )
            logger.debug(f"Question generated successfully: {question[:100]}...")
            self.log(f"Generated dynamic question for {project.phase} phase")
            return question
        except Exception as e:
            logger.warning(f"Failed to generate dynamic question: {e}, falling back to static")
            self.log(f"Failed to generate dynamic question: {e}, falling back to static", "WARN")
            return self._generate_static_question(project, question_count)

    def _build_question_prompt(
        self,
        project: ProjectContext,
        context: str,
        recent_conversation: str,
        relevant_knowledge: str,
        question_count: int,
        current_user: str = None,
        knowledge_results: List[Dict] = None,
        doc_understanding: Optional[Dict[str, Any]] = None,
        previously_asked_questions: List[str] = None,
    ) -> str:
        """Build prompt for dynamic question generation with role-aware context"""
        if knowledge_results is None:
            knowledge_results = []
        if doc_understanding is None:
            doc_understanding = {}
        if previously_asked_questions is None:
            previously_asked_questions = []

        phase_descriptions = {
            "discovery": "exploring the problem space, understanding user needs, and defining project goals",
            "analysis": "analyzing technical requirements, identifying challenges, and planning solutions",
            "design": "designing architecture, choosing patterns, and planning implementation structure",
            "implementation": "planning development steps, deployment strategy, and maintenance approach",
        }

        phase_focus = {
            "discovery": "problem definition, user needs, market research, competitive analysis",
            "analysis": "technical feasibility, performance requirements, security considerations, integrations",
            "design": "architecture patterns, code organization, development workflow, error handling",
            "implementation": "development milestones, deployment pipeline, monitoring, documentation",
        }

        # NEW: Get role-aware context if user is provided
        role_context = ""
        if current_user:
            user_role = project.get_member_role(current_user) or "lead"
            role_focus = ROLE_FOCUS_AREAS.get(user_role, "general project aspects")
            is_solo = project.is_solo_project()

            if not is_solo:
                role_context = f"""

User Role Context:
- Current User: {current_user}
- Role: {user_role.upper()}
- Role Focus Areas: {role_focus}

As a {user_role}, this person should focus on: {role_focus}
Tailor your question to their role and expertise. For example:
- For 'lead': Ask about vision, strategy, goals, and resource allocation
- For 'creator': Ask about implementation details, execution, and deliverables
- For 'specialist': Ask about technical/domain depth, best practices, quality standards
- For 'analyst': Ask about research, requirements, validation, and critical assessment
- For 'coordinator': Ask about timelines, dependencies, process management, and coordination"""

        # NEW: Check if documents include code files
        code_context = ""
        has_code = any(
            result.get("metadata", {}).get("type") == "code"
            or "code_structure" in str(result.get("metadata", {})).lower()
            for result in knowledge_results
        )

        if has_code:
            code_context = """

Code Analysis Context:
Since the knowledge base includes code or code structure, consider these code-specific questions:
- Ask about design patterns and architectural choices in the code
- Explore separation of concerns and code organization
- Discuss error handling and edge cases
- Question the trade-offs in implementation decisions
- Ask about testability, maintainability, and extensibility
- Explore dependencies and external library choices"""

        # Document understanding context
        doc_context = ""
        if doc_understanding and doc_understanding.get("alignment"):
            alignment = doc_understanding.get("alignment", "")
            gaps = doc_understanding.get("gaps", [])
            opportunities = doc_understanding.get("opportunities", [])
            match_score = doc_understanding.get("match_score", 0.0)

            doc_context = f"""

Document Understanding:
Goal Alignment: {alignment}
Match Score: {int(match_score * 100)}%
Identified Gaps: {', '.join(gaps[:2]) if gaps else 'None identified'}
Opportunities: {', '.join(opportunities[:2]) if opportunities else 'Explore documents further'}"""

        # Build section listing previously asked questions to avoid repetition
        previous_questions_section = ""
        if previously_asked_questions:
            previous_questions_section = "\nPreviously Asked Questions in This Phase (DO NOT REPEAT THESE):"
            for i, q in enumerate(previously_asked_questions[-5:], 1):  # Show last 5 to avoid overwhelming
                # Truncate long questions for readability
                q_text = q[:120] + "..." if len(q) > 120 else q
                previous_questions_section += f"\n{i}. {q_text}"

        return f"""You are a Socratic tutor helping guide someone through their {project.project_type} project.

Project Details:
- Name: {project.name}
- Type: {project.project_type.upper() if project.project_type else 'software'}
- Current Phase: {project.phase} ({phase_descriptions.get(project.phase, '')})
- Goals: {project.goals}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
- Requirements: {', '.join(project.requirements) if project.requirements else 'Not specified'}

Project Context:
{context}{role_context}{code_context}{doc_context}

Recent Conversation:
{recent_conversation}

Relevant Knowledge:
{relevant_knowledge}{previous_questions_section}

This is question #{question_count + 1} in the {project.phase} phase. Focus on: {phase_focus.get(project.phase, '')}.

Generate ONE insightful Socratic question that:
1. Builds on what we've discussed so far
2. Helps the user think deeper about their {project.project_type} project
3. Is specific to the {project.phase} phase
4. Encourages critical thinking rather than just information gathering
5. Is relevant to their stated goals and expertise
6. Is appropriate for a {project.project_type} project (not just software-specific)
7. MUST be different from the previously asked questions listed above - do not repeat or rephrase existing questions

The question should be thought-provoking but not overwhelming. Make it conversational and engaging.
Push the conversation forward by exploring new aspects not yet discussed.

Return only the question, no additional text or explanation."""

    def _generate_static_question(self, project: ProjectContext, question_count: int) -> str:
        """Generate questions from static predefined lists"""
        questions = self.static_questions.get(project.phase, [])

        if question_count < len(questions):
            return questions[question_count]
        else:
            # Fallback questions when we've exhausted the static list
            fallbacks = {
                "discovery": "What other aspects of the problem space should we explore?",
                "analysis": "What technical considerations haven't we discussed yet?",
                "design": "What design decisions are you still uncertain about?",
                "implementation": "What implementation details would you like to work through?",
            }
            return fallbacks.get(project.phase, "What would you like to explore further?")

    def _build_full_knowledge_context(self, results: List[Dict]) -> str:
        """Build rich knowledge context with full document content and summaries"""
        if not results:
            return ""

        sections = []
        for i, result in enumerate(results, 1):
            source = (
                result["metadata"].get("source", "Unknown") if result.get("metadata") else "Unknown"
            )
            summary = result.get("summary", "")
            content = result.get("content", "")

            section = f"Document {i}: {source}\nSummary: {summary}\nContent:\n{content}"
            sections.append(section)

        return "\n\n---\n\n".join(sections)

    def _build_snippet_knowledge_context(self, results: List[Dict]) -> str:
        """Build concise knowledge context with snippets and summaries"""
        if not results:
            return ""

        sections = []
        for result in results:
            source = (
                result["metadata"].get("source", "Unknown") if result.get("metadata") else "Unknown"
            )
            summary = result.get("summary", "")
            content = result.get("content", "")

            section = f"[{source}] {summary}: {content}"
            sections.append(section)

        return "\n".join(sections)

    def _generate_document_understanding(
        self, knowledge_results: List[Dict], project: ProjectContext
    ) -> Optional[Dict[str, Any]]:
        """
        Generate document understanding analysis from knowledge results.

        Groups documents and generates summaries and goal comparisons.
        """
        if not knowledge_results:
            return None

        try:
            # Group results by source document
            docs_by_source = self._group_knowledge_by_source(knowledge_results)

            if not docs_by_source:
                return None

            # Create document understanding service
            doc_service = DocumentUnderstandingService()

            # Generate summaries for each document
            document_summaries = []
            for source, chunks in docs_by_source.items():
                chunk_contents = [c.get("full_content", c.get("content", "")) for c in chunks]

                # Determine document type from metadata
                doc_type = "text"
                if chunks and chunks[0].get("metadata", {}).get("type") == "code":
                    doc_type = "code"

                summary = doc_service.generate_document_summary(
                    chunk_contents, file_name=source, file_type=doc_type
                )
                document_summaries.append(summary)

            # Compare goals with documents if goals exist
            if project.goals and document_summaries:
                goal_comparison = doc_service.compare_goals_with_documents(
                    project.goals, document_summaries
                )
                return goal_comparison

            return None

        except Exception as e:
            self.logger.warning(f"Error generating document understanding: {e}")
            return None

    def _group_knowledge_by_source(self, results: List[Dict]) -> Dict[str, List[Dict]]:
        """Group knowledge results by source document."""
        grouped = {}

        for result in results:
            source = result.get("metadata", {}).get("source", "Unknown")
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(result)

        return grouped

    def _extract_insights_only(self, request: Dict) -> Dict:
        """Extract insights from response without processing (for direct mode confirmation)"""
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")

        project = request.get("project")
        user_response = request.get("response")

        logger.debug(f"Extracting insights only ({len(user_response)} chars)")

        # Extract insights using Claude
        logger.info("Extracting insights from user response (confirmation mode)...")
        insights = self.orchestrator.claude_client.extract_insights(user_response, project)
        self._log_extracted_insights(logger, insights)

        return {"status": "success", "insights": insights}

    def _process_response(self, request: Dict) -> Dict:
        """Process user response and extract insights"""
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")

        project = request.get("project")
        user_response = request.get("response")
        current_user = request.get("current_user")
        pre_extracted_insights = request.get("pre_extracted_insights")
        is_api_mode = request.get("is_api_mode", False)  # NEW: API mode flag

        logger.debug(f"Processing user response ({len(user_response)} chars) from {current_user}")

        # Add to conversation history with phase information
        project.conversation_history.append(
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "user",
                "content": user_response,
                "phase": project.phase,
                "author": current_user,  # Track who said what
            }
        )
        logger.debug(
            f"Added response to conversation history (total: {len(project.conversation_history)} messages)"
        )

        # Extract insights using Claude (or use pre-extracted if provided)
        if pre_extracted_insights is not None:
            logger.info("Using pre-extracted insights from direct mode confirmation")
            insights = pre_extracted_insights
        else:
            logger.info("Extracting insights from user response...")
            insights = self.orchestrator.claude_client.extract_insights(user_response, project)
            self._log_extracted_insights(logger, insights)

        # REAL-TIME CONFLICT DETECTION
        if insights:
            conflict_result = self._handle_conflict_detection(
                insights, project, current_user, logger, is_api_mode
            )
            if conflict_result.get("has_conflicts"):
                return {
                    "status": "success",
                    "insights": insights,
                    "conflicts_pending": True,
                    "conflicts": conflict_result.get("conflicts", []),
                }

        # Update context and maturity
        self._update_project_and_maturity(project, insights, logger)

        # Track question effectiveness for learning
        self._track_question_effectiveness(project, insights, user_response, current_user, logger)

        return {"status": "success", "insights": insights}

    def _handle_conflict_detection(
        self, insights, project, current_user, logger, is_api_mode=False
    ) -> dict:
        """Handle conflict detection and return result dict with conflict status

        Args:
            is_api_mode: If True, returns conflicts for frontend handling. If False, handles interactively.

        Returns:
            Dict with 'has_conflicts' bool and 'conflicts' list if in API mode
        """
        logger.info("Running conflict detection on new insights...")
        conflict_result = self.orchestrator.process_request(
            "conflict_detector",
            {
                "action": "detect_conflicts",
                "project": project,
                "new_insights": insights,
                "current_user": current_user,
            },
        )

        if not (conflict_result["status"] == "success" and conflict_result["conflicts"]):
            logger.debug("No conflicts detected")
            return {"has_conflicts": False}

        logger.warning(f"Detected {len(conflict_result['conflicts'])} conflict(s)")

        # If in API mode, return conflicts to frontend
        if is_api_mode:
            return {
                "has_conflicts": True,
                "conflicts": [self._conflict_to_dict(c) for c in conflict_result["conflicts"]],
            }

        # CLI mode: handle interactively
        conflicts_resolved = self._handle_conflicts_realtime(conflict_result["conflicts"], project)
        if not conflicts_resolved:
            logger.info("User chose not to resolve conflicts")
            return {"has_conflicts": True, "conflicts": conflict_result["conflicts"]}
        return {"has_conflicts": False}

    def _update_project_and_maturity(self, project, insights, logger) -> None:
        """Update project context and phase maturity"""
        logger.info("Updating project context with insights...")
        self._update_project_context(project, insights)
        logger.debug("Project context updated successfully")

        if not insights:
            return

        logger.info("Calculating phase maturity...")
        maturity_result = self.orchestrator.process_request(
            "quality_controller",
            {
                "action": "update_after_response",
                "project": project,
                "insights": insights,
            },
        )

        if maturity_result["status"] == "success":
            maturity = maturity_result.get("maturity", {})
            score = maturity.get("overall_score", 0.0)
            logger.info(f"Phase maturity updated: {score:.1f}%")

    def _track_question_effectiveness(
        self, project, insights, user_response, current_user, logger
    ) -> None:
        """Track question effectiveness in learning system"""
        if not (insights and project.conversation_history):
            return

        phase_messages = [
            msg for msg in project.conversation_history if msg.get("phase") == project.phase
        ]
        if len(phase_messages) < 2:  # Need at least question + response
            return

        question_msg = self._find_last_question(phase_messages)
        if not question_msg:
            return

        # Get fallback content from second-to-last message if available
        fallback_content = ""
        if len(phase_messages) >= 2:
            fallback_content = phase_messages[-2].get("content", "")[:50]
        question_id = question_msg.get("id", fallback_content)
        specs_extracted = self._count_extracted_specs(insights)

        logger.debug(f"Tracking question effectiveness: {question_id}")

        user_role = project.get_member_role(current_user) if current_user else "general"
        self.orchestrator.process_request(
            "learning",
            {
                "action": "track_question_effectiveness",
                "user_id": current_user,
                "question_template_id": question_id,
                "role": user_role,
                "answer_length": len(user_response),
                "specs_extracted": specs_extracted,
                "answer_quality": 0.5,
            },
        )

    def _find_last_question(self, phase_messages: list) -> dict:
        """Find the most recent question (assistant message) in phase"""
        for msg in reversed(phase_messages[:-1]):
            if msg.get("type") == "assistant":
                return msg
        return None

    def _count_extracted_specs(self, insights: Dict) -> int:
        """Count total specs extracted from insights"""
        return sum(
            [
                len(insights.get("goals", [])) if insights.get("goals") else 0,
                len(insights.get("requirements", [])) if insights.get("requirements") else 0,
                len(insights.get("tech_stack", [])) if insights.get("tech_stack") else 0,
                len(insights.get("constraints", [])) if insights.get("constraints") else 0,
            ]
        )

    def _log_extracted_insights(self, logger, insights: Dict) -> None:
        """Log detailed breakdown of extracted insights"""
        if not insights:
            logger.debug("No insights extracted from response")
            return

        spec_details = []
        if insights.get("goals"):
            goals = insights["goals"]
            count = len([g for g in goals if g]) if isinstance(goals, list) else 1
            spec_details.append(f"{count} goal(s)" if count > 1 else "1 goal")

        if insights.get("requirements"):
            reqs = insights["requirements"]
            count = len(reqs) if isinstance(reqs, list) else 1
            spec_details.append(f"{count} requirement(s)" if count > 1 else "1 requirement")

        if insights.get("tech_stack"):
            techs = insights["tech_stack"]
            count = len(techs) if isinstance(techs, list) else 1
            spec_details.append(f"{count} tech(s)" if count > 1 else "1 tech")

        if insights.get("constraints"):
            consts = insights["constraints"]
            count = len(consts) if isinstance(consts, list) else 1
            spec_details.append(f"{count} constraint(s)" if count > 1 else "1 constraint")

        spec_summary = ", ".join(spec_details) if spec_details else "no specs"
        logger.info(f"Extracted {spec_summary}")
        logger.debug(f"Full insights: {insights}")

    def _remove_from_project_context(self, project: ProjectContext, value: str, context_type: str):
        """Remove a value from project context"""
        if context_type == "tech_stack" and value in project.tech_stack:
            project.tech_stack.remove(value)
        elif context_type == "requirements" and value in project.requirements:
            project.requirements.remove(value)
        elif context_type == "constraints" and value in project.constraints:
            project.constraints.remove(value)
        elif context_type == "goals":
            project.goals = ""

    def _manual_resolution(self, conflict: ConflictInfo) -> str:
        """Allow user to manually resolve conflict"""
        print(f"\n{Fore.CYAN}Manual Resolution:")
        print(f"Current options: '{conflict.old_value}' vs '{conflict.new_value}'")

        new_value = input(f"{Fore.WHITE}Enter resolved specification: ").strip()
        if new_value:
            return new_value
        return ""

    def _handle_conflicts_realtime(
        self, conflicts: List[ConflictInfo], project: ProjectContext
    ) -> bool:
        """Handle conflicts in real-time during conversation"""
        for conflict in conflicts:
            print(f"\n{Fore.RED}[WARNING]  CONFLICT DETECTED!")
            print(f"{Fore.YELLOW}Type: {conflict.conflict_type}")
            print(f"{Fore.WHITE}Existing: '{conflict.old_value}' (by {conflict.old_author})")
            print(f"{Fore.WHITE}New: '{conflict.new_value}' (by {conflict.new_author})")
            print(f"{Fore.RED}Severity: {conflict.severity}")

            # Get AI-generated suggestions
            suggestions = self.orchestrator.claude_client.generate_conflict_resolution_suggestions(
                conflict, project
            )
            print(f"\n{Fore.MAGENTA}{suggestions}")

            print(f"\n{Fore.CYAN}Resolution Options:")
            print("1. Keep existing specification")
            print("2. Replace with new specification")
            print("3. Skip this specification (continue without adding)")
            print("4. Manual resolution (edit both)")

            while True:
                choice = input(f"{Fore.WHITE}Choose resolution (1-4): ").strip()

                if choice == "1":
                    print(f"{Fore.GREEN}[OK] Keeping existing: '{conflict.old_value}'")
                    self._remove_from_insights(conflict.new_value, conflict.conflict_type)
                    break
                elif choice == "2":
                    print(f"{Fore.GREEN}[OK] Replacing with: '{conflict.new_value}'")
                    self._remove_from_project_context(
                        project, conflict.old_value, conflict.conflict_type
                    )
                    break
                elif choice == "3":
                    print(f"{Fore.YELLOW}[SKIP]  Skipping specification")
                    self._remove_from_insights(conflict.new_value, conflict.conflict_type)
                    break
                elif choice == "4":
                    resolved_value = self._manual_resolution(conflict)
                    if resolved_value:
                        self._remove_from_project_context(
                            project, conflict.old_value, conflict.conflict_type
                        )
                        self._update_insights_value(
                            conflict.new_value, resolved_value, conflict.conflict_type
                        )
                        print(f"{Fore.GREEN}[OK] Updated to: '{resolved_value}'")
                    break
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.")

        return True

    def _explain_document(self, request: Dict) -> Dict:
        """
        Provide explanation/summary of imported documents.

        Generates comprehensive summaries and analysis of documents in the knowledge base.
        """
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")

        project = request.get("project")
        document_name = request.get("document_name")  # Optional: specific document

        if not project:
            return {"status": "error", "message": "Project context required"}

        try:
            # Search for document chunks
            if document_name:
                # Search for specific document
                logger.debug(f"Searching for specific document: {document_name}")
                query = document_name
            else:
                # Use project context to find documents
                logger.debug("Searching for all documents in project")
                query = project.goals or project.name or "document"

            # Search knowledge base
            results = self.orchestrator.vector_db.search_similar_adaptive(
                query=query, strategy="full", top_k=10, project_id=project.project_id
            )

            if not results:
                return {"status": "error", "message": "No documents found for this project"}

            logger.debug(f"Found {len(results)} results for document explanation")

            # Group by source and generate understanding
            doc_service = DocumentUnderstandingService()
            docs_by_source = self._group_knowledge_by_source(results)

            explanations = []
            for source, chunks in docs_by_source.items():
                chunk_contents = [c.get("full_content", c.get("content", "")) for c in chunks]

                # Determine document type
                doc_type = "text"
                if chunks and chunks[0].get("metadata", {}).get("type") == "code":
                    doc_type = "code"

                summary = doc_service.generate_document_summary(
                    chunk_contents, file_name=source, file_type=doc_type
                )

                explanation = self._format_document_explanation(summary)
                explanations.append(explanation)

                logger.debug(f"Generated explanation for {source}")

            return {
                "status": "success",
                "documents_found": len(explanations),
                "explanations": explanations,
                "message": f"Generated explanations for {len(explanations)} document(s)",
            }

        except Exception as e:
            logger.error(f"Error explaining documents: {e}")
            return {"status": "error", "message": f"Failed to explain documents: {str(e)}"}

    def _format_document_explanation(self, summary: Dict[str, Any]) -> str:
        """Format document summary into human-readable explanation."""
        parts = []

        # Document header
        file_name = summary.get("file_name", "Unknown")
        doc_type = summary.get("type", "text")
        complexity = summary.get("complexity", "intermediate")

        parts.append(f"Document: {file_name} ({doc_type}, {complexity} complexity)")
        parts.append("-" * 60)
        parts.append("")

        # Summary
        if summary.get("summary"):
            parts.append("Summary:")
            parts.append(summary["summary"])
            parts.append("")

        # Key points
        key_points = summary.get("key_points", [])
        if key_points:
            parts.append("Key Points:")
            for i, point in enumerate(key_points, 1):
                parts.append(f"  {i}. {point}")
            parts.append("")

        # Topics
        topics = summary.get("topics", [])
        if topics:
            parts.append("Main Topics:")
            parts.append(", ".join(topics))
            parts.append("")

        # Metrics
        length = summary.get("length", 0)
        if length > 0:
            parts.append("Document Metrics:")
            parts.append(f"  - Length: {length} words")
            parts.append(f"  - Complexity: {complexity}")
            parts.append("")

        return "\n".join(parts)

    def _advance_phase(self, request: Dict) -> Dict:
        """Advance project to the next phase with maturity verification"""
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")

        project = request.get("project")
        phases = ["discovery", "analysis", "design", "implementation"]

        current_index = phases.index(project.phase)
        if current_index >= len(phases) - 1:
            return {
                "status": "error",
                "message": "Already at final phase (implementation)",
            }

        # NEW: Check maturity before advancing
        logger.info(f"Verifying readiness to advance from {project.phase}...")
        readiness_result = self.orchestrator.process_request(
            "quality_controller",
            {
                "action": "verify_advancement",
                "project": project,
                "from_phase": project.phase,
            },
        )

        if readiness_result["status"] == "success":
            verification = readiness_result["verification"]
            maturity_score = verification.get("maturity_score", 0.0)
            warnings = verification.get("warnings", [])

            # Display warnings to user if present
            if warnings:
                print(f"\n{Fore.YELLOW}⚠ MATURITY WARNINGS:{Fore.RESET}")
                for warning in warnings[:3]:  # Show top 3 warnings
                    print(f"  • {warning}")

                # Ask for confirmation if maturity is low
                if maturity_score < 60.0:
                    print(f"\n{Fore.RED}Current phase maturity: {maturity_score:.1f}%")
                    print(f"Recommended minimum: 60%{Fore.RESET}")

                    confirm = input(f"\n{Fore.CYAN}Advance anyway? (yes/no): {Fore.RESET}").lower()
                    if confirm not in ["yes", "y"]:
                        return {
                            "status": "cancelled",
                            "message": "Phase advancement cancelled",
                        }

        # Advance to next phase
        new_phase = phases[current_index + 1]
        project.phase = new_phase
        logger.info(f"Advanced project from {phases[current_index]} to {new_phase}")

        # NEW: Emit PHASE_ADVANCED event
        self.emit_event(
            EventType.PHASE_ADVANCED,
            {
                "from_phase": phases[current_index],
                "to_phase": new_phase,
                "maturity_at_advancement": (
                    verification.get("maturity_score", 0.0)
                    if readiness_result["status"] == "success"
                    else None
                ),
            },
        )

        self.log(f"Advanced project to {new_phase} phase")

        return {"status": "success", "new_phase": new_phase}

    def _normalize_to_list(self, value: Any) -> List[str]:
        """Convert any value to a list of non-empty strings"""
        if isinstance(value, list):
            return [str(item).strip() for item in value if item]
        elif isinstance(value, str):
            return [value.strip()] if value.strip() else []
        else:
            normalized = str(value).strip()
            return [normalized] if normalized else []

    def _update_list_field(self, current_list: List[str], new_items: List[str]) -> None:
        """Add new unique items to a list field"""
        for item in new_items:
            if item and item not in current_list:
                current_list.append(item)

    def _update_project_context(self, project: ProjectContext, insights: Dict):
        """Update project context based on extracted insights"""
        if not insights or not isinstance(insights, dict):
            return

        try:
            # Handle goals
            if "goals" in insights and insights["goals"]:
                goals_list = self._normalize_to_list(insights["goals"])
                if goals_list:
                    project.goals = " ".join(goals_list)

            # Handle requirements
            if "requirements" in insights and insights["requirements"]:
                req_list = self._normalize_to_list(insights["requirements"])
                self._update_list_field(project.requirements, req_list)

            # Handle tech_stack
            if "tech_stack" in insights and insights["tech_stack"]:
                tech_list = self._normalize_to_list(insights["tech_stack"])
                self._update_list_field(project.tech_stack, tech_list)

            # Handle constraints
            if "constraints" in insights and insights["constraints"]:
                constraint_list = self._normalize_to_list(insights["constraints"])
                self._update_list_field(project.constraints, constraint_list)

        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Error updating project context: {e}")
            print(f"Insights received: {insights}")

    def _conflict_to_dict(self, conflict) -> dict:
        """Convert ConflictInfo object to dictionary for JSON serialization"""
        return {
            "conflict_id": conflict.conflict_id,
            "conflict_type": conflict.conflict_type,
            "old_value": conflict.old_value,
            "new_value": conflict.new_value,
            "old_author": conflict.old_author,
            "new_author": conflict.new_author,
            "old_timestamp": conflict.old_timestamp,
            "new_timestamp": conflict.new_timestamp,
            "severity": conflict.severity,
            "suggestions": conflict.suggestions,
        }

    def _remove_from_insights(self, value: str, insight_type: str):
        """Remove a value from insights before context update.

        This method is called when user rejects a conflicting insight.
        Since insights are processed per-request and don't persist in agent state,
        this mainly serves as a logging hook for conflict resolution decisions.

        Args:
            value: The value to remove (the new/conflicting value)
            insight_type: Type of insight (goals, requirements, tech_stack, constraints)
        """
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")
        logger.info(f"Conflict resolution: Rejected {insight_type} - '{value}'")

    def _update_insights_value(self, old_value: str, new_value: str, insight_type: str):
        """Update a value in insights after manual conflict resolution.

        This method is called when user manually resolves a conflict.
        Since insights are processed per-request and don't persist in agent state,
        this mainly serves as a logging hook for conflict resolution decisions.
        The actual project context update happens via _remove_from_project_context.

        Args:
            old_value: The old/existing value in the project
            new_value: The new/resolved value from manual input
            insight_type: Type of insight (goals, requirements, tech_stack, constraints)
        """
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")
        logger.info(
            f"Conflict resolution: Manual resolution for {insight_type} - "
            f"'{old_value}' -> '{new_value}'"
        )

    def _generate_hint(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a context-aware hint for the user based on project state"""
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")
        project = request.get("project")

        if not project:
            return {"status": "error", "message": "Project context is required to generate hints"}

        try:
            context = self.orchestrator.context_analyzer.get_context_summary(project)

            # Get recent conversation for context
            recent_conversation = ""
            if project.conversation_history:
                recent_messages = project.conversation_history[-3:]
                for msg in recent_messages:
                    role = "Assistant" if msg.get("type") == "assistant" else "User"
                    recent_conversation += f"{role}: {msg.get('content', '')}\n"

            # Build hint prompt
            hint_prompt = f"""Based on the following project context and conversation, provide a helpful, concise hint to guide the user forward.

Project Phase: {project.phase}
Project Goals: {project.goals or 'Not specified'}
Requirements: {', '.join(project.requirements) if project.requirements else 'Not specified'}
Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}

Recent Conversation:
{recent_conversation if recent_conversation else 'No conversation history yet'}

Provide ONE concise, actionable hint that helps the user move forward in the {project.phase} phase. The hint should be specific to their project context and no more than 2 sentences."""

            logger.info(
                f"Generating hint for project {project.project_id} in {project.phase} phase"
            )

            # Generate hint using Claude
            hint = self.orchestrator.claude_client.generate_response(
                prompt=hint_prompt,
                max_tokens=500,  # Hints should be concise (1-2 sentences)
                temperature=0.7  # Balanced creativity
            )

            self.log(f"Generated hint for {project.phase} phase")

            return {"status": "success", "hint": hint, "context": context}

        except Exception as e:
            logger.warning(f"Failed to generate dynamic hint: {e}, returning generic hint")
            self.log(f"Failed to generate dynamic hint: {e}", "WARN")

            # Provide context-appropriate generic hints as fallback
            phase_hints = {
                "discovery": "Focus on understanding the problem space. What specific needs does your project address?",
                "analysis": "Break down technical requirements into smaller, manageable challenges. What's your biggest concern?",
                "design": "Sketch out the architecture before implementation. What design patterns might help?",
                "implementation": "Start with the core features and iterate. What's your minimum viable product?",
            }

            return {
                "status": "success",
                "hint": phase_hints.get(project.phase, "Keep making progress on your project!"),
                "context": "",
            }

    def _answer_question(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a question as answered"""
        import datetime

        project = request.get("project")
        question_id = request.get("question_id")

        if not project or not question_id:
            return {"status": "error", "message": "Project and question_id required"}

        # Find and mark the question as answered in pending_questions
        for q in project.pending_questions or []:
            if q.get("id") == question_id:
                q["status"] = "answered"
                q["answered_at"] = datetime.datetime.now().isoformat()
                self.log(f"Marked question {question_id} as answered")
                # Save project to persist the change
                self.database.save_project(project)
                return {"status": "success", "message": "Question marked as answered"}

        return {"status": "error", "message": "Question not found"}

    def _skip_question(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a question as skipped"""
        import datetime

        project = request.get("project")
        question_id = request.get("question_id")

        if not project or not question_id:
            return {"status": "error", "message": "Project and question_id required"}

        # Find and mark the question as skipped in pending_questions
        for q in project.pending_questions or []:
            if q.get("id") == question_id:
                q["status"] = "skipped"
                q["skipped_at"] = datetime.datetime.now().isoformat()
                self.log(f"Marked question {question_id} as skipped")
                # Save project to persist the change
                self.database.save_project(project)
                return {"status": "success", "message": "Question marked as skipped"}

        return {"status": "error", "message": "Question not found"}

    def _reopen_question(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Reopen a skipped question (mark as unanswered)"""
        import datetime

        project = request.get("project")
        question_id = request.get("question_id")

        if not project or not question_id:
            return {"status": "error", "message": "Project and question_id required"}

        # Find and mark the question as unanswered in pending_questions
        for q in project.pending_questions or []:
            if q.get("id") == question_id:
                q["status"] = "unanswered"
                q["skipped_at"] = None  # Clear skip timestamp
                self.log(f"Reopened question {question_id}")
                # Save project to persist the change
                self.database.save_project(project)
                return {"status": "success", "message": "Question reopened and ready to answer"}

        return {"status": "error", "message": "Question not found"}

    def _generate_answer_suggestions(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate answer suggestions for the current question"""
        from socratic_system.utils.logger import get_logger

        logger = get_logger("socratic_counselor")
        project = request.get("project")
        current_question = request.get("current_question")

        if not project or not current_question:
            return {"status": "error", "message": "Project and current_question required"}

        try:
            # Build prompt for suggestions
            suggestions_prompt = f"""Based on this Socratic question in the {project.phase} phase:

Question: {current_question}

Project Context:
- Name: {project.name}
- Phase: {project.phase}
- Goals: {project.goals or 'Not specified'}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
- Requirements: {', '.join(project.requirements) if project.requirements else 'Not specified'}

Provide 3-5 specific, actionable answer suggestions or starting points. Each suggestion should be a complete sentence that the user could use as a basis for their answer.

Format as a numbered list (1. 2. 3. etc). Return only the numbered list, no additional text."""

            logger.info(f"Generating answer suggestions for {project.phase} phase")

            # Call Claude to generate suggestions
            response = self.orchestrator.claude_client.generate_response(
                prompt=suggestions_prompt,
                max_tokens=800,
                temperature=0.7
            )

            # Parse suggestions from numbered list
            suggestions = []
            for line in response.split('\n'):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
                    # Remove numbering and clean up
                    suggestion = line.split(".", 1)[1].strip() if "." in line else line
                    suggestions.append(suggestion)

            self.log(f"Generated {len(suggestions)} answer suggestions")

            return {
                "status": "success",
                "suggestions": suggestions if suggestions else [
                    "Consider the problem from your target audience's perspective",
                    "Think about the technical constraints you mentioned",
                    "Review the project goals and how this relates to them",
                    "Consider existing solutions and what makes your approach unique",
                    "Think about potential challenges and how to address them"
                ]
            }

        except Exception as e:
            logger.warning(f"Failed to generate answer suggestions: {e}")
            self.log(f"Failed to generate answer suggestions: {e}", "WARN")

            # Return generic suggestions as fallback
            return {
                "status": "success",
                "suggestions": [
                    "Consider the problem from your target audience's perspective",
                    "Think about the technical constraints you mentioned",
                    "Review the project goals and how this relates to them",
                    "Consider existing solutions and what makes your approach unique",
                    "Think about potential challenges and how to address them"
                ]
            }
