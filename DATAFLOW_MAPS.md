# Complete Data Flow Maps - Socratic Dialogue System

## 1. QUESTION GENERATION FLOW

### Entry Point
- **API Endpoint**: `POST /projects/{project_id}/chat/question`
- **Handler**: `get_question()` in `projects_chat.py` (lines 595-782)

### Flow Diagram
```
GET_QUESTION
    ├─ 1. Check pending_questions for unanswered questions
    │  ├─ YES → Return first unanswered question immediately
    │  │        No new generation needed
    │  │        Status: existing=True
    │  └─ NO → Proceed to generate new question
    │
    ├─ 2. Gather Context for Question Generation
    │  ├─ Get current project state (phase, goals, specs)
    │  ├─ Generate project summary via ContextAnalyzer agent
    │  ├─ Get recent conversation history (last 4 messages)
    │  ├─ Extract previously asked questions in current phase
    │  └─ Determine user role (from project.get_member_role)
    │
    ├─ 3. Adaptive Knowledge Base Loading Strategy
    │  ├─ Analyze phase and conversation context
    │  ├─ Decision Logic:
    │  │  ├─ Early phases (discovery) + few questions → "snippet" (3 chunks, fast)
    │  │  ├─ Later phases (design, impl) + many questions → "full" (5 chunks, comprehensive)
    │  │  └─ Cache strategy per phase to reduce vector_db calls
    │  ├─ Call: vector_db.search_similar_adaptive(query, strategy)
    │  └─ Return: Document chunks with alignment score
    │
    ├─ 4. Document Understanding Integration
    │  ├─ Analyze imported documents (if present)
    │  ├─ Generate summaries and key points
    │  ├─ Compare against project goals
    │  ├─ Identify alignment gaps and opportunities
    │  └─ Generate match score (0-100%)
    │
    ├─ 5. Call SocraticCounselor Agent
    │  ├─ Input Parameters:
    │  │  ├─ project_context (goals, requirements, tech_stack, constraints)
    │  │  ├─ phase (discovery, analysis, design, implementation)
    │  │  ├─ recent_messages (last 4 conversation items)
    │  │  ├─ previously_asked_questions (to avoid repetition)
    │  │  ├─ knowledge_base_chunks (3-5 relevant document sections)
    │  │  ├─ document_understanding (summaries, gaps, alignment)
    │  │  ├─ user_role (lead, creator, specialist, analyst, coordinator)
    │  │  ├─ code_structure (if code present)
    │  │  └─ phase_focus_areas (specific areas to explore this phase)
    │  │
    │  ├─ Processing (SocraticCounselor._generate_dynamic_question):
    │  │  ├─ Build comprehensive prompt with all context
    │  │  ├─ Include role-specific focus areas
    │  │  ├─ Include previous questions to avoid duplicates
    │  │  ├─ Call Claude API with full context
    │  │  └─ Parse single question from response
    │  │
    │  └─ Output: Single question text + metadata
    │
    ├─ 6. Create Question Entry
    │  ├─ Structure:
    │  │  {
    │  │    "id": "q_abc123",
    │  │    "question": "What is your main goal?",
    │  │    "phase": "discovery",
    │  │    "status": "unanswered",
    │  │    "created_at": "2024-01-01T10:00:00",
    │  │    "answer": None,
    │  │    "answered_at": None,
    │  │    "skipped_at": None
    │  │  }
    │  └─ Store in project.pending_questions
    │
    ├─ 7. Track Analytics
    │  ├─ Log question generation
    │  ├─ Record generation timestamp
    │  ├─ Track KB strategy used (snippet vs full)
    │  └─ Store phase and role context
    │
    └─ 8. Return Response
       ├─ Question text
       ├─ Question ID
       ├─ Phase
       ├─ Metadata for frontend
       └─ Suggestions (optional, separate endpoint)
```

### Key Parameters

| Parameter | Source | Purpose |
|-----------|--------|---------|
| project_context | ProjectContext | Goals, requirements, constraints, tech_stack |
| phase | Project.phase | Discovery/Analysis/Design/Implementation |
| recent_messages | conversation_history | Last 4 messages for context |
| previously_asked | pending_questions + asked_questions | Avoid repeating questions |
| knowledge_chunks | vector_db.search_similar() | Document context for grounding |
| document_understanding | DocumentUnderstandingService | Alignment analysis |
| user_role | project.get_member_role(user_id) | Lead/Creator/Specialist/Analyst/Coordinator |

