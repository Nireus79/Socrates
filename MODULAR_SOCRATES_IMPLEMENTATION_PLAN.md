# Modular Socrates Implementation Plan

Complete redesign plan to replicate monolithic Socrates mechanism while maintaining modularity.

---

## PHASE 1: FOUNDATION & ARCHITECTURE (Weeks 1-2)

### 1.1 Orchestrator Restructuring

**File**: `backend/src/socrates_api/orchestrator.py`

**Current Issues:**
- Orchestrator doesn't gather full context before calling agents
- Knowledge base integration is missing
- Document understanding not integrated
- Multi-agent coordination is implicit, not explicit

**Required Changes:**

#### A. Add Context Gathering Methods

```python
class APIOrchestrator:
    # NEW METHOD
    async def _gather_question_context(
        self,
        project_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Gather all context needed for dynamic question generation.
        This is the central context aggregation point.
        """
        project = await self._get_project(project_id)

        # 1. Get project context
        project_context = {
            "goals": project.context.goals,
            "requirements": project.context.requirements,
            "tech_stack": project.context.tech_stack,
            "constraints": project.context.constraints,
            "existing_specs": self._get_extracted_specs(project)
        }

        # 2. Get recent conversation
        recent_messages = self._get_recent_messages(
            project.conversation_history,
            limit=4
        )

        # 3. Get previously asked questions
        previously_asked = self._extract_previously_asked_questions(
            project.pending_questions,
            project.phase
        )

        # 4. Determine KB strategy and get chunks
        kb_strategy = self._determine_kb_strategy(
            project.phase,
            len(project.pending_questions)  # question_number
        )
        knowledge_chunks = await self.vector_db.search_similar_adaptive(
            query=project.pending_questions[0]["question"] if project.pending_questions
                  else "general context",
            strategy=kb_strategy,
            phase=project.phase
        )

        # 5. Get document understanding
        doc_service = DocumentUnderstandingService()
        document_understanding = await doc_service.analyze_documents(
            documents=self._get_imported_documents(project),
            project_context=project_context
        )

        # 6. Get user role
        user_role = project.get_member_role(user_id)

        # 7. Get code structure if present
        code_structure = None
        if project.files:
            code_structure = self._analyze_code_structure(project.files)

        return {
            "project_context": project_context,
            "phase": project.phase,
            "recent_messages": recent_messages,
            "previously_asked_questions": previously_asked,
            "knowledge_base_chunks": knowledge_chunks,
            "document_understanding": document_understanding,
            "user_role": user_role,
            "question_number": len([q for q in project.pending_questions
                                    if q.get("status") != "answered"]),
            "code_structure": code_structure,
            "conversation_history": project.conversation_history
        }

    # NEW METHOD
    def _determine_kb_strategy(self, phase: str, question_number: int) -> str:
        """
        Determine adaptive knowledge base loading strategy.
        """
        # Check cache first
        cache_key = f"{phase}_kb_strategy"
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]

        # Determine strategy
        if phase in ["discovery", "analysis"] and question_number < 5:
            strategy = "snippet"  # 3 chunks, fast
        elif phase in ["design", "implementation"] or question_number >= 5:
            strategy = "full"     # 5 chunks, comprehensive
        else:
            strategy = "snippet"  # default safe choice

        # Cache for this phase
        self._context_cache[cache_key] = strategy

        return strategy
```

#### B. Add Multi-Agent Coordination Methods

