# Technical Specifications - socratic-agents Library Modifications

## Executive Summary

The socratic-agents library currently hardcodes "Generate 3 Socratic questions" behavior. This document specifies the modifications required to support the monolithic Socrates mechanism, which uses single dynamic question generation with full contextual awareness.

**Key Change**: From batch question generation to single dynamic question generation with comprehensive context input.

---

## 1. CURRENT STATE vs REQUIRED STATE

### Current Behavior (Library v1.0)

```python
# Current: Always generates 3 questions as a batch
response = counselor.generate_guiding_questions(
    project_context="Build a web app"
)

# Returns:
{
    "questions": [
        "What is your main goal?",
        "Who are your users?",
        "What technologies will you use?"
    ]
}
```

**Problems:**
1. Ignores user's actual answer (no feedback loop)
2. Generates 3 at once (batch, not dynamic)
3. No context about which question user is answering
4. No knowledge base integration
5. No role awareness
6. No document understanding
7. No conflict detection
8. No maturity tracking
9. No learning analytics

### Required Behavior (Monolithic Pattern)

```python
# New: Generate single question with full context
response = counselor.generate_dynamic_question(
    project_context={...},
    phase="discovery",
    recent_messages=[...],
    previously_asked_questions=[...],
    knowledge_base_chunks=[...],
    document_understanding={...},
    user_role="lead",
    question_number=3
)

# Returns:
{
    "question": "Given that you're targeting enterprise users, what's the biggest pain point you're trying to solve?",
    "metadata": {
        "category": "discovery",
        "target_field": "problem_statement",
        "confidence": 0.92
    }
}
```

**Improvements:**
1. Responds to user's previous answers via recent_messages
2. Single question, dynamically generated
3. Explicitly knows which question number in sequence
4. Grounded in knowledge base documents
5. Role-aware (adjusts for lead vs creator vs specialist)
6. Uses document understanding (gaps, alignment)
7. Prepares for conflict detection
8. Inputs enable maturity tracking
9. Enables learning analytics

---

## 2. API SPECIFICATION

### 2.1 SocraticCounselor.generate_dynamic_question()