### Decision Logic

**When to Return Existing vs Generate New:**
```python
if pending_questions exists AND has unanswered:
    return first_unanswered
    # User can continue answering at their own pace
    # No forced progression
else:
    generate_new_question
    # Only when all pending are answered/skipped
```

**Knowledge Base Strategy Selection:**
```python
if phase in [discovery, analysis] AND question_number < 5:
    strategy = "snippet"  # 3 chunks, faster
elif phase in [design, implementation] OR question_number >= 5:
    strategy = "full"     # 5 chunks, comprehensive
else:
    strategy = "snippet"  # default safe choice
```

---

## 2. ANSWER PROCESSING FLOW

### Entry Point
- **API Endpoint**: `POST /projects/{project_id}/chat/message`
- **Handler**: `send_message()` in `projects_chat.py` (lines 1075-1095)

### Flow Diagram
```
SEND_MESSAGE (user answer to question)
    ├─ 1. Find Current Question Being Answered
    │  ├─ Search pending_questions for status="unanswered"
    │  ├─ Validate question exists
    │  └─ Store question_id and phase for later use
    │
    ├─ 2. Add to Conversation History
    │  ├─ Structure:
    │  │  {
    │  │    "timestamp": "2024-01-01T10:05:00",
    │  │    "type": "user",
    │  │    "content": "User's answer",
    │  │    "phase": "discovery",
    │  │    "author": "user_id",
    │  │    "question_id": "q_abc123"  # Link to question
    │  │  }
    │  └─ Persist to database
    │
    ├─ 3. Extract Specifications (Specs Extraction)
    │  ├─ Call SocraticCounselor._extract_specs_from_response
    │  ├─ Claude analyzes answer for:
    │  │  ├─ Goals mentioned
    │  │  ├─ Requirements stated
    │  │  ├─ Technology choices
    │  │  ├─ Constraints identified
    │  │  └─ Assumptions made
    │  ├─ Return structure:
    │  │  {
    │  │    "goals": [...],
    │  │    "requirements": [...],
    │  │    "tech_stack": [...],
    │  │    "constraints": [...],
    │  │    "confidence": 0.95  # Quality metric
    │  │  }
    │  └─ Store in project.specs_extracted[question_id]
    │
    ├─ 4. Mark Question as ANSWERED (CRITICAL TIMING)
    │  ├─ Update pending_questions entry:
    │  │  {
    │  │    "status": "answered",
    │  │    "answered_at": "2024-01-01T10:05:30",
    │  │    "answer": "User's full answer text"
    │  │  }
    │  └─ Also update in asked_questions for permanent history
    │  └─ NOTE: This happens BEFORE conflict detection
    │     so conflicts don't block question progression
    │
    ├─ 5. Detect Conflicts
    │  ├─ Call conflict_detector agent
    │  ├─ Compare new_specs with existing project.specs
    │  ├─ Conflict exists when:
    │  │  ├─ Previous answer said "use Python"
    │  │  └─ New answer says "use Java"
    │  │  OR
    │  │  ├─ Previous answer said "10 users"
    │  │  └─ New answer says "10 million users"
    │  ├─ Return structure:
    │  │  {
    │  │    "conflicts_found": [
    │  │      {
    │  │        "type": "tech_stack",
    │  │        "existing": "Python",
    │  │        "new": "Java",
    │  │        "field": "backend_language"
    │  │      }
    │  │    ]
    │  │  }
    │  └─ Store conflicts in project.pending_conflicts
    │
    ├─ 6. Update Project Maturity
    │  ├─ Call QualityController.update_after_response
    │  ├─ Input: specs_extracted, question_quality, answer_length
    │  ├─ Output: updated maturity_percentage for current phase
    │  ├─ Logic:
    │  │  ├─ Count extracted specs as progress
    │  │  ├─ Evaluate spec quality (confidence score)
    │  │  ├─ Consider answer comprehensiveness
    │  │  └─ Calculate phase completion % (0-100%)
    │  └─ Store in project.phase_maturity[phase]
    │
    ├─ 7. Check Phase Completion
    │  ├─ If maturity >= 100%:
    │  │  ├─ Phase is complete
    │  │  ├─ Ask user: "Advance to next phase?" or "Enrich this phase further?"
    │  │  └─ User chooses action
    │  └─ Else:
    │      └─ Continue with next question
    │
    ├─ 8. Track Question Effectiveness
    │  ├─ Call LearningAgent.track_question_effectiveness
    │  ├─ Record:
    │  │  ├─ user_id
    │  │  ├─ question_id
    │  │  ├─ user_role
    │  │  ├─ phase
    │  │  ├─ answer_length (chars or word count)
    │  │  ├─ specs_extracted_count
    │  │  ├─ answer_quality_score
    │  │  └─ time_to_answer (seconds)
    │  └─ Store in learning_analytics database
    │
    ├─ 9. Generate Response
    │  ├─ Summarize key specs extracted
    │  ├─ Acknowledge specs captured
    │  ├─ If conflicts exist: show conflict modal separately
    │  └─ Prepare for next question or phase advancement prompt
    │
    └─ 10. Return Response
       ├─ Confirmation of specs extracted
       ├─ Updated maturity %
       ├─ Phase completion status
       ├─ Conflicts (if any) for separate handling
       └─ Prompt for next action (continue or advance)
```