```python
class APIOrchestrator:
    # NEW METHOD
    async def _orchestrate_question_generation(
        self,
        project_id: str,
        user_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Orchestrate complete question generation flow with all agents.
        Single point of coordination for question generation.
        """
        project = await self._get_project(project_id)

        # 1. Check for pending unanswered questions
        if not force_refresh and project.pending_questions:
            unanswered = [q for q in project.pending_questions
                         if q.get("status") == "unanswered"]
            if unanswered:
                # Return existing question instead of generating new
                return {
                    "status": "success",
                    "question": unanswered[0],
                    "existing": True
                }

        # 2. Gather full context
        context = await self._gather_question_context(project_id, user_id)

        # 3. Call ContextAnalyzer for project summary
        project_summary = await self.agents["context_analyzer"].generate_project_summary(
            project_context=context["project_context"],
            conversation_history=context["conversation_history"],
            current_phase=context["phase"]
        )
        context["project_summary"] = project_summary

        # 4. Call SocraticCounselor for question generation
        question_response = await self.agents["socratic_counselor"].generate_dynamic_question(
            **context
        )

        if question_response.get("status") != "success":
            # Fallback question
            question_response = self._get_fallback_question(context["phase"])

        # 5. Store generated question
        question_entry = {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "question": question_response["question"],
            "phase": context["phase"],
            "status": "unanswered",
            "created_at": datetime.now().isoformat(),
            "answer": None,
            "answered_at": None,
            "skipped_at": None,
            "metadata": question_response.get("metadata", {})
        }
        project.pending_questions.append(question_entry)
        await self._save_project(project)

        # 6. Track in analytics
        await self.agents["learning_agent"].track_question_generation(
            user_id=user_id,
            question_id=question_entry["id"],
            phase=context["phase"],
            kb_strategy=context.get("kb_strategy")
        )

        return {
            "status": "success",
            "question": question_entry,
            "context": question_response.get("context_used", {})
        }

    # NEW METHOD
    async def _orchestrate_answer_processing(
        self,
        project_id: str,
        user_id: str,
        question_id: str,
        answer_text: str
    ) -> Dict[str, Any]:
        """
        Orchestrate complete answer processing flow with all agents.
        Handles: specs extraction → conflict detection → maturity update → learning tracking.
        """
        project = await self._get_project(project_id)

        # 1. Find question being answered
        question = self._find_question(project, question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # 2. Add to conversation history
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "content": answer_text,
            "phase": project.phase,
            "question_id": question_id,
            "author": user_id
        }
        project.conversation_history.append(conversation_entry)

        # 3. Call SocraticCounselor to extract specs
        specs_response = await self.agents["socratic_counselor"].extract_specs_from_response(
            user_answer=answer_text,
            question=question["question"],
            project_context=project.context.__dict__,
            phase=project.phase
        )

        # 4. MARK QUESTION AS ANSWERED (BEFORE conflict detection - critical timing)
        question["status"] = "answered"
        question["answered_at"] = datetime.now().isoformat()
        question["answer"] = answer_text

        # Also mark in asked_questions for permanent history
        asked_entry = {
            "question_id": question_id,
            "question": question["question"],
            "answer": answer_text,
            "phase": project.phase,
            "timestamp": datetime.now().isoformat(),
            "specs_extracted": specs_response.get("specs", {})
        }
        project.asked_questions.append(asked_entry)

        # 5. Call conflict detector
        conflicts_response = await self.agents["socratic_counselor"].detect_conflicts(
            new_specs=specs_response.get("specs", {}),
            existing_specs=self._get_existing_specs(project),
            context=project.context.__dict__
        )

        # 6. Call QualityController to update maturity
        maturity_response = await self.agents["quality_controller"].update_after_response(
            specs=specs_response.get("specs", {}),
            answer_quality=specs_response.get("overall_confidence", 0.5),
            answer_length=len(answer_text)
        )
        project.phase_maturity[project.phase] = maturity_response.get("maturity", 0)

        # 7. Call LearningAgent to track effectiveness
        await self.agents["learning_agent"].track_question_effectiveness(
            user_id=user_id,
            question_id=question_id,
            question_text=question["question"],
            user_role=project.get_member_role(user_id),
            phase=project.phase,
            answer_text=answer_text,
            specs_extracted=specs_response.get("specs", {}),
            answer_quality=specs_response.get("overall_confidence", 0.5),
            time_to_answer=0  # Would be calculated on frontend
        )

        # 8. Save updated project
        await self._save_project(project)

        # 9. Check phase completion
        phase_complete = maturity_response.get("maturity", 0) >= 100

        return {
            "status": "success",
            "specs_extracted": specs_response.get("specs", {}),
            "phase_maturity": maturity_response.get("maturity", 0),
            "conflicts": conflicts_response.get("conflicts_found", []),
            "phase_complete": phase_complete
        }

    # NEW METHOD
    async def _orchestrate_answer_suggestions(
        self,
        project_id: str,
        user_id: str,
        question_id: str
    ) -> Dict[str, Any]:
        """
        Orchestrate answer suggestions generation.
        Generates 3-5 DIVERSE suggestions (different angles, not variations).
        """
        project = await self._get_project(project_id)

        # 1. Find current question
        question = self._find_question(project, question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # 2. Gather context
        context = {
            "question": question["question"],
            "project_context": project.context.__dict__,
            "phase": project.phase,
            "user_role": project.get_member_role(user_id),
            "recent_messages": self._get_recent_messages(
                project.conversation_history,
                limit=2
            ),
            "diversity_emphasis": True  # Critical: emphasize diverse approaches
        }

        # 3. Call SocraticCounselor for suggestions
        suggestions_response = await self.agents["socratic_counselor"].generate_answer_suggestions(
            **context
        )

        if suggestions_response.get("status") != "success":
            # Use fallback suggestions
            suggestions_response = self._get_fallback_suggestions(project.phase)

        return {
            "status": "success",
            "suggestions": suggestions_response.get("suggestions", [])
        }
```