#### Signature
```python
def generate_dynamic_question(
    self,
    project_context: Dict[str, Any],
    phase: str,
    recent_messages: List[Dict[str, str]],
    previously_asked_questions: List[str],
    knowledge_base_chunks: List[Dict[str, str]],
    document_understanding: Dict[str, Any],
    user_role: str,
    question_number: int = 1,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    code_structure: Optional[Dict[str, Any]] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| project_context | Dict | Yes | - | Current project goals, requirements, tech_stack, constraints |
| phase | str | Yes | - | Current phase: "discovery", "analysis", "design", "implementation" |
| recent_messages | List | Yes | - | Last 4 messages from conversation history (user + assistant) |
| previously_asked_questions | List | Yes | - | Questions already asked in this phase (to avoid repeats) |
| knowledge_base_chunks | List | Yes | - | Document chunks from vector_db search (3-5 items) |
| document_understanding | Dict | Yes | - | Analysis of imported documents (summaries, gaps, alignment) |
| user_role | str | Yes | "contributor" | User's role: "lead", "creator", "specialist", "analyst", "coordinator" |
| question_number | int | No | 1 | Question number in this phase (affects depth) |
| conversation_history | List | No | None | Full conversation history for context (optional for efficiency) |
| code_structure | Dict | No | None | If code present, AST or structure analysis |
| force_refresh | bool | No | False | Force new generation even if pending question exists |

#### Return Structure

```python
{
    "status": "success" | "error",
    "question": "Actual question text",
    "metadata": {
        "category": "discovery",          # Question type/category
        "target_field": "goals",          # What spec this targets
        "confidence": 0.92,               # Quality metric (0-1)
        "approach": "open-ended",         # Question approach
        "phase": "discovery",
        "question_number": 3,
        "timestamp": "2024-01-01T10:00:00"
    },
    "context_used": {
        "kb_strategy": "snippet",         # "snippet" or "full"
        "document_chunks_count": 3,
        "document_sources": ["Architecture.pdf"],
        "gaps_addressed": ["Security considerations"]
    }
}
```

#### Context Requirements Explained

**project_context**
```python
{
    "goals": ["Build web platform for enterprise"],
    "requirements": ["Real-time collaboration"],
    "tech_stack": ["Python", "React"],
    "constraints": ["Budget $50k", "Launch in 6 months"],
    "existing_specs": {
        "database": "PostgreSQL",
        "deployment": "AWS",
        "scaling": "Horizontal"
    }
}
```

**recent_messages**
```python
[
    {
        "type": "assistant",
        "content": "What is your main goal?",
        "timestamp": "2024-01-01T10:00:00"
    },
    {
        "type": "user",
        "content": "Build a real-time collaboration tool",
        "timestamp": "2024-01-01T10:05:00"
    },
    {
        "type": "assistant",
        "content": "Who are your target users?",
        "timestamp": "2024-01-01T10:10:00"
    },
    {
        "type": "user",
        "content": "Enterprise teams, 5-500 person organizations",
        "timestamp": "2024-01-01T10:15:00"
    }
]
```

**previously_asked_questions**
```python
[
    "What is your main goal?",
    "Who are your target users?",
    "What specific problems will your product solve?"
]
```

**knowledge_base_chunks** (from vector_db.search_similar_adaptive)
```python
[
    {
        "content": "Real-time collaboration requires...",
        "source": "Architecture_Guide.pdf",
        "relevance_score": 0.95,
        "section": "Real-time Patterns"
    },
    {
        "content": "Enterprise deployments need...",
        "source": "Enterprise_Guide.pdf",
        "relevance_score": 0.87,
        "section": "Security"
    },
    {
        "content": "Scaling to 500 concurrent users...",
        "source": "Scaling_Guide.pdf",
        "relevance_score": 0.82,
        "section": "Performance"
    }
]
```

**document_understanding**
```python
{
    "documents_analyzed": ["Architecture_Guide.pdf", "Enterprise_Guide.pdf"],
    "summaries": {
        "Architecture_Guide.pdf": {
            "summary": "Covers system design patterns and architecture approaches",
            "key_points": ["Microservices", "Event-driven", "API-first"],
            "word_count": 5432
        }
    },
    "alignment": {
        "score": 0.85,  # 0-1, how well docs match project goals
        "covered_areas": ["Architecture", "Security"],
        "gaps": ["Performance optimization", "Testing strategies"]
    }
}
```

**user_role** - Influences question approach:
- **"lead"**: Strategic, vision, resource allocation, timeline
- **"creator"**: Implementation, execution, technical decisions
- **"specialist"**: Technical depth, best practices, quality
- **"analyst"**: Research, requirements validation, edge cases
- **"coordinator"**: Dependencies, timelines, team coordination

---

### 2.2 SocraticCounselor.extract_specs_from_response()

#### Signature
```python
def extract_specs_from_response(
    self,
    user_answer: str,
    question: str,
    project_context: Dict[str, Any],
    phase: str
) -> Dict[str, Any]:
```

#### Return Structure

```python
{
    "status": "success",
    "specs": {
        "goals": [
            {
                "text": "Build real-time collaboration platform",
                "confidence": 0.95,
                "extracted_from": "User's answer"
            }
        ],
        "requirements": [
            {
                "text": "Support 500 concurrent users",
                "confidence": 0.92,
                "category": "scalability"
            }
        ],
        "tech_stack": [
            {
                "technology": "PostgreSQL",
                "confidence": 0.88,
                "rationale": "Mentioned by user for data storage"
            }
        ],
        "constraints": [
            {
                "constraint": "Launch in 6 months",
                "confidence": 0.90,
                "type": "timeline"
            }
        ]
    },
    "overall_confidence": 0.91,
    "completeness": 0.78,  # How much of question was answered
    "clarity": 0.85        # How clear the answer was
}
```

---

### 2.3 SocraticCounselor.generate_answer_suggestions()

#### Signature
```python
def generate_answer_suggestions(
    self,
    question: str,
    project_context: Dict[str, Any],
    phase: str,
    user_role: str,
    recent_messages: List[Dict[str, str]],
    diversity_emphasis: bool = True
) -> Dict[str, Any]:
```

#### Return Structure

```python
{
    "status": "success",
    "suggestions": [
        {
            "id": "suggestion_1",
            "text": "Describe the business problem and market opportunity you're addressing",
            "approach": "methodology",
            "angle": "Problem-first approach",
            "rationale": "Helps understand root cause vs symptom"
        },
        {
            "id": "suggestion_2",
            "text": "Who are the key stakeholders and what are their pain points?",
            "approach": "stakeholder",
            "angle": "User-centered approach",
            "rationale": "Essential for product-market fit"
        },
        {
            "id": "suggestion_3",
            "text": "What constraints (budget, timeline, team) drive your approach?",
            "approach": "constraint",
            "angle": "Constraint-driven approach",
            "rationale": "Reveals practical boundaries"
        },
        {
            "id": "suggestion_4",
            "text": "What similar solutions exist and what would make yours different?",
            "approach": "competitive",
            "angle": "Competitive analysis",
            "rationale": "Positions solution in market"
        }
    ],
    "count": 4,
    "diversity_score": 0.92  # How diverse suggestions are
}
```

**Key Requirement:** Suggestions must be DIVERSE in approach, not variations on same answer. Each should explore a fundamentally different angle.

---

### 2.4 SocraticCounselor.detect_conflicts()

#### Signature
```python
def detect_conflicts(
    self,
    new_specs: Dict[str, Any],
    existing_specs: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
```

#### Return Structure

```python
{
    "status": "success",
    "conflicts_found": [
        {
            "conflict_id": "conflict_1",
            "type": "tech_stack",
            "field": "database",
            "existing": {
                "value": "PostgreSQL",
                "source": "q_abc123",  # question_id
                "timestamp": "2024-01-01T09:00:00"
            },
            "new": {
                "value": "MongoDB",
                "source": "q_xyz789",
                "timestamp": "2024-01-01T10:00:00"
            },
            "severity": "high",  # "low", "medium", "high"
            "message": "Database choice changed from PostgreSQL to MongoDB",
            "suggested_resolutions": [
                "Keep PostgreSQL (relational is better for consistency)",
                "Switch to MongoDB (better for document storage)",
                "Use both (polyglot persistence approach)"
            ]
        }
    ],
    "total_conflicts": 1,
    "requires_resolution": True
}
```

**Important Timing:** Conflicts are detected AFTER question is marked answered, so they don't block progression. This is metadata to resolve, not a blocker.

---

## 3. DOCUMENT UNDERSTANDING SERVICE API

### 3.1 DocumentUnderstandingService.analyze_documents()

#### Signature
```python
def analyze_documents(
    self,
    documents: List[Dict[str, str]],
    project_context: Dict[str, Any]
) -> Dict[str, Any]:
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| documents | List | List of {name, content} dicts |
| project_context | Dict | Current project goals, requirements, phase |

#### Return Structure

```python
{
    "status": "success",
    "analysis": {
        "Architecture_Guide.pdf": {
            "summary": "Comprehensive guide covering system design patterns...",
            "complexity_level": "intermediate",  # "beginner", "intermediate", "advanced"
            "word_count": 5432,
            "key_points": [
                "Microservices reduce coupling",
                "Event-driven improves responsiveness",
                "API-first enables integration"
            ],
            "main_topics": [
                "System Architecture",
                "Design Patterns",
                "Performance",
                "Scalability"
            ],
            "relevance": {
                "score": 0.85,  # 0-1, how relevant to project
                "covered_areas": [
                    "Architecture decisions",
                    "Scaling strategies"
                ],
                "gaps": [
                    "Testing strategies",
                    "Security best practices"
                ],
                "recommendations": [
                    "Document covers architecture well, review for design phase",
                    "Consider adding security guide for implementation phase"
                ]
            }
        }
    },
    "total_documents": 1,
    "overall_alignment": 0.85
}
```

---

## 4. QUALITY CONTROLLER API

### 4.1 QualityController.verify_advancement()

#### Signature
```python
def verify_advancement(
    self,
    current_phase: str,
    specs_collected: Dict[str, Any],
    conversation_quality: Dict[str, float],
    project_context: Dict[str, Any]
) -> Dict[str, Any]:
```

#### Return Structure

```python
{
    "status": "success",
    "ready_to_advance": True,  # True/False/Warning
    "maturity_score": 95,  # 0-100%
    "readiness_assessment": {
        "completeness": 95,     # Do we have all needed specs?
        "clarity": 92,          # Are specs clear and specific?
        "consistency": 98,      # No contradictions?
        "depth": 88             # Sufficient detail?
    },
    "missing_elements": [],  # What's still needed if < 100%
    "warnings": [],
    "recommendations": []
}
```

---

## 5. LEARNING AGENT API

### 5.1 LearningAgent.track_question_effectiveness()

#### Signature
```python
def track_question_effectiveness(
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
```

#### Analytics Stored

```python
{
    "analytics": {
        "user_id": "user_123",
        "question_id": "q_abc123",
        "question_text": "What is your main goal?",
        "user_role": "lead",
        "phase": "discovery",
        "answer_length": 245,  # Characters
        "specs_extracted_count": 3,  # How many specs
        "specs_extracted": ["goal_1", "goal_2", "requirement_1"],
        "answer_quality_score": 0.92,
        "time_to_answer_seconds": 125,
        "timestamp": "2024-01-01T10:05:30",
        "phase_progression": "discovery_q3"
    },
    "effectiveness_metrics": {
        "question_was_useful": True,
        "answer_completeness": 0.92,
        "spec_extraction_rate": 1.23  # specs per 100 chars
    }
}
```

---

## 6. KNOWLEDGE BASE INTEGRATION API

### 6.1 VectorDB.search_similar_adaptive()

#### Signature
```python
def search_similar_adaptive(
    self,
    query: str,
    strategy: str = "auto",
    phase: Optional[str] = None,
    question_number: Optional[int] = None
) -> List[Dict[str, str]]:
```

#### Parameters

| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| query | str | - | Search query (the question text) |
| strategy | str | "snippet", "full", "auto" | Loading strategy |
| phase | str | "discovery", "analysis", "design", "impl" | Current phase |
| question_number | int | 1-20+ | Question number for strategy selection |

#### Strategy Behavior

**"snippet"** (Fast, overview):
- Returns top 3 document chunks
- Quick vector search
- For early phase exploration
- Reduces token usage in prompts

**"full"** (Comprehensive):
- Returns top 5 document chunks
- Detailed content
- For later phases needing depth
- More context for Claude

**"auto"**:
- Analyzes phase and question_number
- Selects "snippet" for discovery/analysis or early questions
- Selects "full" for design/implementation or later questions

#### Return Structure

```python
[
    {
        "content": "Real-time collaboration requires careful consideration of...",
        "source": "Architecture_Guide.pdf",
        "section": "Real-time Patterns",
        "relevance_score": 0.95,
        "start_line": 324,
        "end_line": 412
    },
    {
        "content": "Enterprise deployments should consider...",
        "source": "Enterprise_Guide.pdf",
        "section": "Security",
        "relevance_score": 0.87,
        "start_line": 156,
        "end_line": 201
    }
]
```

---

## 7. CONTEXT ANALYZER API

### 7.1 ContextAnalyzer.generate_project_summary()

#### Signature
```python
def generate_project_summary(
    self,
    project_context: Dict[str, Any],
    conversation_history: List[Dict[str, Any]],
    current_phase: str
) -> Dict[str, Any]:
```

#### Return Structure

```python
{
    "status": "success",
    "summary": {
        "project_name": "Collaboration Platform",
        "phase": "discovery",
        "goals": ["Build real-time collaboration tool for enterprises"],
        "target_users": ["Enterprise teams, 5-500 person orgs"],
        "tech_stack": ["Python", "React", "PostgreSQL"],
        "constraints": ["6 month timeline", "$50k budget"],
        "key_decisions_made": ["Real-time via WebSocket", "AWS deployment"],
        "open_questions": ["Offline support needed?", "Mobile app?"],
        "completed_phases": [],
        "current_progress": "Early discovery, 3 of ~8 questions"
    },
    "context_quality": 0.85  # How complete the context is
}
```

---

## 8. INTEGRATION REQUIREMENTS

### 8.1 How Modular Socrates Calls Library

**Current Pattern (Problematic):**
```python
# socrates-agents library always does this
questions = counselor.generate_guiding_questions(
    project_context=context
)  # Returns 3 questions

# Frontend stores all 3, user answers first
# User's answer is ignored when generating next question
```

**Required Pattern (New):**
```python
# Modular Socrates prepares rich context
context = {
    "project_context": project.context,
    "phase": project.phase,
    "recent_messages": conversation_history[-4:],
    "previously_asked": extract_previously_asked(project.pending_questions),
    "knowledge_base_chunks": vector_db.search_similar_adaptive(
        query=project.pending_questions[0].get("question"),
        strategy=determine_kb_strategy(project.phase, question_number)
    ),
    "document_understanding": doc_service.analyze_documents(
        documents=project.knowledge_base,
        project_context=project.context
    ),
    "user_role": project.get_member_role(user_id)
}

# Call single-question generator
response = counselor.generate_dynamic_question(**context)

# Library returns single question, modular Socrates decides next step
# User's answer flows back through complete pipeline
```

---

## 9. ENDPOINT SPECIFICATIONS FOR API ORCHESTRATOR

### 9.1 Endpoint: POST /projects/{project_id}/chat/question

**Request:**
```json
{
    "user_id": "user_123",
    "force_refresh": false
}
```

**Processing:**
1. Get project and conversation history
2. Check for pending unanswered questions
   - If exists: return first unanswered
   - If not: proceed to generate
3. Gather all context (KB, documents, previous questions, role)
4. Call counselor.generate_dynamic_question(context)
5. Store question in project.pending_questions
6. Return response

**Response:**
```json
{
    "status": "success",
    "question": {
        "id": "q_abc123",
        "text": "Given that you're targeting enterprise users...",
        "phase": "discovery",
        "question_number": 3,
        "metadata": {
            "category": "discovery",
            "target_field": "problem_statement"
        }
    },
    "context": {
        "phase_maturity": 45,
        "questions_in_phase": 3,
        "can_skip": true,
        "can_reopen_previous": false
    }
}
```

---

### 9.2 Endpoint: POST /projects/{project_id}/chat/message

**Request:**
```json
{
    "question_id": "q_abc123",
    "answer": "User's answer text",
    "user_id": "user_123"
}
```

**Processing:**
1. Find pending question (validate matches request)
2. Add answer to conversation_history
3. Call counselor.extract_specs_from_response(answer, question, context)
4. Mark question as answered in pending_questions
5. Call conflict_detector.detect_conflicts(new_specs, existing_specs)
6. Call quality_controller.update_after_response(specs, answer_quality)
7. Call learning_agent.track_question_effectiveness(analytics)
8. Check phase completion (maturity >= 100%)
9. Return response with conflicts (if any) for separate modal

**Response:**
```json
{
    "status": "success",
    "specs_extracted": {
        "goals": ["Build real-time collaboration platform"],
        "requirements": ["Support 500 concurrent users"],
        "tech_stack": ["Python", "React"],
        "constraints": ["6 month timeline"]
    },
    "phase_maturity": 65,
    "conflicts": [
        {
            "type": "tech_stack",
            "field": "database",
            "existing": "PostgreSQL",
            "new": "MongoDB",
            "severity": "high"
        }
    ],
    "next_action": "continue"  # or "phase_complete"
}
```

---

### 9.3 Endpoint: POST /projects/{project_id}/chat/suggestions

**Request:**
```json
{
    "question_id": "q_abc123",
    "user_id": "user_123"
}
```

**Processing:**
1. Get current pending question
2. Gather context (project, role, recent messages, phase)
3. Call counselor.generate_answer_suggestions(context)
4. Return diverse suggestions (not variations)

**Response:**
```json
{
    "status": "success",
    "suggestions": [
        {
            "id": "sugg_1",
            "text": "Describe the business problem...",
            "approach": "methodology",
            "angle": "Problem-first"
        },
        {
            "id": "sugg_2",
            "text": "Who are the stakeholders...",
            "approach": "stakeholder",
            "angle": "User-centered"
        }
    ]
}
```

---

## 10. LIBRARY MODIFICATION CHECKLIST

- [ ] Modify `_generate_guiding_questions()` to `generate_dynamic_question()`
- [ ] Change from batch (3 questions) to single question generation
- [ ] Add all required parameters (phase, recent_messages, KB chunks, etc.)
- [ ] Create comprehensive prompt that incorporates all context
- [ ] Add metadata output to returned question
- [ ] Implement `extract_specs_from_response()` for spec extraction
- [ ] Implement `generate_answer_suggestions()` with diversity emphasis
- [ ] Implement `detect_conflicts()` with conflict detection logic
- [ ] Update error handling and fallback questions
- [ ] Add role-aware question generation
- [ ] Add document integration in prompts
- [ ] Create adapter layer in orchestrator.py for compatibility
- [ ] Update all relevant endpoints in projects_chat.py
- [ ] Add learning analytics integration
- [ ] Update documentation and examples

---

## 11. BACKWARDS COMPATIBILITY STRATEGY

**Option 1: Major Version Bump (Recommended)**
- Release as socratic-agents v2.0
- Breaking change (library API changes significantly)
- Full migration guide provided
- Old API can be soft-deprecated

**Option 2: Compatibility Layer**
- Keep old API as wrapper around new API
- New code uses new API directly
- Old code continues to work (at cost of some features)
- Phase out old API over time

**Recommendation:** Go with Option 1 (Major Version) because:
1. Old API fundamentally doesn't support required features
2. Attempting to maintain compatibility adds complexity
3. Modular Socrates redesign requires full API change anyway
4. Clean break is better than confusing wrapper

---

## 12. TESTING SPECIFICATIONS

### Unit Tests Required

```python
# Test single question generation
def test_generate_dynamic_question_with_full_context():
    # Verify question is generated (not 3)
    # Verify metadata included
    # Verify context was considered

# Test spec extraction
def test_extract_specs_from_answer():
    # Verify specs correctly extracted
    # Verify confidence scores
    # Verify no missed specs

# Test suggestion generation
def test_generate_diverse_suggestions():
    # Verify 3-5 suggestions returned
    # Verify suggestions are diverse
    # Verify no variation duplicates

# Test conflict detection
def test_detect_conflicts_comprehensive():
    # Verify conflicts found when exist
    # Verify no false positives
    # Verify severity assessment

# Test KB strategy selection
def test_knowledge_base_strategy_selection():
    # Verify "snippet" for early phases
    # Verify "full" for later phases
    # Verify caching works
```

### Integration Tests Required

```python
# Test full question generation with KB
def test_question_generation_with_knowledge_base():
    # Verify KB chunks included in prompt
    # Verify question is grounded in KB
    # Verify relevance

# Test complete answer flow
def test_complete_answer_processing():
    # Answer question
    # Specs extracted
    # Conflicts detected
    # Maturity updated
    # Analytics tracked

# Test phase progression
def test_phase_advancement_flow():
    # Answer multiple questions
    # Maturity accumulates
    # Phase complete prompt shows
    # Phase advances correctly
```

---

## 13. DOCUMENTATION REQUIREMENTS

- [ ] API Reference for all public methods
- [ ] Migration Guide from v1.0 to v2.0
- [ ] Integration Examples showing how Modular Socrates uses library
- [ ] Context Parameter Guide (what each param is, how to prepare it)
- [ ] Knowledge Base Integration Guide
- [ ] Error Handling Guide
- [ ] Performance Tuning Guide (when to use "snippet" vs "full")
- [ ] Learning Analytics Integration Guide
- [ ] Role-Aware Question Generation Guide