### Critical Timing Notes

**Question Marked as ANSWERED BEFORE conflict detection:**
- This ensures user can resolve conflicts without re-answering question
- Conflicts are metadata to resolve, not blockers to progression
- User sees conflicts separately, doesn't need to change answer

**Specs Storage Structure:**
```python
project.specs_extracted = {
    "q_abc123": {  # By question ID
        "goals": ["Build web app"],
        "requirements": ["User auth"],
        "tech_stack": ["Python", "React"],
        "constraints": ["Budget $5k"],
        "confidence": 0.95,
        "extracted_at": "2024-01-01T10:05:30"
    }
}
```

---

## 3. ANSWER SUGGESTIONS FLOW

### Entry Point
- **API Endpoint**: `POST /projects/{project_id}/chat/suggestions`
- **Handler**: `get_suggestions()` in `projects_chat.py`

### Flow Diagram
```
GET_SUGGESTIONS (for current question)
    ├─ 1. Validate Current Question
    │  ├─ Find pending_questions entry with status="unanswered"
    │  ├─ Validate question exists
    │  └─ Store question text for prompt
    │
    ├─ 2. Gather Suggestion Context
    │  ├─ Project context (goals, phase, tech_stack)
    │  ├─ User role (lead, creator, specialist, analyst, coordinator)
    │  ├─ Recent conversation (last 2-3 messages)
    │  ├─ Question category (if available from metadata)
    │  └─ Phase-specific focus areas
    │
    ├─ 3. Generate DIVERSE Suggestions
    │  ├─ Call Claude with emphasis on DIFFERENT angles:
    │  │  ├─ "Provide 3-5 suggestions that are diverse in approach"
    │  │  ├─ "Each suggestion should explore a different angle:"
    │  │  │  ├─ Different methodology or framework
    │  │  │  ├─ Different perspective or viewpoint
    │  │  │  ├─ Different scope or depth level
    │  │  │  └─ Different approach or strategy
    │  │  └─ "Do NOT provide variations on the same suggestion"
    │  │
    │  ├─ Prompt Structure:
    │  │  {
    │  │    "current_question": "What is your main goal?",
    │  │    "project_context": {...},
    │  │    "user_role": "lead",
    │  │    "phase": "discovery",
    │  │    "conversation_history": [...],
    │  │    "instruction": "Provide diverse suggestions, not variations"
    │  │  }
    │  │
    │  ├─ Processing:
    │  │  ├─ Call Claude with diverse-emphasis prompt
    │  │  ├─ Parse numbered suggestions from response
    │  │  ├─ Validate count (3-5)
    │  │  └─ Return formatted suggestions
    │  │
    │  └─ Return structure:
    │     [
    │       {
    │         "id": "suggestion_1",
    │         "text": "First suggestion focusing on methodology",
    │         "approach": "methodology",
    │         "rationale": "Why this approach"
    │       },
    │       {
    │         "id": "suggestion_2",
    │         "text": "Second suggestion focusing on perspective",
    │         "approach": "perspective",
    │         "rationale": "Why this perspective"
    │       },
    │       ...
    │     ]
    │
    ├─ 4. Fallback Suggestions (If Claude Fails)
    │  ├─ Per-phase fallback templates:
    │  │  ├─ DISCOVERY:
    │  │  │  ├─ "Describe the problem you're solving in detail"
    │  │  │  ├─ "Who are your target users or stakeholders?"
    │  │  │  └─ "What are the key challenges you're facing?"
    │  │  │
    │  │  ├─ ANALYSIS:
    │  │  │  ├─ "Break down the requirements into smaller components"
    │  │  │  ├─ "What are the technical constraints you need to consider?"
    │  │  │  └─ "How would you prioritize these requirements?"
    │  │  │
    │  │  ├─ DESIGN:
    │  │  │  ├─ "Sketch out the high-level architecture or flow"
    │  │  │  ├─ "What design patterns would be appropriate here?"
    │  │  │  └─ "How would you organize the system components?"
    │  │  │
    │  │  └─ IMPLEMENTATION:
    │  │     ├─ "What's the first feature or module you'd implement?"
    │  │     ├─ "What technologies would you use for this?"
    │  │     └─ "How would you test this implementation?"
    │  │
    │  └─ Return pre-defined suggestions
    │
    └─ 5. Return Response
       ├─ Array of suggestions
       ├─ Approach type for each
       ├─ Rationale for diversity
       └─ Optional: Confidence score
```

