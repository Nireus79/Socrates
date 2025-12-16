"""
Socratic counselor agent for guided questioning and response processing
"""

import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from colorama import Fore

from socratic_system.agents.document_context_analyzer import DocumentContextAnalyzer
from socratic_system.events import EventType
from socratic_system.models import ROLE_FOCUS_AREAS, ConflictInfo, ProjectContext

from .base import Agent

if TYPE_CHECKING:
    from socratic_system.orchestration import AgentOrchestrator


class SocraticCounselorAgent(Agent):
    """Core agent that guides users through Socratic questioning about their project"""

    def __init__(self, orchestrator: "AgentOrchestrator") -> None:
        super().__init__("SocraticCounselor", orchestrator)
        self.use_dynamic_questions = True  # Toggle for dynamic vs static questions
        self.max_questions_per_phase = 5

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
        elif action == "toggle_dynamic_questions":
            self.use_dynamic_questions = not self.use_dynamic_questions
            return {"status": "success", "dynamic_mode": self.use_dynamic_questions}

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

        context = self.orchestrator.context_analyzer.get_context_summary(project)

        # NEW: Check question limit
        from socratic_system.subscription.checker import SubscriptionChecker

        user = self.orchestrator.database.load_user(current_user)

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
        if project.conversation_history:
            recent_messages = project.conversation_history[-4:]  # Last 4 messages
            for msg in recent_messages:
                role = "Assistant" if msg["type"] == "assistant" else "User"
                recent_conversation += f"{role}: {msg['content']}\n"
            logger.debug(f"Using {len(recent_messages)} recent messages for context")

        # Get relevant knowledge from vector database with adaptive loading strategy
        relevant_knowledge = ""
        if context:
            logger.debug("Analyzing question context for adaptive document loading...")

            # Use DocumentContextAnalyzer to determine loading strategy
            doc_analyzer = DocumentContextAnalyzer()

            # Convert project context to dict format for analyzer
            project_context_dict = {
                "current_phase": project.phase,
                "goals": project.goals or ""
            }

            # Determine loading strategy based on conversation context
            strategy = doc_analyzer.analyze_question_context(
                project_context=project_context_dict,
                conversation_history=project.conversation_history,
                question_count=question_count
            )

            logger.debug(f"Using '{strategy}' document loading strategy")

            # Get top_k based on strategy
            top_k = 5 if strategy == "full" else 3

            # Use adaptive search
            knowledge_results = self.orchestrator.vector_db.search_similar_adaptive(
                query=context,
                strategy=strategy,
                top_k=top_k,
                project_id=project.project_id
            )

            if knowledge_results:
                # Build knowledge context based on strategy
                if strategy == "full":
                    relevant_knowledge = self._build_full_knowledge_context(knowledge_results)
                else:
                    relevant_knowledge = self._build_snippet_knowledge_context(knowledge_results)

                logger.debug(f"Found {len(knowledge_results)} relevant knowledge items with strategy '{strategy}'")

        logger.debug(
            f"Building question prompt for {project.phase} phase (question #{question_count + 1})"
        )
        prompt = self._build_question_prompt(
            project, context, recent_conversation, relevant_knowledge, question_count, current_user
        )

        try:
            logger.info(f"Generating dynamic question for {project.phase} phase")
            question = self.orchestrator.claude_client.generate_socratic_question(prompt)
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
    ) -> str:
        """Build prompt for dynamic question generation with role-aware context"""
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

        return f"""You are a Socratic tutor helping guide someone through their {project.project_type} project.

Project Details:
- Name: {project.name}
- Type: {project.project_type.upper() if project.project_type else 'software'}
- Current Phase: {project.phase} ({phase_descriptions.get(project.phase, '')})
- Goals: {project.goals}
- Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}
- Requirements: {', '.join(project.requirements) if project.requirements else 'Not specified'}

Project Context:
{context}{role_context}

Recent Conversation:
{recent_conversation}

Relevant Knowledge:
{relevant_knowledge}

This is question #{question_count + 1} in the {project.phase} phase. Focus on: {phase_focus.get(project.phase, '')}.

Generate ONE insightful Socratic question that:
1. Builds on what we've discussed so far
2. Helps the user think deeper about their {project.project_type} project
3. Is specific to the {project.phase} phase
4. Encourages critical thinking rather than just information gathering
5. Is relevant to their stated goals and expertise
6. Is appropriate for a {project.project_type} project (not just software-specific)

The question should be thought-provoking but not overwhelming. Make it conversational and engaging.

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
            source = result["metadata"].get("source", "Unknown") if result.get("metadata") else "Unknown"
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
            source = result["metadata"].get("source", "Unknown") if result.get("metadata") else "Unknown"
            summary = result.get("summary", "")
            content = result.get("content", "")

            section = f"[{source}] {summary}: {content}"
            sections.append(section)

        return "\n".join(sections)

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
            if not self._handle_conflict_detection(insights, project, current_user, logger):
                return {"status": "success", "insights": insights, "conflicts_pending": True}

        # Update context and maturity
        self._update_project_and_maturity(project, insights, logger)

        # Track question effectiveness for learning
        self._track_question_effectiveness(project, insights, user_response, current_user, logger)

        return {"status": "success", "insights": insights}

    def _handle_conflict_detection(self, insights, project, current_user, logger) -> bool:
        """Handle conflict detection and return whether to continue"""
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
            return True

        logger.warning(f"Detected {len(conflict_result['conflicts'])} conflict(s)")
        conflicts_resolved = self._handle_conflicts_realtime(conflict_result["conflicts"], project)
        if not conflicts_resolved:
            logger.info("User chose not to resolve conflicts")
            return False
        return True

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

        question_id = question_msg.get("id", phase_messages[-2].get("content", "")[:50])
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

    def _remove_from_insights(self, value: str, insight_type: str):
        """Remove a value from insights before context update"""
        pass

    def _update_insights_value(self, old_value: str, new_value: str, insight_type: str):
        """Update a value in insights before context update"""
        pass
