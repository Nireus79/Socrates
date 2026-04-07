# Comprehensive Analysis: Monolithic-Socrates Agent Implementations

This document provides a detailed analysis of all 22 agent implementations from the Monolithic-Socrates repository.

---

## Table of Contents

1. [Overview](#overview)
2. [Agent Dependency Graph](#agent-dependency-graph)
3. [Critical Infrastructure Agents](#critical-infrastructure-agents)
4. [Supporting Agents](#supporting-agents)
5. [External Dependencies](#external-dependencies)
6. [Data Flow Analysis](#data-flow-analysis)
7. [Configuration Requirements](#configuration-requirements)

---

## Overview

The Monolithic-Socrates system consists of 21 functional agents (plus 1 test file) that work together to provide a Socratic tutoring and project development system. The architecture follows an orchestrator pattern where agents communicate through a central `AgentOrchestrator`.

### Agent Classification

| Category | Agents |
|----------|--------|
| **Infrastructure** | Agent (base), ProjectManagerAgent, KnowledgeManagerAgent |
| **Core Dialogue** | SocraticCounselorAgent, QuestionQueueAgent |
| **Analysis** | ContextAnalyzerAgent, DocumentContextAnalyzer, ConflictDetectorAgent, KnowledgeAnalysisAgent |
| **Document Processing** | DocumentProcessorAgent, NoteManagerAgent, ProjectFileLoader |
| **Code Operations** | CodeGeneratorAgent, CodeValidationAgent |
| **Learning & Quality** | UserLearningAgent, QualityControllerAgent |
| **External Integration** | GitHubSyncHandler, MultiLLMAgent |
| **User & System** | UserManagerAgent, SystemMonitorAgent |

---

## Agent Dependency Graph

```
                                    ┌─────────────────────┐
                                    │  AgentOrchestrator  │
                                    └─────────┬───────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
            ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
            │  Agent (base) │◄───────│  EventEmitter │        │  VectorDB     │
            └───────┬───────┘        └───────────────┘        └───────────────┘
                    │
    ┌───────────────┼───────────────────────────────────────────────┐
    │               │               │               │               │
    ▼               ▼               ▼               ▼               ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ ProjectMgr │ │ SocraticC. │ │ DocProc.   │ │ CodeGen    │ │ QualityCtl │
└──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └────────────┘ └──────┬─────┘
       │              │              │                             │
       │              │              │                             │
       ▼              ▼              ▼                             ▼
┌────────────┐ ┌────────────┐ ┌────────────┐                ┌────────────┐
│ GitManager │ │ ConflictDet│ │ CodeParser │                │MaturityCalc│
└────────────┘ │ ContextAnl │ └────────────┘                │WorkflowOpt │
               │ KnowledgeMg│                               └────────────┘
               └────────────┘
```

---

## Critical Infrastructure Agents

### 1. Agent (base.py)

**Main Class:** `Agent` (Abstract Base Class)

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(name: str, orchestrator: AgentOrchestrator)` | Initialize agent with name and orchestrator reference |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | **Abstract** - Process request synchronously |
| `process_async` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Async wrapper using thread pool |
| `log` | `(message: str, level: str = "INFO") -> None` | Structured logging with event emission |
| `emit_event` | `(event_type: EventType, data: Optional[Dict] = None) -> None` | Domain event emission |
| `suggest_knowledge_addition` | `(content, category, topic, difficulty, reason) -> None` | Suggest knowledge additions |

**Key Capabilities:**
- Abstract base for all agents
- Synchronous and asynchronous processing
- Structured logging via EventType
- Knowledge gap detection and suggestion

**Dependencies:**
- Internal: `EventType`, `AgentOrchestrator`
- External: `asyncio`, `logging`, `abc`, `datetime`

**Data Structures:**
- Request/Response: `Dict[str, Any]`
- Events: `EventType` enum

---

### 2. ProjectManagerAgent (project_manager.py)

**Main Class:** `ProjectManagerAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize with orchestrator |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route to action handlers |
| `_create_project` | `(request: Dict) -> Dict` | Create new project with quota validation |
| `_create_from_github` | `(request: Dict) -> Dict` | Import project from GitHub |
| `_apply_initial_insights` | `(project, insights) -> None` | Apply extracted specs to project |
| `_load_project` | `(request: Dict) -> Dict` | Retrieve project by ID |
| `_save_project` | `(request: Dict) -> Dict` | Persist project with timestamp |
| `_archive_project` | `(request: Dict) -> Dict` | Archive project (owner-only) |
| `_restore_project` | `(request: Dict) -> Dict` | Restore archived project |
| `_delete_project_permanently` | `(request: Dict) -> Dict` | Permanent deletion |
| `_add_collaborator` | `(request: Dict) -> Dict` | Add team member |
| `_update_member_role` | `(request: Dict) -> Dict` | Change member role |
| `_list_collaborators` | `(request: Dict) -> Dict` | List team members |
| `_remove_collaborator` | `(request: Dict) -> Dict` | Remove collaborator |
| `_list_projects` | `(request: Dict) -> Dict` | List user's projects |
| `_validate_github_request` | `(request) -> None` | Validate GitHub import fields |
| `_validate_github_url` | `(git_manager, url) -> None` | Verify GitHub URL format |
| `_clone_repository` | `(git_manager, url) -> str` | Clone repo to temp directory |
| `_extract_repository_metadata` | `(git_manager, path) -> Dict` | Extract repo metadata |
| `_parse_repo_info` | `(url) -> tuple` | Extract owner/name from URL |
| `_get_or_create_user` | `(owner) -> User` | Get or create user account |
| `_validate_subscription` | `(user, owner) -> None` | Check project creation limits |
| `_run_code_validation` | `(path) -> Dict` | Validate project code |
| `_create_project_context` | `(...) -> ProjectContext` | Construct project context |
| `_save_project_files` | `(project_id, path) -> None` | Save files to database |
| `_collect_files_to_save` | `(path) -> List` | Filter files by type/size |
| `_should_save_file` | `(file_path, repo_root) -> bool` | File filter logic |
| `_detect_language` | `(file_path) -> str` | Map extensions to languages |
| `_generate_auto_user_email` | `(username) -> str` | Generate UUID email |
| `_normalize_to_list` | `(value) -> List[str]` | Convert to string list |
| `_update_list_field` | `(current_list, new_items) -> List` | Add unique items |
| `_get_archived_projects` | `(request: Dict) -> Dict` | Get archived projects |

**Key Capabilities:**
- Full project lifecycle management
- GitHub repository import with code validation
- Team collaboration with role-based access
- Subscription quota enforcement
- Initial spec extraction from descriptions

**Dependencies:**
- Internal: `Agent`, `ProjectContext`, `GitManager`, `CodeValidationAgent`
- External: Standard library

**Data Structures:**
- `ProjectContext` - Core project model
- `User` - User account model
- Extension-to-language mapping dictionary

**Configuration:**
- Skip directories: `.git`, `node_modules`, `__pycache__`, etc.
- Skip extensions: `.pyc`, `.exe`, `.dll`, etc.
- Max file size limits

---

### 3. KnowledgeManagerAgent (knowledge_manager.py)

**Main Class:** `KnowledgeManagerAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(name: str, orchestrator: AgentOrchestrator)` | Initialize with event subscription |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route to action handlers |
| `_handle_knowledge_suggestion` | `(data: Dict) -> None` | Handle KNOWLEDGE_SUGGESTION events |
| `_get_suggestions` | `(request: Dict) -> Dict` | Get pending suggestions |
| `_approve_suggestion` | `(request: Dict) -> Dict` | Approve a suggestion |
| `_reject_suggestion` | `(request: Dict) -> Dict` | Reject a suggestion |
| `_get_queue_status` | `(request: Dict) -> Dict` | Get suggestion queue status |
| `_clear_suggestions` | `(request: Dict) -> Dict` | Clear all suggestions |
| `_generate_suggestion_id` | `() -> str` | Generate unique suggestion ID |

**Key Capabilities:**
- Knowledge suggestion management
- Event-driven suggestion processing
- Approval/rejection workflow
- Queue status monitoring

**Dependencies:**
- Internal: `Agent`, `EventType`, `KnowledgeEntry`
- External: Standard library

**Data Structures:**
```python
suggestions = {
    project_id: {
        suggestion_id: {
            "id": str,
            "content": str,
            "category": str,
            "topic": str,
            "difficulty": str,
            "reason": str,
            "agent": str,
            "timestamp": str,
            "status": str  # pending/approved/rejected
        }
    }
}
```

---

### 4. DocumentProcessorAgent (document_processor.py)

**Main Class:** `DocumentProcessorAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize with logger |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route to action handlers |
| `_import_file` | `(request: Dict) -> Dict` | Import file, chunk, store |
| `_import_directory` | `(request: Dict) -> Dict` | Recursively process directory |
| `_import_text` | `(request: Dict) -> Dict` | Process inline text |
| `_import_url` | `(request: Dict) -> Dict` | Fetch and process URL |
| `_fetch_url_content` | `(url: str) -> Optional[str]` | Fetch URL with validation |
| `_extract_text_from_html` | `(html_content: str) -> str` | HTML to text extraction |
| `_read_file` | `(file_path: str) -> str` | Read file (text, PDF, code) |
| `_chunk_content` | `(content, chunk_size=500, overlap=50) -> List[str]` | Sentence-based chunking |
| `_store_code_structure` | `(file_name, structure, project_id) -> bool` | Store parsed code structure |
| `_format_code_structure` | `(file_name, structure) -> str` | Format for storage |
| `_format_metrics` | `(data) -> List[str]` | Format code metrics |
| `_format_functions` | `(data) -> List[str]` | Format function info |
| `_format_classes` | `(data) -> List[str]` | Format class info |
| `_format_imports` | `(data) -> List[str]` | Format import info |
| `_list_documents` | `(request: Dict) -> Dict` | List documents (placeholder) |

**Key Capabilities:**
- Multi-format document import (text, PDF, code, URL)
- Intelligent content chunking with overlap
- Code structure parsing and storage
- Vector database integration

**Dependencies:**
- Internal: `Agent`, `CodeParser`, `VectorDB`
- External: `pypdf`, `requests`, `HTMLParser`

**Supported Extensions:**
`.txt`, `.md`, `.py`, `.js`, `.java`, `.cpp`, `.pdf`, `.code`

**Configuration:**
- Chunk size: 500 words
- Chunk overlap: 50 words

---

### 5. QualityControllerAgent (quality_controller.py)

**Main Class:** `QualityControllerAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize calculators and thresholds |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route to 12 action handlers |
| `_calculate_phase_maturity` | `(request) -> Dict` | Return saved scores with spec analysis |
| `_update_maturity_after_response` | `(request) -> Dict` | Incremental scoring |
| `_verify_advancement` | `(request) -> Dict` | Generate warnings (non-blocking) |
| `_get_phase_readiness` | `(request) -> Dict` | Readiness assessment |
| `_get_maturity_summary` | `(request) -> Dict` | Cross-phase summary |
| `_get_maturity_history` | `(request) -> Dict` | Progression tracking |
| `_update_analytics_metrics` | `(request) -> Dict` | Calculate velocity, confidence |
| `_record_maturity_event` | `(request) -> Dict` | Record timestamped events |
| `_request_workflow_approval` | `(request) -> Dict` | Blocking approval point |
| `_approve_workflow` | `(request) -> Dict` | Unblock after approval |
| `_reject_workflow` | `(request) -> Dict` | Handle rejection |
| `_get_pending_approvals` | `(request) -> Dict` | List pending decisions |

**Key Capabilities:**
- Phase maturity tracking
- Incremental scoring: `answer_score = sum(spec_value × confidence)`
- Workflow approval (blocking)
- Analytics and velocity tracking
- Event emission for state changes

**Dependencies:**
- Internal: `Agent`, `MaturityCalculator`, `WorkflowOptimizer`, `AnalyticsCalculator`, `ProjectContext`, `WorkflowApprovalRequest`
- External: Standard library

**Phase Thresholds:**
- READY
- COMPLETE
- WARNING

**Events Emitted:**
- `PHASE_MATURITY_UPDATED`
- `QUALITY_CHECK_WARNING`
- `WORKFLOW_APPROVAL_REQUESTED`

---

### 6. SocraticCounselorAgent (socratic_counselor.py)

**Main Class:** `SocraticCounselorAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator: AgentOrchestrator) -> None` | Initialize with settings |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route actions |
| `_generate_question` | `(request: Dict) -> Dict` | Main question generation |
| `_generate_dynamic_question` | `(...) -> str` | Claude API question generation |
| `_generate_static_question` | `(...) -> str` | Fallback static questions |
| `_build_question_prompt` | `(...) -> str` | Build prompt with contexts |
| `_process_response` | `(request: Dict) -> Dict` | Process user answers |
| `_extract_insights_only` | `(request: Dict) -> Dict` | Extract insights only |
| `_update_project_context` | `(...) -> None` | Update specs from insights |
| `_explain_document` | `(request: Dict) -> Dict` | Document explanation |
| `_build_full_knowledge_context` | `(...) -> str` | Full document context |
| `_build_snippet_knowledge_context` | `(...) -> str` | Snippet context |
| `_generate_document_understanding` | `(...) -> str` | Document alignment analysis |
| `_group_knowledge_by_source` | `(...) -> Dict` | Group by source |
| `_handle_conflict_detection` | `(...) -> Dict` | Detect conflicts |
| `_handle_conflicts_realtime` | `(...) -> Dict` | Interactive resolution |
| `_conflict_to_dict` | `(...) -> Dict` | Convert ConflictInfo |
| `_remove_from_insights` | `(...) -> None` | Remove rejected insights |
| `_update_insights_value` | `(...) -> None` | Update with resolution |
| `_manual_resolution` | `(...) -> str` | Prompt for manual input |
| `_advance_phase` | `(request: Dict) -> Dict` | Move to next phase |
| `_rollback_phase` | `(request: Dict) -> Dict` | Return to previous |
| `_check_phase_completion` | `(...) -> bool` | Check >= 100% maturity |
| `_answer_question` | `(request: Dict) -> Dict` | Mark as answered |
| `_skip_question` | `(request: Dict) -> Dict` | Mark as skipped |
| `_reopen_question` | `(request: Dict) -> Dict` | Reopen skipped |
| `_generate_hint` | `(...) -> str` | Generate context-aware hint |
| `_generate_answer_suggestions` | `(...) -> List[str]` | Diverse suggestions |
| `_get_fallback_suggestions` | `(...) -> List[str]` | Phase-specific fallback |
| `_should_use_workflow_optimization` | `(...) -> bool` | Check workflow enabled |
| `_generate_question_with_workflow` | `(...) -> Dict` | Workflow-based questions |
| `_initiate_workflow_approval` | `(...) -> Dict` | Request QC approval |
| `_create_workflow_for_phase` | `(...) -> Dict` | Generate workflow |
| `_advance_workflow_node` | `(...) -> None` | Progress workflow |
| `_update_project_and_maturity` | `(...) -> None` | Update and recalculate |
| `_track_question_effectiveness` | `(...) -> None` | Log to learning system |
| `_find_last_question` | `(...) -> str` | Get last assistant message |
| `_count_extracted_specs` | `(...) -> int` | Tally specs |
| `_log_extracted_insights` | `(...) -> None` | Log breakdown |
| `_normalize_to_list` | `(...) -> List` | Convert to list |
| `_update_list_field` | `(...) -> List` | Add unique items |
| `_format_document_explanation` | `(...) -> str` | Format explanation |

**Key Capabilities:**
- Dynamic and static question generation
- Multi-phase Socratic dialogue (discovery, analysis, design, implementation)
- Insight extraction and conflict detection
- Document understanding and explanation
- Workflow optimization integration
- Role-aware questioning (ROLE_FOCUS_AREAS)

**Dependencies:**
- Internal: `Agent`, `ConflictDetectorAgent`, `ContextAnalyzerAgent`, `KnowledgeManagerAgent`, `QualityControllerAgent`, `VectorDB`, `Claude Client`
- External: `colorama`

**Configuration:**
- `use_dynamic_questions`: Boolean toggle
- `max_questions_per_phase`: 5
- `phase_docs_cache`: Phase-based caching

**Events Emitted:**
- `PHASE_ADVANCED`
- `WORKFLOW_NODE_ENTERED`
- `WORKFLOW_NODE_COMPLETED`

**Static Questions:**
5 base questions per phase with extended fallback options

---

### 7. UserLearningAgent (learning_agent.py)

**Main Class:** `UserLearningAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize with LearningEngine |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route to handlers |
| `_track_question_effectiveness` | `(data) -> Dict` | Track with EMA (alpha=0.3) |
| `_learn_behavior_pattern` | `(data) -> Dict` | Create/update patterns |
| `_recommend_next_question` | `(data) -> Dict` | Score and recommend |
| `_upload_knowledge_document` | `(data) -> Dict` | Persist with embeddings |
| `_get_user_profile` | `(data) -> Dict` | Build comprehensive profile |
| `_merge_pattern_data` | `(existing, new) -> Dict` | Dictionary merge |
| `emit_event` | `(event_type, data) -> None` | Event emission |

**Key Capabilities:**
- Question effectiveness tracking with exponential moving averages
- User behavior pattern learning
- Question recommendation based on historical effectiveness
- Knowledge document management with embeddings
- User profile building

**Dependencies:**
- Internal: `Agent`, `LearningEngine`, `KnowledgeBaseDocument`, `QuestionEffectiveness`, `UserBehaviorPattern`
- External: `sentence-transformers` (optional)

**Configuration:**
- EMA alpha: 0.3 for smoothing

---

### 8. CodeGeneratorAgent (code_generator.py)

**Main Class:** `CodeGeneratorAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize with name "CodeGenerator" |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route by action type |
| `_generate_artifact` | `(request: Dict) -> Dict` | Create project artifacts |
| `_generate_documentation` | `(request: Dict) -> Dict` | Generate documentation |
| `_build_generation_context` | `(project: ProjectContext) -> str` | Build context string |
| `_detect_language` | `(file_path: str) -> str` | Map extension to language |

**Key Capabilities:**
- Multi-file code generation
- Documentation generation
- Project structure organization
- Artifact persistence (disk and database)

**Dependencies:**
- Internal: `Agent`, `ProjectContext`, `ArtifactSaver`, `CodeStructureAnalyzer`, `MultiFileCodeSplitter`, `ProjectStructureGenerator`
- External: `pathlib`

**Supported Languages:** 40+ file extensions mapped

**Artifact Types:**
- software
- business
- research
- creative
- marketing
- educational

---

## Supporting Agents

### 9. CodeValidationAgent (code_validation_agent.py)

**Main Class:** `CodeValidationAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize validators |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route requests |
| `_validate_project` | `(request: Dict) -> Dict` | Full project validation |
| `_validate_file` | `(request: Dict) -> Dict` | Single file validation |
| `_run_tests` | `(request: Dict) -> Dict` | Execute tests |
| `_check_syntax` | `(request: Dict) -> Dict` | Syntax validation |
| `_check_dependencies` | `(request: Dict) -> Dict` | Dependency check |
| `_generate_summary` | `(...) -> Dict` | Generate validation summary |
| `_generate_recommendations` | `(...) -> List[str]` | Generate recommendations |
| `_syntax_recommendations` | `(...) -> List[str]` | Syntax-specific |
| `_dependency_recommendations` | `(...) -> List[str]` | Dependency-specific |
| `_test_recommendations` | `(...) -> List[str]` | Test-specific |
| `_general_recommendations` | `(...) -> List[str]` | General advice |
| `_codebase_recommendations` | `(...) -> List[str]` | Codebase-wide |
| `_format_summary_details` | `(...) -> str` | Format summary |

**Key Capabilities:**
- Syntax validation
- Dependency validation
- Test execution
- Recommendation generation

**Dependencies:**
- Internal: `Agent`, `SyntaxValidator`, `DependencyValidator`, `TestExecutor`

---

### 10. ConflictDetectorAgent (conflict_detector.py)

**Main Class:** `ConflictDetectorAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize four conflict checkers |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route requests |
| `_detect_conflicts` | `(request: Dict) -> Dict` | Parallel conflict detection |
| `_resolve_conflict` | `(request: Dict) -> Dict` | Resolve conflict |
| `_get_conflict_suggestions` | `(request: Dict) -> Dict` | Get suggestions |

**Key Capabilities:**
- Parallel conflict detection using ThreadPoolExecutor
- Four pluggable checkers:
  - TechStackConflictChecker
  - RequirementsConflictChecker
  - GoalsConflictChecker
  - ConstraintsConflictChecker

**Dependencies:**
- Internal: `Agent`, conflict_resolution module
- External: `concurrent.futures`

---

### 11. ContextAnalyzerAgent (context_analyzer.py)

**Main Class:** `ContextAnalyzerAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route actions |
| `_analyze_context` | `(request: Dict) -> Dict` | Analyze patterns |
| `_identify_patterns` | `(history: List[Dict]) -> Dict` | Extract metrics |
| `get_context_summary` | `(project: ProjectContext) -> str` | Build summary |
| `_get_summary` | `(request: Dict) -> Dict` | Wrap summary |
| `_find_similar` | `(request: Dict) -> Dict` | Query vector DB |
| `_search_conversations` | `(request: Dict) -> Dict` | Filter history |
| `_generate_summary` | `(request: Dict) -> Dict` | Claude-generated summary |
| `_get_statistics` | `(request: Dict) -> Dict` | Comprehensive metrics |

**Key Capabilities:**
- Project context analysis
- Conversation pattern extraction
- Similar project discovery
- Conversation search
- Claude-powered summarization
- Statistical metrics (days active, collaborators, etc.)

**Dependencies:**
- Internal: `Agent`, `ProjectContext`, `VectorDB`, `Claude Client`

---

### 12. DocumentContextAnalyzer (document_context_analyzer.py)

**Main Class:** `DocumentContextAnalyzer` (NOT an Agent)

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `()` | Initialize |
| `analyze_question_context` | `(project_context, conversation_history, question_count) -> str` | Return strategy |
| `detect_document_references` | `(text) -> List[str]` | Identify document mentions |
| `calculate_relevance_score` | `(query, document_chunk) -> float` | Jaccard similarity |
| `_has_document_keywords` | `(text) -> bool` | Check for keywords |
| `_get_recent_messages` | `(conversation_history, window) -> str` | Get recent context |
| `_contains_document_reference` | `(text) -> bool` | Check references |
| `_contains_specific_detail_question` | `(text) -> bool` | Check detail indicators |

**Key Capabilities:**
- Document retrieval strategy optimization
- Strategy selection: full/medium/snippet
- Relevance scoring with Jaccard similarity

**Constants:**
- `DOCUMENT_REFERENCE_KEYWORDS`: 19 keywords
- `DETAIL_REQUIRED_PHASES`: {analysis, design, evaluation, refinement}
- `SPECIFIC_DETAIL_INDICATORS`: 15 indicators

---

### 13. GitHubSyncHandler (github_sync_handler.py)

**Main Class:** `GitHubSyncHandler` (NOT an Agent)

**Custom Exceptions:**
- `ConflictResolutionError`
- `TokenExpiredError`
- `PermissionDeniedError`
- `RepositoryNotFoundError`
- `NetworkSyncFailedError`
- `FileSizeExceededError`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `detect_merge_conflicts` | `(repo_path) -> List` | Identify conflicted files |
| `resolve_merge_conflict` | `(repo_path, file_path, strategy) -> bool` | Resolve with strategy |
| `handle_merge_conflicts` | `(repo_path, conflict_info, default_strategy) -> Dict` | Full resolution |
| `validate_file_sizes` | `(files_to_push) -> Dict` | Check size limits |
| `handle_large_files` | `(files_to_push, strategy) -> Dict` | Handle oversized files |
| `check_token_validity` | `(token, token_expiry) -> bool` | Validate token |
| `sync_with_token_refresh` | `(repo_url, token, refresh_callback) -> Dict` | Sync with refresh |
| `sync_with_retry_and_resume` | `(repo_url, sync_function, max_retries, timeout) -> Dict` | Exponential backoff |
| `_call_with_timeout` | `(func, args, timeout_seconds) -> Any` | Signal-based timeout |
| `check_repo_access` | `(repo_url, token, timeout) -> Dict` | Verify access |
| `sync_with_permission_check` | `(repo_url, token, sync_function) -> Dict` | Access-checked sync |

**Key Capabilities:**
- Merge conflict detection and resolution (ours/theirs/manual)
- Large file handling (exclude, LFS, split)
- Token management with refresh
- Exponential backoff retry (1s to 32s)
- Permission verification

**Configuration:**
- `MAX_FILE_SIZE`: 100MB
- `MAX_REPO_SIZE`: 1GB
- `MAX_RETRIES`: 3
- `INITIAL_BACKOFF`: 1s
- `MAX_BACKOFF`: 32s

**Dependencies:**
- External: `subprocess`, `requests`, `signal`

---

### 14. KnowledgeAnalysisAgent (knowledge_analysis.py)

**Main Class:** `KnowledgeAnalysisAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize with event listeners |
| `process` | `(request: Dict) -> Dict` | Route requests |
| `_handle_document_imported` | `(data: Dict) -> None` | Event handler |
| `_analyze_knowledge` | `(request: Dict) -> Dict` | Extract concepts, assess relevance |
| `_regenerate_questions` | `(request: Dict) -> Dict` | Update question plans |
| `_get_knowledge_gaps` | `(request: Dict) -> Dict` | Identify gaps |
| `_extract_key_concepts` | `(search_results) -> List` | Parse top concepts |
| `_assess_relevance` | `(project, search_results) -> str` | high/medium/low |
| `_identify_gaps` | `(project, search_results) -> List` | Map uncovered areas |
| `_suggest_focus_areas` | `(project, search_results) -> List` | Phase-specific questions |
| `emit_event` | `(event_type, data) -> None` | Publish events |

**Key Capabilities:**
- Document import event handling
- Knowledge gap identification
- Question regeneration based on imported documents
- Relevance assessment

**Workflow:**
Document import → Knowledge analysis → Gap identification → Question regeneration → UI event emission

---

### 15. MultiLLMAgent (multi_llm_agent.py)

**Main Class:** `MultiLLMAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route requests |
| `_list_providers` | `(data) -> Dict` | List available providers |
| `_get_provider_models` | `(data) -> Dict` | Get provider models |
| `_get_provider_config` | `(data) -> Dict` | Get user config |
| `_set_default_provider` | `(data) -> Dict` | Set default provider |
| `_set_provider_model` | `(data) -> Dict` | Configure model |
| `_add_api_key` | `(data) -> Dict` | Store encrypted key |
| `_remove_api_key` | `(data) -> Dict` | Delete key |
| `_set_auth_method` | `(data) -> Dict` | Configure auth |
| `_track_usage` | `(data) -> Dict` | Record usage |
| `_get_usage_stats` | `(data) -> Dict` | Aggregate statistics |
| `_encrypt_api_key` | `(api_key) -> str` | Fernet + PBKDF2 |
| `_hash_api_key` | `(api_key) -> str` | SHA256 hash |

**Key Capabilities:**
- Multi-provider support (Claude, OpenAI, Gemini, Ollama)
- API key management with encryption
- Usage tracking and cost analysis
- Provider configuration

**Dependencies:**
- Internal: `Agent`, `LLMProviderConfig`, `LLMUsageRecord`
- External: `cryptography` (Fernet, PBKDF2)

---

### 16. NoteManagerAgent (note_manager.py)

**Main Class:** `NoteManagerAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route requests |
| `_add_note` | `(request) -> Dict` | Create with validation |
| `_list_notes` | `(request) -> Dict` | Retrieve notes |
| `_search_notes` | `(request) -> Dict` | Query by content |
| `_delete_note` | `(request) -> Dict` | Remove note |
| `_chunk_note_content` | `(content) -> List[str]` | Split for embedding |

**Key Capabilities:**
- Project note management
- Note types: design, bug, idea, task, general
- Vector database integration for search
- Content chunking (500 words, 50 overlap)
- Event emission for document import tracking

**Dependencies:**
- Internal: `Agent`, `ProjectNote`, `VectorDB`

---

### 17. ProjectFileLoader (project_file_loader.py)

**Main Class:** `ProjectFileLoader` (NOT an Agent)

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator: AgentOrchestrator)` | Initialize |
| `should_load_files` | `(project: ProjectContext) -> bool` | Check if files exist |
| `load_project_files` | `(project, strategy, max_files, show_progress) -> Dict` | Load files |
| `_load_all_project_files` | `(file_manager, project_id) -> List[Dict]` | Batch load |
| `_empty_files_response` | `(strategy) -> Dict` | Empty response |
| `_already_loaded_response` | `(strategy) -> Dict` | Already loaded response |
| `_process_project_files` | `(files, project_id, show_progress) -> tuple` | Process files |
| `_apply_strategy` | `(files, strategy, max_files) -> List[Dict]` | Apply loading strategy |
| `_priority_strategy` | `(files, max_files) -> List[Dict]` | Priority-based selection |
| `_sample_strategy` | `(files, max_files) -> List[Dict]` | Important + random |
| `_filter_duplicates` | `(files, project_id) -> List[Dict]` | Remove duplicates |
| `_rank_readme_files` | `(files, priority) -> List[tuple]` | Rank READMEs |
| `_rank_main_entry_points` | `(files, priority) -> List[tuple]` | Rank main files |
| `_rank_source_files` | `(files, priority) -> List[tuple]` | Rank source files |
| `_rank_test_files` | `(files, priority) -> List[tuple]` | Rank test files |
| `_rank_config_files` | `(files, priority) -> List[tuple]` | Rank config files |
| `_rank_other_files` | `(files, ranked_files, priority) -> List[tuple]` | Rank others |

**Key Capabilities:**
- Automated project file loading to vector DB
- Three strategies: priority, sample, all
- File ranking by importance
- Progress tracking

**File Priority Order:**
1. README files
2. Main entry points (main.py, index.js, etc.)
3. Source files (/src/, /lib/)
4. Test files
5. Config files (.json, .yaml, etc.)
6. Other files

---

### 18. QuestionQueueAgent (question_queue_agent.py)

**Main Class:** `QuestionQueueAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route requests |
| `_add_question` | `(request) -> Dict` | Create queue entry |
| `_determine_roles` | `(question, project) -> List[str]` | Map to team roles |
| `_get_user_questions` | `(request) -> Dict` | Filter pending for user |
| `_answer_question` | `(request) -> Dict` | Mark answered |
| `_skip_question` | `(request) -> Dict` | Mark skipped |
| `_get_queue_status` | `(request) -> Dict` | Calculate metrics |

**Key Capabilities:**
- Question queue management
- Role-based question assignment
- Status tracking (pending/answered/skipped)
- Completion metrics

**Team Roles:**
- lead
- creator
- specialist
- analyst
- coordinator

---

### 19. SystemMonitorAgent (system_monitor.py)

**Main Class:** `SystemMonitorAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route requests |
| `_track_tokens` | `(request: Dict) -> Dict` | Record API consumption |
| `_check_health` | `(request: Dict) -> Dict` | Validate API connectivity |
| `_get_stats` | `(request: Dict) -> Dict` | Aggregate metrics |
| `_check_limits` | `(request: Dict) -> Dict` | Identify threshold violations |

**Key Capabilities:**
- Token usage tracking
- Claude API health checking
- Usage statistics aggregation
- Threshold monitoring

**Configuration:**
- Token warning threshold: 50,000 tokens
- High usage alert: 40,000 tokens (recent 5-call window)
- Monitoring window: 10 or 5 API calls

**Attributes:**
- `token_usage`: List of TokenUsage objects
- `connection_status`: Boolean
- `last_health_check`: datetime

---

### 20. UserManagerAgent (user_manager.py)

**Main Class:** `UserManagerAgent(Agent)`

**Methods:**
| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(orchestrator)` | Initialize |
| `process` | `(request: Dict[str, Any]) -> Dict[str, Any]` | Route requests |
| `_archive_user` | `(request: Dict) -> Dict` | Self-archival |
| `_restore_user` | `(request: Dict) -> Dict` | Restore account |
| `_delete_user_permanently` | `(request: Dict) -> Dict` | Permanent deletion |
| `_get_archived_users` | `(request: Dict) -> Dict` | List archived |

**Key Capabilities:**
- User account archival (self-only)
- Account restoration
- Permanent deletion (requires "DELETE" confirmation)
- Archived user listing

**Security:**
- Users can only archive their own accounts
- Permanent deletion requires explicit "DELETE" string

---

## External Dependencies

### Python Standard Library
- `asyncio` - Async operations
- `logging` - Structured logging
- `abc` - Abstract base classes
- `datetime` - Timestamps
- `typing` - Type hints
- `concurrent.futures` - Parallel execution
- `pathlib` - Path handling
- `re` - Regular expressions
- `urllib.parse` - URL parsing
- `html.parser` - HTML parsing
- `uuid` - Unique IDs
- `signal` - Timeouts
- `subprocess` - Git commands

### Third-Party Libraries
| Library | Used By | Purpose |
|---------|---------|---------|
| `colorama` | SocraticCounselorAgent | Terminal colors |
| `pypdf` | DocumentProcessorAgent | PDF reading |
| `requests` | DocumentProcessorAgent, GitHubSyncHandler | HTTP requests |
| `cryptography` | MultiLLMAgent | API key encryption |
| `sentence-transformers` | UserLearningAgent | Document embeddings |

### Internal Dependencies
| Component | Used By |
|-----------|---------|
| `EventType` | All agents |
| `AgentOrchestrator` | All agents |
| `VectorDB` | Multiple agents |
| `Claude Client` | SocraticCounselorAgent, ContextAnalyzerAgent |
| `Database` | Most agents |
| `CodeParser` | DocumentProcessorAgent |
| `MaturityCalculator` | QualityControllerAgent |
| `WorkflowOptimizer` | QualityControllerAgent, SocraticCounselorAgent |
| `LearningEngine` | UserLearningAgent |
| `ConflictCheckers` | ConflictDetectorAgent |
| `Validators` | CodeValidationAgent |
| `GitManager` | ProjectManagerAgent |

---

## Data Flow Analysis

### Question Generation Flow
```
User Request
    │
    ▼
SocraticCounselorAgent._generate_question()
    │
    ├─► DocumentContextAnalyzer.analyze_question_context()
    │       │
    │       ▼
    │   VectorDB.search() ─► Knowledge context
    │
    ├─► ContextAnalyzerAgent.get_context_summary()
    │       │
    │       ▼
    │   ProjectContext analysis
    │
    ├─► QualityControllerAgent (workflow check)
    │
    └─► Claude API (dynamic) OR Static Questions (fallback)
            │
            ▼
        Generated Question
```

### Response Processing Flow
```
User Answer
    │
    ▼
SocraticCounselorAgent._process_response()
    │
    ├─► Claude API (insight extraction)
    │       │
    │       ▼
    │   Extracted Insights
    │
    ├─► ConflictDetectorAgent._detect_conflicts()
    │       │
    │       ├─► TechStackConflictChecker
    │       ├─► RequirementsConflictChecker
    │       ├─► GoalsConflictChecker
    │       └─► ConstraintsConflictChecker
    │               │
    │               ▼
    │           Conflicts (if any)
    │
    ├─► _update_project_context()
    │       │
    │       ▼
    │   Updated ProjectContext
    │
    └─► QualityControllerAgent._update_maturity_after_response()
            │
            ▼
        Updated Maturity Score
```

### Document Import Flow
```
Document Import Request
    │
    ▼
DocumentProcessorAgent._import_file()
    │
    ├─► _read_file() (PDF, text, code)
    │
    ├─► CodeParser (for code files)
    │       │
    │       ▼
    │   Code structure analysis
    │
    ├─► _chunk_content() (500 words, 50 overlap)
    │
    └─► VectorDB.add() (store chunks)
            │
            ▼
        Event: DOCUMENT_IMPORTED
            │
            ▼
KnowledgeAnalysisAgent._handle_document_imported()
    │
    ├─► _analyze_knowledge()
    │
    └─► _regenerate_questions()
            │
            ▼
        Updated Question Plan
```

### Project Creation Flow
```
Create Project Request
    │
    ▼
ProjectManagerAgent._create_project()
    │
    ├─► _get_or_create_user()
    │
    ├─► _validate_subscription() (quota check)
    │
    ├─► Initial spec extraction (if description provided)
    │       │
    │       ▼
    │   _apply_initial_insights()
    │
    └─► Database.save_project()
            │
            ▼
        New ProjectContext
```

### GitHub Import Flow
```
GitHub Import Request
    │
    ▼
ProjectManagerAgent._create_from_github()
    │
    ├─► _validate_github_url()
    │
    ├─► _clone_repository()
    │
    ├─► _extract_repository_metadata()
    │
    ├─► _run_code_validation()
    │       │
    │       ▼
    │   CodeValidationAgent
    │
    ├─► _create_project_context()
    │
    └─► _save_project_files()
            │
            ▼
        ProjectFileLoader.load_project_files()
            │
            ▼
        Files in VectorDB
```

---

## Configuration Requirements

### Environment Variables
| Variable | Purpose | Required By |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Claude API access | SocraticCounselorAgent, ContextAnalyzerAgent |
| `OPENAI_API_KEY` | OpenAI API access | MultiLLMAgent |
| `GOOGLE_API_KEY` | Gemini API access | MultiLLMAgent |
| `GITHUB_TOKEN` | GitHub API access | GitHubSyncHandler, ProjectManagerAgent |

### Database Configuration
- SQLite database path
- Vector database (ChromaDB) path
- File storage paths

### Agent-Specific Configuration

**SocraticCounselorAgent:**
```python
{
    "use_dynamic_questions": True,
    "max_questions_per_phase": 5
}
```

**QualityControllerAgent:**
```python
{
    "phase_thresholds": {
        "READY": 70,
        "COMPLETE": 100,
        "WARNING": 50
    }
}
```

**SystemMonitorAgent:**
```python
{
    "token_warning_threshold": 50000,
    "high_usage_alert": 40000,
    "monitoring_window": 10
}
```

**GitHubSyncHandler:**
```python
{
    "MAX_FILE_SIZE": 100 * 1024 * 1024,  # 100MB
    "MAX_REPO_SIZE": 1024 * 1024 * 1024,  # 1GB
    "MAX_RETRIES": 3,
    "INITIAL_BACKOFF": 1,
    "MAX_BACKOFF": 32
}
```

**DocumentProcessorAgent:**
```python
{
    "chunk_size": 500,
    "chunk_overlap": 50,
    "supported_extensions": [".txt", ".md", ".py", ".js", ".java", ".cpp", ".pdf", ".code"]
}
```

**ProjectFileLoader:**
```python
{
    "strategies": ["priority", "sample", "all"],
    "max_files": 50,
    "batch_size": 100
}
```

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Agents | 21 (excluding test file) |
| Agent subclasses | 16 |
| Standalone classes | 5 |
| Total methods | ~200+ |
| External libraries | 5 |
| Event types used | 10+ |
| Database models | 15+ |

---

## Recommendations for Modularization

1. **Core Module**: Agent base, EventType, Orchestrator
2. **Dialogue Module**: SocraticCounselorAgent, QuestionQueueAgent
3. **Analysis Module**: ContextAnalyzerAgent, ConflictDetectorAgent, KnowledgeAnalysisAgent
4. **Document Module**: DocumentProcessorAgent, NoteManagerAgent, ProjectFileLoader, DocumentContextAnalyzer
5. **Code Module**: CodeGeneratorAgent, CodeValidationAgent
6. **Quality Module**: QualityControllerAgent (MaturityCalculator, WorkflowOptimizer)
7. **Learning Module**: UserLearningAgent (LearningEngine)
8. **Integration Module**: GitHubSyncHandler, MultiLLMAgent
9. **Management Module**: ProjectManagerAgent, UserManagerAgent, KnowledgeManagerAgent
10. **Monitoring Module**: SystemMonitorAgent