### Key Distinctions

**Suggestions are NOT variations on same answer - they are DIVERSE approaches:**

**BAD (Variations):**
- "Build a web app"
- "Create a web application"
- "Develop a web-based platform"
← All same approach, different wording

**GOOD (Diverse):**
- "Describe the business problem you're trying to solve" (methodology: problem-first)
- "Who are your target users and what do they need?" (methodology: user-first)
- "What constraints or requirements drive your solution?" (methodology: constraint-driven)
- "What similar solutions exist and what would make yours different?" (methodology: competitive analysis)
← Each explores fundamentally different angle

---

## 4. PHASE ADVANCEMENT FLOW

### Entry Point
- **User Action**: "Advance to next phase?" prompt at phase completion (100% maturity)
- **Handler**: `advance_phase()` in `projects_chat.py`

### Flow Diagram
```
ADVANCE_PHASE
    ├─ 1. Get Current Phase Maturity
    │  ├─ Call QualityController.verify_advancement
    │  ├─ Input: current_phase, specs_collected, conversation_quality
    │  ├─ Output: maturity_score (0-100%), readiness_assessment
    │  └─ Store: maturity_percentage, readiness_reasons
    │
    ├─ 2. Show Advancement Prompt to User
    │  ├─ Display maturity score (e.g., "Discovery phase is 85% complete")
    │  ├─ If maturity >= 80%:
    │  │  ├─ Show positive prompt
    │  │  ├─ "Ready to move to Analysis phase?"
    │  │  ├─ Suggest what they've achieved
    │  │  └─ Ask: "Advance or continue enriching Discovery?"
    │  │
    │  ├─ If 20% <= maturity < 80%:
    │  │  ├─ Show warning
    │  │  ├─ "Discovery phase is only X% complete"
    │  │  ├─ Show what's missing (e.g., "Need clearer constraints")
    │  │  └─ Ask: "Continue enriching or advance anyway?"
    │  │
    │  └─ If maturity < 20%:
    │     ├─ Show strong warning
    │     ├─ "Recommend continuing with Discovery"
    │     ├─ List critical gaps
    │     └─ Require confirmation to advance
    │
    ├─ 3. User Choice
    │  ├─ Option A: Advance to next phase
    │  │  └─ Proceed to step 4
    │  └─ Option B: Continue current phase
    │     └─ Generate next question in current phase
    │
    ├─ 4. Update Project Phase
    │  ├─ Current: project.phase = discovery
    │  ├─ Next: project.phase = analysis
    │  ├─ Update: project.phase_maturity[discovery] = final_maturity
    │  ├─ Initialize: project.phase_maturity[analysis] = 0
    │  └─ Clear: project.pending_questions (start fresh questions)
    │
    ├─ 5. Emit PHASE_ADVANCED Event
    │  ├─ WebSocket broadcast to all project members
    │  ├─ Event structure:
    │  │  {
    │  │    "event": "PHASE_ADVANCED",
    │  │    "project_id": "proj_123",
    │  │    "from_phase": "discovery",
    │  │    "to_phase": "analysis",
    │  │    "timestamp": "2024-01-01T10:30:00",
    │  │    "direction": "forward",
    │  │    "final_maturity": 0.95
    │  │  }
    │  └─ All clients update UI to show new phase
    │
    ├─ 6. Reset Question Context
    │  ├─ Clear pending_questions (all questions from old phase)
    │  ├─ Keep asked_questions for history
    │  ├─ Initialize new phase context
    │  └─ Next question will be first of new phase
    │
    └─ 7. Return Response
       ├─ Confirmation of phase change
       ├─ New phase name and focus areas
       ├─ Prompt to start new phase
       └─ First question of new phase ready
```