---

### 1.2 Add Agent Initialization

```python
class APIOrchestrator:
    async def __init__(self, ...):
        # ... existing code ...

        # Initialize agents with dependencies
        self.agents = {
            "context_analyzer": ContextAnalyzerAgent(),
            "document_understanding": DocumentUnderstandingService(),
            "socratic_counselor": SocraticCounselorAgent(),
            "quality_controller": QualityControllerAgent(),
            "learning_agent": LearningAgent(),
            "conflict_detector": ConflictDetectorAgent()
        }

        # Initialize caching
        self._context_cache = {}
        self._kb_cache = {}
```

---

### 1.3 Update Endpoint Router Integration

```python
# In orchestrator.process_request():
async def process_request(self, request: dict) -> dict:
    router = request.get("router")

    if router == "socratic_counselor":
        if request.get("action") == "get_question":
            return await self._orchestrate_question_generation(
                project_id=request["project_id"],
                user_id=request["user_id"],
                force_refresh=request.get("force_refresh", False)
            )
        elif request.get("action") == "process_answer":
            return await self._orchestrate_answer_processing(
                project_id=request["project_id"],
                user_id=request["user_id"],
                question_id=request["question_id"],
                answer_text=request["answer"]
            )
        elif request.get("action") == "get_suggestions":
            return await self._orchestrate_answer_suggestions(
                project_id=request["project_id"],
                user_id=request["user_id"],
                question_id=request["question_id"]
            )

    # ... handle other routers ...
```

---

## PHASE 2: ENDPOINTS REDESIGN (Week 2-3)

### 2.1 Update /chat/question Endpoint

**File**: `backend/src/socrates_api/routers/projects_chat.py`

**Current Code** (lines 595-782):
- Extracts all questions from batch
- Stores all 3 in pending_questions
- Returns first

**New Implementation**:

```python
@router.post("/{project_id}/chat/question")
async def get_question(
    project_id: str,
    request: QuestionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    orchestrator: APIOrchestrator = Depends(get_orchestrator)
):
    """
    Get next Socratic question with full context awareness.

    Dynamic generation:
    - Checks for unanswered pending questions first
    - If none, generates new question with comprehensive context
    - Knowledge base grounded
    - Role-aware
    - Document-informed
    """
    try:
        # Call orchestrator to generate/return question
        response = await orchestrator._orchestrate_question_generation(
            project_id=project_id,
            user_id=current_user.user_id,
            force_refresh=request.force_refresh or False
        )

        return {
            "status": "success",
            "question": {
                "id": response["question"]["id"],
                "text": response["question"]["question"],
                "phase": response["question"]["phase"],
                "can_skip": True,
                "can_reopen_previous": len(response["question"]) > 0
            },
            "context": {
                "phase": response["question"]["phase"],
                "question_number": request.question_number or 1,
                "is_existing": response.get("existing", False),
                "kb_context": response.get("context", {})
            }
        }
    except Exception as e:
        logger.error(f"Error getting question: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 2.2 Update /chat/message Endpoint

**Current Code** (lines 1075-1095):
- Only updates answered question in asked_questions
- Doesn't extract specs
- Doesn't detect conflicts
- Doesn't update maturity

**New Implementation**:

```python
@router.post("/{project_id}/chat/message")
async def send_message(
    project_id: str,
    request: ChatMessageRequest,  # Contains: question_id, answer, user_id
    current_user: CurrentUser = Depends(get_current_user),
    orchestrator: APIOrchestrator = Depends(get_orchestrator)
):
    """
    Process user answer to question.

    Full flow:
    1. Add answer to conversation history
    2. Extract specifications
    3. Mark question as answered (before conflict detection)
    4. Detect conflicts
    5. Update maturity
    6. Track analytics
    """
    try:
        # Call orchestrator to process answer completely
        response = await orchestrator._orchestrate_answer_processing(
            project_id=project_id,
            user_id=current_user.user_id,
            question_id=request.question_id,
            answer_text=request.answer
        )

        return {
            "status": "success",
            "message": "Answer processed successfully",
            "specs_extracted": response.get("specs_extracted", {}),
            "phase_maturity": response.get("phase_maturity", 0),
            "conflicts": response.get("conflicts", []),
            "next_action": "phase_complete" if response.get("phase_complete") else "continue"
        }
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 2.3 Add /chat/suggestions Endpoint (NEW)