### Phase Rollback Option

**User can go backward if needed:**
```
ROLLBACK_PHASE
    ├─ User clicks "Go back to Discovery"
    ├─ project.phase = previous_phase
    ├─ Emit PHASE_ADVANCED event with direction="backward"
    ├─ Restore pending_questions from backup or regenerate
    └─ Allow re-exploration of earlier phase
```

---

## 5. QUESTION LIFECYCLE FLOW

### 5A. SKIP QUESTION

```
SKIP_QUESTION (user wants to skip without answering)
    ├─ 1. Find Current Question
    │  ├─ Search pending_questions for status="unanswered"
    │  └─ Validate exists
    │
    ├─ 2. Update Question Status
    │  ├─ Set: status = "skipped"
    │  ├─ Set: skipped_at = current_timestamp
    │  ├─ Keep: answer = None (no answer provided)
    │  └─ Persist to database
    │
    ├─ 3. Continue to Next Question
    │  ├─ Check if other unanswered questions exist
    │  ├─ If YES: return next unanswered question
    │  └─ If NO: generate new question
    │
    └─ 4. Return Response
       ├─ Confirmation question was skipped
       └─ Next question to answer
```

### 5B. REOPEN QUESTION

```
REOPEN_QUESTION (user wants to answer skipped question later)
    ├─ 1. Find Skipped Question
    │  ├─ Search pending_questions for status="skipped"
    │  ├─ Match by question_id from frontend
    │  └─ Validate exists
    │
    ├─ 2. Revert to Unanswered
    │  ├─ Set: status = "unanswered"
    │  ├─ Clear: skipped_at = None
    │  ├─ Keep: answer = None
    │  └─ Persist to database
    │
    ├─ 3. Return Question
    │  ├─ Return the reopened question
    │  ├─ Frontend shows question for answering
    │  └─ User can now answer it
    │
    └─ 4. Flow continues as normal answer
       └─ When answered: Answer Processing Flow (section 2)
```

### Question States Diagram

```
┌─────────────┐
│ UNANSWERED  │  (Initial state, waiting for user)
└─────────────┘
      │
      ├─→ ANSWERED ────────→ Specs extracted
      │   (answered_at set)   Maturity updated
      │                       Next question generated
      │
      └─→ SKIPPED ──────────→ User continues without answering
          (skipped_at set)    Can be reopened later
                              │
                              └─→ UNANSWERED (reopened)
                                  Returns to answer
```

---

## 6. DOCUMENT UNDERSTANDING FLOW

### Entry Point
- **API Endpoint**: `POST /projects/{project_id}/documents/explain`
- **Handler**: `explain_document()` in `knowledge.py`

### Flow Diagram
```
EXPLAIN_DOCUMENT (user asks about imported document)
    ├─ 1. Locate Document
    │  ├─ Search knowledge base for document by name or ID
    │  ├─ Retrieve document content from vector_db
    │  └─ Validate document exists
    │
    ├─ 2. Call DocumentUnderstandingService
    │  ├─ Input: document_content, project_context
    │  ├─ Processing:
    │  │  ├─ Analyze structure and topics
    │  │  ├─ Generate summary (key points, structure)
    │  │  ├─ Extract main topics and concepts
    │  │  ├─ Calculate relevance to project goals
    │  │  ├─ Identify alignment gaps
    │  │  └─ Assess coverage of project needs
    │  │
    │  └─ Output structure:
    │     {
    │       "document_name": "Architecture Guide",
    │       "summary": "Comprehensive guide covering...",
    │       "complexity_level": "intermediate",
    │       "word_count": 5432,
    │       "key_points": [
    │         "Component-based architecture",
    │         "API gateway pattern",
    │         "Microservices deployment"
    │       ],
    │       "main_topics": [
    │         "Architecture",
    │         "Deployment",
    │         "Scalability"
    │       ],
    │       "alignment_score": 0.85,
    │       "gaps_identified": [
    │         "Security best practices",
    │         "Performance testing"
    │       ]
    │     }
    │
    ├─ 3. Search Related Knowledge Chunks
    │  ├─ Use vector_db to find related sections
    │  ├─ Group results by source document
    │  ├─ Limit to 3-5 most relevant chunks
    │  └─ Store as context for explanation
    │
    ├─ 4. Generate Explanation
    │  ├─ Call Claude to generate human-readable explanation
    │  ├─ Include:
    │  │  ├─ What the document is about
    │  │  ├─ Key concepts and practices
    │  │  ├─ How it relates to project
    │  │  ├─ Where it helps and where gaps exist
    │  │  └─ Recommendations for usage
    │  └─ Format as structured sections
    │
    └─ 5. Return Response
       ├─ Document metadata (name, size, complexity)
       ├─ Summary
       ├─ Key points
       ├─ Topics
       ├─ Relevance to project
       └─ Recommendations
```

### Document Integration in Question Generation

**During question generation, documents are integrated:**
```
QUESTION_GENERATION includes document understanding:
    ├─ Retrieve document summaries from cache
    ├─ Extract relevant chunks via vector_db search
    ├─ Identify gaps between document and project goals
    ├─ Include document insights in Claude prompt:
    │  ├─ "We have a guide on Architecture..."
    │  ├─ "The document covers these topics..."
    │  ├─ "These areas are not covered..."
    │  └─ "Based on the document, ask about..."
    ├─ Generate questions grounded in document context
    └─ Questions reference document insights
```

---

## 7. MULTI-AGENT COORDINATION FLOW

### Overview

Agents are called sequentially but coordinated by orchestrator:

```
COMPLETE WORKFLOW (Orchestrator perspective)
    ├─ 1. ContextAnalyzer Agent
    │  ├─ Call: generate_project_summary()
    │  ├─ Input: current project state
    │  ├─ Output: comprehensive context for other agents
    │  └─ Usage: Provided to all other agents
    │
    ├─ 2. DocumentUnderstandingService Agent
    │  ├─ Call: analyze_documents()
    │  ├─ Input: imported documents, project goals
    │  ├─ Output: document summaries, alignment analysis
    │  └─ Usage: Provided to SocraticCounselor
    │
    ├─ 3. SocraticCounselor Agent
    │  ├─ Call: generate_dynamic_question()
    │  ├─ Input: all context from above agents
    │  ├─ Output: single question
    │  └─ Also: extract_specs_from_response(), handle_conflict_detection()
    │
    ├─ 4. QualityController Agent
    │  ├─ Call: update_after_response()
    │  ├─ Input: specs extracted, answer quality
    │  ├─ Output: updated maturity_percentage
    │  ├─ Also: verify_advancement()
    │  └─ Also: get_phase_maturity()
    │
    ├─ 5. LearningAgent
    │  ├─ Call: track_question_effectiveness()
    │  ├─ Input: question_id, user_role, specs_extracted, answer_quality
    │  ├─ Output: analytics recorded
    │  └─ Used for: Improving question quality over time
    │
    └─ Orchestrator Coordinates
       ├─ Manages sequence of agent calls
       ├─ Passes outputs from one agent to next
       ├─ Handles errors and fallbacks
       ├─ Manages caching (KB strategy, document summaries)
       └─ Broadcasts WebSocket events
```

### Agent Responsibilities Matrix