```python
@router.post("/{project_id}/chat/suggestions")
async def get_suggestions(
    project_id: str,
    request: SuggestionsRequest,  # Contains: question_id
    current_user: CurrentUser = Depends(get_current_user),
    orchestrator: APIOrchestrator = Depends(get_orchestrator)
):
    """
    Get diverse answer suggestions for current question.

    Returns 3-5 suggestions with different approaches:
    - Different methodology
    - Different perspective
    - Different scope
    - Different strategy

    NOT variations on same answer - fundamentally different angles.
    """
    try:
        response = await orchestrator._orchestrate_answer_suggestions(
            project_id=project_id,
            user_id=current_user.user_id,
            question_id=request.question_id
        )

        return {
            "status": "success",
            "suggestions": response.get("suggestions", []),
            "message": "Here are different approaches to answer this question"
        }
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 2.4 Add /chat/skip Endpoint (NEW)

```python
@router.post("/{project_id}/chat/skip")
async def skip_question(
    project_id: str,
    request: SkipRequest,  # Contains: question_id
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Skip current question without answering.
    """
    try:
        project = db.query(Project).filter_by(project_id=project_id).first()

        # Mark question as skipped
        for q in project.pending_questions:
            if q["id"] == request.question_id:
                q["status"] = "skipped"
                q["skipped_at"] = datetime.now().isoformat()
                break

        db.commit()

        return {
            "status": "success",
            "message": "Question skipped",
            "question_skipped": request.question_id
        }
    except Exception as e:
        logger.error(f"Error skipping question: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 2.5 Add /chat/reopen Endpoint (NEW)

```python
@router.post("/{project_id}/chat/reopen")
async def reopen_question(
    project_id: str,
    request: ReopenRequest,  # Contains: question_id
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reopen a previously skipped question for answering.
    """
    try:
        project = db.query(Project).filter_by(project_id=project_id).first()

        # Mark question as unanswered (revert from skipped)
        for q in project.pending_questions:
            if q["id"] == request.question_id:
                q["status"] = "unanswered"
                q["skipped_at"] = None
                break

        db.commit()

        return {
            "status": "success",
            "message": "Question reopened",
            "question": q  # Return reopened question
        }
    except Exception as e:
        logger.error(f"Error reopening question: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PHASE 3: CONFLICT RESOLUTION FLOW (Week 3)

### 3.1 Add /conflicts/resolve Endpoint

```python
@router.post("/{project_id}/conflicts/resolve")
async def resolve_conflict(
    project_id: str,
    request: ConflictResolutionRequest,  # Contains: conflict_id, resolution_choice, resolution_data
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User resolves a detected conflict.

    Choices:
    1. Keep existing specification
    2. Replace with new specification
    3. Skip new specification
    4. Manual resolution (edit both)
    """
    try:
        project = db.query(Project).filter_by(project_id=project_id).first()

        # Find conflict
        conflict = None
        for c in project.pending_conflicts:
            if c["id"] == request.conflict_id:
                conflict = c
                break

        if not conflict:
            raise ValueError("Conflict not found")

        # Apply resolution
        if request.resolution_choice == "keep_existing":
            # Keep existing spec, discard new
            pass
        elif request.resolution_choice == "replace":
            # Replace existing with new
            spec_field = conflict["field"]
            project.context.__dict__[spec_field] = conflict["new"]["value"]
        elif request.resolution_choice == "skip":
            # Skip new specification entirely
            pass
        elif request.resolution_choice == "manual":
            # User manually edited one or both
            if request.new_existing:
                project.context.__dict__[conflict["field"]] = request.new_existing
            if request.new_value:
                conflict["new"]["value"] = request.new_value

        # Remove conflict from pending
        project.pending_conflicts.remove(conflict)

        db.commit()

        return {
            "status": "success",
            "message": "Conflict resolved",
            "resolution": request.resolution_choice
        }
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PHASE 4: PHASE ADVANCEMENT FLOW (Week 3)

### 4.1 Add /phase/advance Endpoint

```python
@router.post("/{project_id}/phase/advance")
async def advance_phase(
    project_id: str,
    request: AdvancePhaseRequest,  # Contains: confirm (bool)
    current_user: CurrentUser = Depends(get_current_user),
    orchestrator: APIOrchestrator = Depends(get_orchestrator),
    db: Session = Depends(get_db)
):
    """
    Advance project to next phase.

    Flow:
    1. Get maturity score
    2. Show warning if < 20%
    3. Ask confirmation if low
    4. Update phase
    5. Clear pending questions
    6. Emit WebSocket event
    """
    try:
        project = db.query(Project).filter_by(project_id=project_id).first()
        current_phase = project.phase

        # Get maturity assessment
        maturity_response = await orchestrator.agents["quality_controller"].verify_advancement(
            current_phase=current_phase,
            specs_collected=project.context.__dict__,
            conversation_quality={"length": len(project.conversation_history)},
            project_context=project.context.__dict__
        )

        maturity = maturity_response.get("maturity_score", 0)

        # Check if needs confirmation
        if maturity < 20 and not request.confirm:
            return {
                "status": "requires_confirmation",
                "maturity_score": maturity,
                "message": f"Phase only {maturity}% complete. Are you sure?",
                "warnings": maturity_response.get("warnings", [])
            }

        # Advance phase
        phase_order = ["discovery", "analysis", "design", "implementation"]
        current_idx = phase_order.index(current_phase)
        if current_idx < len(phase_order) - 1:
            next_phase = phase_order[current_idx + 1]
            project.phase = next_phase
            project.phase_maturity[next_phase] = 0
            project.pending_questions = []  # Clear pending for new phase

        db.commit()

        # Emit WebSocket event
        await emit_event(
            event="PHASE_ADVANCED",
            project_id=project_id,
            data={
                "from_phase": current_phase,
                "to_phase": project.phase,
                "final_maturity": maturity
            }
        )

        return {
            "status": "success",
            "message": f"Advanced to {project.phase}",
            "new_phase": project.phase,
            "previous_maturity": maturity
        }
    except Exception as e:
        logger.error(f"Error advancing phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PHASE 5: KNOWLEDGE BASE INTEGRATION (Week 4)

### 5.1 Enhance vector_db.search_similar_adaptive()

**File**: `backend/src/socrates_api/vector_db.py` (or vector store implementation)

```python
class VectorDatabase:
    async def search_similar_adaptive(
        self,
        query: str,
        strategy: str = "auto",
        phase: Optional[str] = None,
        question_number: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Adaptive knowledge base search with strategy selection.
        """
        # Determine strategy if auto
        if strategy == "auto":
            if phase in ["discovery", "analysis"] and (question_number or 1) < 5:
                strategy = "snippet"
            else:
                strategy = "full"

        # Perform search
        results = await self._search_embeddings(query, top_k=10)

        # Filter based on strategy
        if strategy == "snippet":
            chunks = results[:3]  # Top 3
        elif strategy == "full":
            chunks = results[:5]  # Top 5

        # Format results
        formatted = []
        for result in chunks:
            formatted.append({
                "content": result.content,
                "source": result.document_name,
                "section": result.section_name,
                "relevance_score": result.score,
                "start_line": result.start_line,
                "end_line": result.end_line
            })

        return formatted
```

---

### 5.2 DocumentUnderstandingService Integration

**File**: `backend/src/socrates_api/services/document_understanding.py` (NEW)

```python
class DocumentUnderstandingService:
    async def analyze_documents(
        self,
        documents: List[Dict[str, str]],
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze imported documents for alignment with project goals.
        """
        analysis = {
            "documents_analyzed": [],
            "summaries": {},
            "alignment": {
                "score": 0,
                "covered_areas": [],
                "gaps": [],
                "recommendations": []
            }
        }

        for doc in documents:
            doc_name = doc.get("name", "unknown")
            doc_content = doc.get("content", "")

            # Summarize document
            summary = await self._summarize_document(doc_content)

            # Extract key points
            key_points = await self._extract_key_points(doc_content)

            # Extract topics
            topics = await self._extract_topics(doc_content)

            # Calculate relevance
            relevance = await self._calculate_relevance(
                doc_content,
                project_context
            )

            analysis["documents_analyzed"].append(doc_name)
            analysis["summaries"][doc_name] = {
                "summary": summary,
                "complexity_level": self._assess_complexity(doc_content),
                "word_count": len(doc_content.split()),
                "key_points": key_points,
                "main_topics": topics,
                "relevance": relevance
            }

            # Accumulate alignment gaps
            analysis["alignment"]["gaps"].extend(relevance.get("gaps", []))
            analysis["alignment"]["covered_areas"].extend(relevance.get("covered", []))

        # Overall alignment score
        if analysis["summaries"]:
            scores = [
                s["relevance"].get("score", 0.5)
                for s in analysis["summaries"].values()
            ]
            analysis["alignment"]["score"] = sum(scores) / len(scores)

        return analysis

    async def _summarize_document(self, content: str) -> str:
        """Summarize document using Claude."""
        # Call Claude to summarize
        pass

    async def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from document."""
        # Call Claude to extract key points
        pass

    async def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics from document."""
        # Call Claude to extract topics
        pass

    async def _calculate_relevance(
        self,
        doc_content: str,
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate document relevance to project."""
        # Compare document content to project goals
        # Return score, covered areas, gaps
        pass
```

---

## PHASE 6: LEARNING ANALYTICS (Week 4)

### 6.1 Implement LearningAgent Integration

**File**: `backend/src/socrates_api/services/learning_agent.py`

```python
class LearningAgent:
    async def track_question_effectiveness(
        self,
        user_id: str,
        question_id: str,
        question_text: str,
        user_role: str,
        phase: str,
        answer_text: str,
        specs_extracted: Dict[str, Any],
        answer_quality: float,
        time_to_answer: int
    ) -> Dict[str, Any]:
        """
        Track question effectiveness for continuous improvement.
        """
        analytics_entry = {
            "user_id": user_id,
            "question_id": question_id,
            "question_text": question_text,
            "user_role": user_role,
            "phase": phase,
            "answer_length": len(answer_text),
            "specs_extracted_count": len(specs_extracted),
            "specs_extracted": list(specs_extracted.keys()),
            "answer_quality_score": answer_quality,
            "time_to_answer_seconds": time_to_answer,
            "timestamp": datetime.now().isoformat(),
            "phase_progression": f"{phase}_q{self._get_question_number(question_id)}"
        }

        # Store in database
        await self._store_analytics(analytics_entry)

        # Calculate effectiveness metrics
        spec_extraction_rate = len(specs_extracted) / max(len(answer_text) / 100, 1)

        return {
            "status": "success",
            "effectiveness_metrics": {
                "question_was_useful": answer_quality > 0.7,
                "answer_completeness": answer_quality,
                "spec_extraction_rate": spec_extraction_rate
            }
        }

    async def _store_analytics(self, entry: Dict[str, Any]) -> None:
        """Store analytics in database for later analysis."""
        # Store in learning_analytics table
        pass
```

---

## PHASE 7: FRONTEND INTEGRATION (Week 5)

### 7.1 Update Frontend Chat Component

**File**: `socrates-frontend/src/components/SocraticChat.tsx`

**Key Changes:**

```typescript
// NEW: Manage pending question and answer state
const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
const [showSuggestions, setShowSuggestions] = useState(false);
const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

// Load question on mount
useEffect(() => {
  loadQuestion();
}, [projectId]);

async function loadQuestion() {
  const response = await projectsAPI.getQuestion(projectId);
  setCurrentQuestion(response.question);
}

async function submitAnswer() {
  // Send answer for processing
  const response = await projectsAPI.sendMessage(
    projectId,
    currentQuestion.id,
    answerText
  );

  // Handle conflicts if any
  if (response.conflicts?.length > 0) {
    showConflictModal(response.conflicts);
  }

  // Show next question or phase prompt
  if (response.next_action === "phase_complete") {
    showPhaseCompletePrompt();
  } else {
    loadQuestion();  // Get next question
  }
}

async function loadSuggestions() {
  const response = await projectsAPI.getSuggestions(
    projectId,
    currentQuestion.id
  );
  setSuggestions(response.suggestions);
  setShowSuggestions(true);
}

function skipQuestion() {
  projectsAPI.skipQuestion(projectId, currentQuestion.id);
  loadQuestion();
}
```

---

## IMPLEMENTATION SEQUENCE

### Week 1-2: Foundation
1. Restructure APIOrchestrator with context gathering
2. Add multi-agent coordination methods
3. Update orchestrator initialization

### Week 2-3: Endpoints
1. Redesign /chat/question endpoint
2. Redesign /chat/message endpoint
3. Add /chat/suggestions endpoint
4. Add /chat/skip endpoint
5. Add /chat/reopen endpoint

### Week 3: Conflict Resolution
1. Implement conflict detection flow
2. Add /conflicts/resolve endpoint
3. Test conflict handling

### Week 3-4: Phase Advancement
1. Implement phase advancement flow
2. Add /phase/advance endpoint
3. Add rollback capability
4. Test with maturity checks

### Week 4: Knowledge Base
1. Enhance vector_db.search_similar_adaptive()
2. Implement DocumentUnderstandingService
3. Integrate into question generation

### Week 4: Analytics
1. Implement LearningAgent tracking
2. Add analytics storage
3. Create analytics queries

### Week 5: Frontend
1. Update chat component
2. Add suggestions UI
3. Add skip/reopen UI
4. Add conflict modal
5. Add phase advancement prompt

---

## TESTING STRATEGY

### Unit Tests
- Context gathering methods
- KB strategy selection
- Spec extraction
- Conflict detection
- Maturity calculation

### Integration Tests
- Full question generation flow
- Complete answer processing
- Suggestion generation
- Phase advancement
- Conflict resolution

### End-to-End Tests
- New user → discovery questions → analysis → design → implementation
- Skip/reopen workflow
- Conflict detection and resolution
- Phase advancement with warnings

---

## ROLLOUT STRATEGY

1. **Internal Testing** (Week 5-6)
   - Test with small team
   - Verify all flows work
   - Gather feedback

2. **Beta Release** (Week 7)
   - Release to beta testers
   - Monitor for issues
   - Collect usage data

3. **Production Release** (Week 8)
   - Release to all users
   - Gradual rollout
   - Monitor performance

---

## ROLLBACK PLAN

If issues arise:
1. Keep monolithic branch as fallback
2. Implement feature flags for new components
3. Can revert endpoints individually
4. Database migrations are backwards compatible