| Agent | Responsibility | When Called | Input | Output |
|-------|----------------|------------|-------|--------|
| ContextAnalyzer | Project summary generation | Before question generation | Project state | Comprehensive context |
| DocumentUnderstanding | Document analysis | Before question generation | Documents, goals | Summaries, alignment, gaps |
| SocraticCounselor | Question generation | On question request | Full context | Single question |
| SocraticCounselor | Specs extraction | After user answer | Answer text | Extracted specs |
| SocraticCounselor | Conflict detection | After specs extraction | New specs, existing specs | Conflicts found |
| QualityController | Maturity calculation | After specs extraction | Specs, answer quality | Maturity % |
| QualityController | Advancement verification | Before phase advance | Phase stats | Readiness assessment |
| LearningAgent | Question effectiveness | After specs extraction | All response data | Analytics recorded |

---

## 8. KNOWLEDGE BASE STRATEGY SELECTION

### Adaptive Loading Decision Tree

```
KNOWLEDGE_BASE_STRATEGY = ?
    │
    ├─ Analyze Phase
    │  ├─ discovery, analysis → consider "snippet"
    │  └─ design, implementation → consider "full"
    │
    ├─ Analyze Conversation Progress
    │  ├─ question_number in phase
    │  ├─ Early questions (1-4) → prefer "snippet"
    │  └─ Later questions (5+) → prefer "full"
    │
    ├─ Check Cache
    │  ├─ If already cached for this phase → use cached strategy
    │  └─ Reduces vector_db calls
    │
    ├─ Decide
    │  ├─ snippet = 3 chunks, fast, overview level
    │  └─ full = 5 chunks, comprehensive, detailed
    │
    └─ Execute
       ├─ vector_db.search_similar_adaptive(query, strategy)
       ├─ Get document chunks
       └─ Pass to SocraticCounselor
```

### Caching Strategy

```
KNOWLEDGE_BASE_CACHE
    │
    ├─ Cache Key: (project_id, phase)
    ├─ Cache Value: {strategy, chunks, last_updated}
    ├─ TTL: Per phase (invalidate when phase changes)
    │
    ├─ Usage:
    │  ├─ First question of phase → compute strategy, cache result
    │  ├─ Subsequent questions → use cached strategy
    │  └─ Phase change → clear cache
    │
    └─ Benefit:
       ├─ Reduces vector_db API calls
       ├─ Consistent strategy within phase
       └─ Faster question generation
```

---

## 9. ERROR HANDLING AND FALLBACKS

### Question Generation Fallback

```
GENERATE_QUESTION fails (Claude timeout, API error, etc.)
    │
    ├─ Catch exception
    ├─ Log error details
    ├─ Fall back to phase-specific default question
    │  ├─ DISCOVERY: "Tell me about your project"
    │  ├─ ANALYSIS: "What are the main requirements?"
    │  ├─ DESIGN: "Describe your architecture"
    │  └─ IMPLEMENTATION: "What will you build first?"
    │
    └─ Return fallback question
```

### Conflict Detection Fallback

```
CONFLICT_DETECTION fails
    │
    ├─ Return empty conflicts array
    ├─ Continue normal flow
    └─ Log warning for debugging
```

### Knowledge Base Loading Fallback

```
VECTOR_DB fails or no chunks found
    │
    ├─ Continue without KB context
    ├─ SocraticCounselor still generates question
    │  (just without document grounding)
    │
    └─ Return valid question with reduced context
```

---

## Summary of Data Flows

| Flow | Trigger | Primary Agent | Output | Next Step |
|------|---------|---------------|--------|-----------|
| Question Generation | User requests question | SocraticCounselor | Single question + ID | Wait for answer or skip |
| Answer Processing | User submits answer | SocraticCounselor + QualityController | Specs extracted, maturity updated | Show conflict modal or next question |
| Answer Suggestions | User clicks "Get suggestions" | Claude | 3-5 diverse suggestions | User picks suggestion to answer |
| Phase Advancement | Phase maturity >= 100% | QualityController | Readiness assessment | User confirms advance or continue |
| Question Skip | User skips question | (State change only) | Question marked skipped | Proceed to next question |
| Question Reopen | User reopens skipped | (State change only) | Question marked unanswered | User answers reopened question |
| Document Explanation | User asks about document | DocumentUnderstanding | Document summary + relevance | Continue with dialog |

