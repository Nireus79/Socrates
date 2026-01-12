# Quality Controller Mechanism: Comprehensive Documentation

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [The Cause: Why Quality Controller Exists](#the-cause-why-quality-controller-exists)
3. [Current State: Advisory System](#current-state-advisory-system)
4. [Future State: Workflow Optimization System](#future-state-workflow-optimization-system)
5. [How It Works: Technical Flow](#how-it-works-technical-flow)
6. [Example Scenarios](#example-scenarios)
7. [Architecture Details](#architecture-details)
8. [Migration Path](#migration-path)

---

## Executive Summary

The **Quality Controller (QC)** is Socrates' mechanism for preventing "greedy algorithm" behavior in agents. Agents naturally make locally-optimal decisions (choosing the easiest next step) without considering the global cost impact (expensive overall path). The QC solves this by:

1. **Enumerating all possible workflow paths** before execution begins
2. **Calculating cost (API tokens) and risk (specification gaps, rework probability)** for each path
3. **Recommending the optimal path** based on strategy (minimize cost, minimize risk, balanced, etc.)
4. **Blocking execution** until user/system approves a path
5. **Constraining question generation** to follow the approved path

**Current State**: QC is an advisory system that measures maturity and generates warnings but does NOT block execution.

**Future State**: QC will be a true workflow optimizer with approval gates that prevent agents from proceeding down suboptimal paths.

---

## The Cause: Why Quality Controller Exists

### The Problem: Greedy Algorithm Behavior

Software agents, when making decisions independently, exhibit **greedy algorithm** behavior:

- **Locally-optimal decisions**: Each decision looks good in isolation
- **Globally-suboptimal outcomes**: The sequence of "good" decisions leads to expensive or risky overall paths
- **No look-ahead**: Agents don't evaluate the full cost/benefit of their entire execution path

### Real-World Example: Question Generation in Discovery Phase

Consider an agent generating questions to understand a user's project during the Discovery phase:

**Scenario**: Agent needs to reach 20% maturity across 10 categories (goals, requirements, tech stack, constraints, risks, etc.)

#### Greedy Approach (Current Behavior):

```
Agent reasoning per question:
  "What's the most informative question I can ask RIGHT NOW?"

Question 1: "What's your project about?" (easy, broad, 2000 tokens)
  → Covers: goals
Question 2: "What tech stack will you use?" (easy, specific, 1500 tokens)
  → Covers: tech_stack
Question 3: "What are your requirements?" (easy, common, 1800 tokens)
  → Covers: requirements
Question 4: "Tell me about constraints?" (medium, detailed, 3000 tokens)
  → Covers: constraints
Question 5: "What risks do you foresee?" (hard, deep analysis, 5000 tokens)
  → Covers: risks

Total tokens: 13,300
Coverage: 5/10 categories = 50%
Risk: High (missing deployment, timeline, team structure, assumptions, dependencies)
```

Each question seemed like a good choice at the time, but:
- Questions were chosen one-at-a-time for immediate informativeness
- No consideration of overall path efficiency
- Ended with high token usage AND poor coverage

#### Global Optimization Approach (With QC):

```
Agent reasoning before starting:
  "What are ALL possible question sequences I could ask?
   Which complete path has the best cost/risk/benefit ratio?"

Path A (Basic Coverage):
  3 questions, 7000 tokens, 30% coverage, HIGH risk (missing categories)

Path B (Balanced Coverage):
  5 questions, 11000 tokens, 60% coverage, MEDIUM risk (some gaps)

Path C (Comprehensive Coverage):
  7 questions, 15000 tokens, 90% coverage, LOW risk (minimal gaps)

QC Analysis:
  Path A: Cheap but too risky (70% rework probability)
  Path B: OPTIMAL - Good balance of cost/risk/coverage (RECOMMENDED)
  Path C: Expensive and overkill for 20% threshold

User approves Path B → Agent follows exactly those 5 questions → No deviation

Result: Better coverage at similar cost, with lower rework risk
```

### Why Greedy Fails: The Cost of Locally-Optimal Decisions

**Example Path Comparison**:

| Approach | Questions | Tokens | Coverage | Rework Prob | Total Cost |
|----------|-----------|--------|----------|-------------|------------|
| Greedy (one-at-a-time) | 5 | 13,300 | 50% | 65% | 13,300 + (65% × 20,000 rework) = **26,300 tokens** |
| Optimized (look-ahead) | 5 | 11,000 | 60% | 35% | 11,000 + (35% × 20,000 rework) = **18,000 tokens** |

**Savings: 31% reduction** in total expected cost by using global optimization instead of greedy selection.

### Root Causes of Greedy Behavior

1. **Agent autonomy**: Each agent makes decisions independently without cross-agent coordination
2. **Immediate reward**: Agents optimize for immediate value (informative questions) over long-term efficiency
3. **No cost visibility**: Agents don't see the cumulative cost impact of their decision sequence
4. **No alternative comparison**: Agents evaluate one option at a time, not all possible paths simultaneously

### The Solution: Quality Controller as Workflow Optimizer

**Key Insight**: Prevent greedy behavior by forcing agents to:
1. **Enumerate all possible execution paths** BEFORE starting
2. **Calculate comprehensive metrics** (cost, risk, quality) for EACH complete path
3. **Compare alternatives** and select the globally-optimal path
4. **Commit to the chosen path** and block deviations

This transforms locally-optimal, myopic decision-making into globally-optimal, strategic planning.

---

## Current State: Advisory System

### What QC Currently Does

The Quality Controller currently operates as a **measurement and warning system** without blocking capabilities:

#### 1. Maturity Measurement
- **Location**: `socratic_system/agents/quality_controller.py`
- **Triggered**: After each user response is processed
- **Function**: Calculates phase maturity using the `MaturityCalculator`
- **Algorithm**:
  ```python
  For each phase category:
      Get all specs tagged with that category
      Calculate: weighted_sum = Σ(spec_value × confidence)
      Cap at category target (prevents domination)
  Overall maturity = (total_score / 90) × 100
  ```

#### 2. Warning Generation
- **Thresholds**:
  - `WARNING_THRESHOLD = 10%`: Below this triggers strong warning
  - `READY_THRESHOLD = 20%`: Below this triggers advancement warning
  - `COMPLETE_THRESHOLD = 100%`: Phase fully mature
- **Warning Types**:
  - Overall score warnings ("Phase maturity very low")
  - Missing category warnings ("No coverage in: goals, requirements, tech_stack")
  - Weak category warnings ("Weak areas: assumptions, risks")
  - Imbalance warnings ("Some categories well-developed while others missing")

#### 3. Event Emission
- Emits `QUALITY_CHECK_COMPLETED` events after each analysis
- Events include:
  - Phase maturity score
  - Warnings list
  - Category breakdowns
  - Ready/complete status

#### 4. Maturity Reporting
- Provides detailed maturity reports on demand
- Shows category-by-category breakdown
- Identifies strongest/weakest/missing areas
- Generates actionable recommendations

### What QC Does NOT Currently Do

**Critical Limitation**: QC is purely advisory - it **DOES NOT BLOCK** any agent actions.

- ❌ Does NOT evaluate multiple workflow paths
- ❌ Does NOT compare cost/risk between alternatives
- ❌ Does NOT prevent agents from proceeding
- ❌ Does NOT control question generation
- ❌ Does NOT require approval before execution
- ❌ Does NOT constrain agent behavior to optimal paths

**Example Current Flow**:

```
User answers question
    ↓
SocraticCounselor processes response
    ↓
Specifications extracted and stored
    ↓
QualityController measures maturity
    ↓
QC generates warnings: "Phase maturity low (12%)"
    ↓
Warnings displayed to user
    ↓
Agent generates next question (GREEDY - picks immediately informative question)
    ↓
Execution continues (NO BLOCKING)
```

### Integration Points (Current)

**1. SocraticCounselor Integration** (`socratic_counselor.py:1029-1108`)
```python
def _process_response(self, request: Dict) -> Dict:
    # ... process user response, extract insights ...

    # Check quality after processing
    if project.phase_maturity_scores.get(project.phase, 0) >= 60:
        self._perform_quality_check(project, current_user)  # ADVISORY ONLY

    # Continue with question generation
    return self._generate_next_question(project, current_user)  # NO BLOCKING
```

**2. Orchestrator Integration** (`orchestrator.py:457-516`)
```python
def process_request(self, agent_name: str, request: Dict) -> Dict:
    # Route to agent
    result = agent.process(request)

    # QC is just another agent, called explicitly
    # Does NOT intercept other agents' requests
    # Does NOT enforce approval gates

    return result
```

**3. Current QC Actions** (`quality_controller.py`)
```python
action_handlers = {
    "check_quality": self._check_quality,              # Measure & warn
    "get_maturity_report": self._get_maturity_report,  # Report generation
    "analyze_trends": self._analyze_trends,            # Historical analysis
    "get_recommendations": self._get_recommendations,  # Suggest improvements
}
# NO APPROVAL ACTIONS - purely informational
```

### Limitations of Current System

1. **No Path Comparison**: QC measures current state but doesn't compare alternative futures
2. **No Cost Awareness**: No token counting or cost estimation for different question sequences
3. **No Blocking**: Agents proceed regardless of QC warnings
4. **Reactive, Not Proactive**: QC reacts to decisions already made, can't prevent bad choices
5. **No Question Control**: Question generation is unconstrained by QC recommendations

---

## Future State: Workflow Optimization System

### Overview: From Advisory to Enforcing

The enhanced QC transforms from a **measurement system** into a **decision optimization and enforcement system**:

| Aspect | Current (Advisory) | Future (Optimizer) |
|--------|-------------------|-------------------|
| **Role** | Measures and warns | Plans and enforces |
| **Timing** | After decisions made | Before execution starts |
| **Mechanism** | Calculate maturity → warn | Enumerate paths → approve → block |
| **Scope** | Single state snapshot | Complete workflow paths |
| **Agent Interaction** | Agent ignores warnings | Agent blocked until approval |
| **Cost Awareness** | None | Token estimation per path |
| **Risk Assessment** | Current gaps only | Future rework probability |

### New Capabilities

#### 1. Workflow Graph Representation

**Data Model**: `WorkflowDefinition` represents agent workflows as directed graphs

```python
WorkflowDefinition:
  - Nodes: Steps in the workflow (question sets, analysis, validation)
  - Edges: Transitions between steps (with probabilities and costs)
  - Start/End: Entry and exit points
  - Strategy: How to select optimal path (minimize cost, minimize risk, balanced)
```

**Example Discovery Workflow**:

```
        ┌─────────────┐
        │   START     │
        └──────┬──────┘
               │
         ┌─────┴─────┐
         │           │
         ▼           ▼
  ┌────────────┐  ┌─────────────┐
  │   Basic    │  │Comprehensive│
  │ Questions  │  │  Questions  │
  │ (3 Q's)    │  │   (5 Q's)   │
  │ 7000 tok   │  │  11000 tok  │
  └─────┬──────┘  └──────┬──────┘
        │                │
        └────────┬───────┘
                 ▼
         ┌──────────────┐
         │   Analysis   │
         │   5000 tok   │
         └──────┬───────┘
                ▼
          ┌──────────┐
          │   END    │
          └──────────┘

Possible Paths:
  Path A: START → Basic Questions → Analysis → END
          Total: 12,000 tokens, 40% coverage, HIGH risk
  Path B: START → Comprehensive Questions → Analysis → END
          Total: 16,000 tokens, 70% coverage, LOW risk
```

#### 2. Path Enumeration Algorithm

**DFS-based path finding** that discovers all valid routes through the workflow:

```python
Algorithm: find_all_paths(workflow)
  Input: WorkflowDefinition with nodes and edges
  Output: List of complete paths from start to any end node

  Procedure:
    adjacency_list = build_graph(workflow.edges)
    all_paths = []

    for each end_node in workflow.end_nodes:
        paths = dfs_paths(
            current = workflow.start_node,
            target = end_node,
            visited = empty_set,
            current_path = empty_list
        )
        all_paths.extend(paths)

    return all_paths

  DFS Logic:
    - Mark current node as visited (avoid cycles)
    - If current == target: return current path
    - For each unvisited neighbor:
        Recursively explore with updated path
    - Return all paths found
```

**Example Output**:
```
Workflow with 3 branches → 3 possible paths enumerated
Each path: [node_ids], [edge_ids], ready for cost/risk calculation
```

#### 3. Cost Calculator

**Token estimation** for each complete path:

```python
Constants:
  COST_PER_QUESTION_GENERATION = 500   # Claude API call to generate question
  COST_PER_QUESTION_ANALYSIS = 1000    # Claude API call to analyze response
  COST_PER_VALIDATION = 800            # Validation check tokens
  AVG_TOKEN_COST = $0.000045           # USD per token

Calculation per path:
  total_tokens = 0
  for each node in path.nodes:
      total_tokens += node.estimated_tokens
  for each edge in path.edges:
      total_tokens += edge.cost

  total_cost_usd = total_tokens * AVG_TOKEN_COST

  return {
      total_tokens: 15000,
      total_cost_usd: $0.675,
      breakdown: {node1: 7000, node2: 5000, node3: 3000}
  }
```

#### 4. Risk Calculator

**Multi-dimensional risk assessment**:

```python
Risk Components (weighted):

1. Incompleteness Risk (40% weight):
   - Categories with no coverage in this path
   - Formula: (missing_categories / total_categories) × 100
   - Example: 4 missing out of 10 = 40% incompleteness risk

2. Complexity Risk (30% weight):
   - Technical difficulty of questions in path
   - Ambiguity and depth of coverage needed
   - Example: Basic questions = 20%, Deep questions = 60%

3. Rework Risk (30% weight):
   - Probability of needing to redo work due to gaps
   - Based on maturity deficits and missing critical categories
   - Example: Low coverage = 70% rework, High coverage = 20% rework

Overall Risk Score:
  risk = (incompleteness × 0.4) + (complexity × 0.3) + (rework × 0.3)

Example:
  Path A: 40% incompleteness, 20% complexity, 65% rework
  → Risk = (40×0.4) + (20×0.3) + (65×0.3) = 41.5
```

#### 5. Path Selection Strategies

**Multiple strategies** for choosing the optimal path:

```python
Strategy Options:

1. MINIMIZE_COST:
   - Select path with lowest token count
   - Best for: Budget-constrained projects
   - Risk: May sacrifice quality/coverage

2. MINIMIZE_RISK:
   - Select path with lowest risk score
   - Best for: Critical projects needing high reliability
   - Risk: May be expensive

3. BALANCED (default):
   - Weighted combination: 50% cost, 30% risk, 20% quality
   - Best for: Most projects
   - Provides good cost/benefit tradeoff

4. MAXIMIZE_QUALITY:
   - Select path with highest quality score (maturity gain)
   - Best for: Projects where thoroughness is critical
   - Risk: Most expensive

5. USER_CHOICE:
   - Present all paths, let user decide
   - Best for: When user has domain knowledge or specific preferences
```

#### 6. Approval Blocking Mechanism

**Critical Change**: Execution stops and waits for approval

```python
Flow with Approval Gate:

SocraticCounselor._generate_question():
    if workflow_optimization_enabled:
        if not active_workflow_execution:
            # BLOCKING POINT 1: No approved workflow yet
            result = _initiate_workflow_approval(project)

            if result.status == "pending_approval":
                # EXECUTION STOPS HERE
                # Agent cannot proceed
                # User/API must approve a path
                return result

        # Have approved workflow - continue execution
        execution = project.active_workflow_execution
        questions = select_from_approved_path(execution)
        return questions

QualityController._request_workflow_approval():
    # Enumerate all paths
    all_paths = path_finder.find_all_paths(workflow)

    # Calculate cost/risk for each
    for path in all_paths:
        path.cost = cost_calculator.calculate(path)
        path.risk = risk_calculator.calculate(path)

    # Recommend optimal
    recommended = select_optimal_path(all_paths, strategy)

    # Store as pending approval
    approval_request = WorkflowApprovalRequest(
        all_paths=all_paths,
        recommended=recommended,
        status="pending"
    )
    pending_approvals[request_id] = approval_request

    # Emit event for async notification
    emit_event(WORKFLOW_APPROVAL_REQUESTED)

    # Return BLOCKING status
    return {
        "status": "pending_approval",  # THIS BLOCKS EXECUTION
        "request_id": request_id,
        "message": "Workflow approval required before proceeding"
    }
```

#### 7. Question Optimization

**Path-constrained question selection**:

```python
QuestionSelector.select_next_questions():
    # Get current node in approved path
    current_node = execution.current_node

    if current_node.type == QUESTION_SET:
        # Get categories this node should target
        target_categories = current_node.metadata["target_categories"]

        # Get categories already covered
        covered_categories = get_covered_categories(project)

        # Generate questions ONLY for needed categories
        uncovered = [c for c in target_categories if c not in covered]
        questions = generate_category_targeted_questions(uncovered)

        return questions

    # Node is not a question set - advance to next node
    return advance_to_next_node(execution)
```

**Key Difference from Greedy**:
- **Greedy**: "What's the most informative question right now?" (no path constraint)
- **Optimized**: "What question does the approved path require at this step?" (path-constrained)

---

## How It Works: Technical Flow

### Phase 1: Workflow Definition (Setup)

**When**: Before agent starts executing (e.g., at start of Discovery phase)

**Who**: `WorkflowBuilder` creates workflow definition

```python
# Example: Discovery phase workflow with 2 alternative paths

workflow = WorkflowBuilder(workflow_id="discovery_v1", phase="discovery")
    .add_node("start", PHASE_START, "Phase Start", 0)
    .add_node("basic_q", QUESTION_SET, "Basic Questions", 7000,
              metadata={"target_categories": ["goals", "requirements", "tech_stack"]})
    .add_node("comprehensive_q", QUESTION_SET, "Comprehensive Questions", 11000,
              metadata={"target_categories": ["goals", "requirements", "tech_stack",
                                             "constraints", "risks", "timeline", "team"]})
    .add_node("analysis", ANALYSIS, "Analyze Responses", 5000)
    .add_node("end", PHASE_END, "Phase Complete", 0)
    .add_edge("start", "basic_q", probability=1.0, cost=0)
    .add_edge("start", "comprehensive_q", probability=1.0, cost=0)
    .add_edge("basic_q", "analysis", probability=1.0, cost=500)
    .add_edge("comprehensive_q", "analysis", probability=1.0, cost=500)
    .add_edge("analysis", "end", probability=1.0, cost=0)
    .set_entry("start")
    .add_exit("end")
    .set_strategy(PathDecisionStrategy.BALANCED)
    .build()

# Result: Workflow with 2 possible paths ready for optimization
```

### Phase 2: Approval Request (Blocking Point)

**When**: Agent attempts to start workflow (e.g., generate first question)

**Who**: `SocraticCounselor` → `QualityController` → `WorkflowOptimizer`

```python
# User in CLI: /chat or /ask
# Agent flow:

SocraticCounselor._generate_question():
    # Check if workflow optimization enabled
    if project.metadata["use_workflow_optimization"]:
        # Check if we have an active approved workflow
        if not project.active_workflow_execution:
            # NO APPROVED WORKFLOW - REQUEST APPROVAL
            return _initiate_workflow_approval(project, user)

        # Have approved workflow - proceed with constrained questions
        return _generate_from_approved_path(project)

_initiate_workflow_approval():
    # Create workflow definition
    workflow = create_workflow_for_phase(project)

    # Call QualityController to optimize
    result = orchestrator.process_request("quality_controller", {
        "action": "request_workflow_approval",
        "project_id": project.project_id,
        "workflow": workflow,
        "requested_by": user
    })

    # Result will be status="pending_approval" - BLOCKS HERE
    return result
```

### Phase 3: Path Optimization

**When**: QC receives approval request

**Who**: `QualityController` → `WorkflowOptimizer` → `PathFinder`, `CostCalculator`, `RiskCalculator`

```python
QualityController._request_workflow_approval():
    # 1. Enumerate all paths
    path_finder = WorkflowPathFinder(workflow)
    all_paths = path_finder.find_all_paths()
    # Result: [Path A (basic), Path B (comprehensive)]

    # 2. Calculate metrics for each path
    for path in all_paths:
        # Cost calculation
        cost_metrics = cost_calculator.calculate_path_cost(path, workflow)
        path.total_cost_tokens = cost_metrics["total_tokens"]
        path.total_cost_usd = cost_metrics["total_cost_usd"]

        # Risk calculation
        risk_metrics = risk_calculator.calculate_path_risk(path, workflow, project)
        path.risk_score = risk_metrics["risk_score"]
        path.incompleteness_risk = risk_metrics["incompleteness_risk"]
        path.rework_probability = risk_metrics["rework_probability"]

        # Quality/ROI calculation
        path.quality_score = calculate_quality(path)
        path.roi_score = calculate_roi(path)

    # 3. Select optimal path based on strategy
    recommended_path = select_optimal_path(all_paths, workflow.strategy)
    # Strategy=BALANCED → Path B selected (best cost/risk/quality tradeoff)

    # 4. Create approval request
    approval_request = WorkflowApprovalRequest(
        request_id="wf_abc123",
        all_paths=all_paths,
        recommended_path=recommended_path,
        status="pending"
    )

    # 5. Store as pending
    self.pending_approvals[approval_request.request_id] = approval_request

    # 6. Emit event for async notification
    self.emit_event(WORKFLOW_APPROVAL_REQUESTED, {
        "request_id": "wf_abc123",
        "project_id": project.project_id,
        "path_count": 2
    })

    # 7. Return BLOCKING status
    return {
        "status": "pending_approval",  # EXECUTION STOPS
        "request_id": "wf_abc123",
        "approval_request": approval_request
    }
```

### Phase 4: User Approval (CLI or API)

**When**: User sees approval prompt

**Who**: User interaction via CLI or API

**CLI Flow**:

```python
WorkflowCommands.handle_approval_request():
    print("\n" + "="*80)
    print("WORKFLOW APPROVAL REQUIRED - DISCOVERY PHASE")
    print("="*80)

    print("\nAvailable Paths:")
    print("Path   Description              Tokens   Cost      Risk   Quality   ROI")
    print("-"*80)
    print("   1   Basic Questions          12,000   $0.54    45.0     65       1.2")
    print(">> 2   Comprehensive Questions  16,000   $0.72    28.0     85       1.8  (RECOMMENDED)")
    print("\nOptions: [1/2] select path, [r] recommended, [c] cancel")

    choice = input("> ")

    if choice == "r" or choice == "2":
        approved_path_id = "comprehensive_questions_path"

        # Submit approval to QC
        result = orchestrator.process_request("quality_controller", {
            "action": "approve_workflow",
            "request_id": "wf_abc123",
            "approved_path_id": approved_path_id
        })

        return result
```

**API Flow**:

```python
# Frontend receives WebSocket event: WORKFLOW_APPROVAL_REQUESTED
# Frontend fetches pending approvals:
GET /api/v1/workflow/pending-approvals/{project_id}

# Display approval UI to user with path comparison table
# User clicks "Approve Path 2"

# Frontend submits approval:
POST /api/v1/workflow/approve
{
    "request_id": "wf_abc123",
    "approved_path_id": "comprehensive_questions_path"
}

# Backend processes approval (see Phase 5)
```

### Phase 5: Approval Processing

**When**: User submits approval choice

**Who**: `QualityController` processes approval

```python
QualityController._approve_workflow():
    # Get pending approval request
    approval_request = self.pending_approvals[request_id]

    # Find the approved path
    approved_path = [p for p in approval_request.all_paths
                     if p.path_id == approved_path_id][0]

    # Mark as approved
    approval_request.status = "approved"
    approval_request.approved_path_id = approved_path_id
    approval_request.approval_timestamp = now()

    # Remove from pending
    del self.pending_approvals[request_id]

    # Create execution state for project
    execution_state = WorkflowExecutionState(
        execution_id="exec_xyz789",
        workflow_id=approval_request.workflow.workflow_id,
        approved_path_id=approved_path_id,
        current_node_id=approved_path.nodes[1],  # First node after START
        completed_nodes=[approved_path.nodes[0]],  # START completed
        remaining_nodes=approved_path.nodes[2:],
        estimated_tokens_remaining=approved_path.total_cost_tokens,
        status="active"
    )

    # Store execution state in project
    project.active_workflow_execution = execution_state
    project.workflow_definitions[project.phase] = approval_request.workflow
    database.save_project(project)

    # Emit approval event
    self.emit_event(WORKFLOW_APPROVED, {
        "request_id": request_id,
        "approved_path_id": approved_path_id
    })

    # Return success - EXECUTION CAN NOW RESUME
    return {"status": "success", "approved_path_id": approved_path_id}
```

### Phase 6: Constrained Execution

**When**: Agent resumes after approval

**Who**: `SocraticCounselor` with `QuestionSelector`

```python
SocraticCounselor._generate_question():
    # Check for active workflow execution (now exists)
    execution = project.active_workflow_execution
    workflow = project.workflow_definitions[project.phase]

    # Get current node in approved path
    current_node = workflow.nodes[execution.current_node_id]
    # current_node = "comprehensive_questions" node

    # Use QuestionSelector to pick questions from this node
    selector = QuestionSelector()
    questions = selector.select_next_questions(project, workflow, execution)

    # Questions are now constrained to this node's target categories
    # Node metadata: target_categories = ["goals", "requirements", "tech_stack",
    #                                     "constraints", "risks", "timeline", "team"]

    # Generate question for first uncovered category
    question = questions[0]  # e.g., "What are your project's primary goals?"

    return {
        "status": "success",
        "question": question,
        "workflow_node": "comprehensive_questions",
        "path": "comprehensive_questions_path"
    }

QuestionSelector.select_next_questions():
    # Get what this node needs
    target_categories = current_node.metadata["target_categories"]

    # Get what's already covered
    covered_categories = get_covered_categories(project)
    # covered_categories = [] (first question, nothing covered yet)

    # Find gaps
    uncovered = [c for c in target_categories if c not in covered]
    # uncovered = ["goals", "requirements", "tech_stack", "constraints", "risks", "timeline", "team"]

    # Generate questions ONLY for uncovered categories in this node
    questions = generate_category_targeted_questions(project, uncovered, current_node)

    # Return questions (agent will ask first one)
    return questions
```

### Phase 7: Node Advancement

**When**: All questions in current node completed

**Who**: `SocraticCounselor`

```python
SocraticCounselor._generate_question():
    execution = project.active_workflow_execution
    workflow = project.workflow_definitions[project.phase]

    selector = QuestionSelector()
    questions = selector.select_next_questions(project, workflow, execution)

    if not questions:
        # No more questions in this node - advance to next node
        _advance_workflow_node(project, execution)
        return {"status": "workflow_node_advanced", "next_node": execution.current_node_id}

_advance_workflow_node(project, execution):
    # Get approved path
    approved_path = [p for p in project.workflow_approval_requests[-1].all_paths
                     if p.path_id == execution.approved_path_id][0]

    # Find current position in path
    current_idx = approved_path.nodes.index(execution.current_node_id)

    # Mark current as completed
    execution.completed_nodes.append(execution.current_node_id)

    # Move to next node
    execution.current_node_id = approved_path.nodes[current_idx + 1]
    # e.g., "comprehensive_questions" → "analysis"

    # Update remaining
    execution.remaining_nodes = approved_path.nodes[current_idx + 2:]

    # Save
    database.save_project(project)

    # Emit event
    emit_event(WORKFLOW_NODE_ENTERED, {"node_id": execution.current_node_id})
```

### Phase 8: Workflow Completion

**When**: Execution reaches END node

**Who**: `SocraticCounselor`

```python
SocraticCounselor._generate_question():
    execution = project.active_workflow_execution

    if execution.current_node_id == workflow.end_nodes[0]:
        # Workflow complete
        execution.status = "completed"

        # Record actual vs estimated tokens
        actual_tokens = execution.actual_tokens_used
        estimated_tokens = approved_path.total_cost_tokens
        variance = ((actual_tokens - estimated_tokens) / estimated_tokens) * 100

        # Store in history
        project.workflow_history.append({
            "workflow_id": execution.workflow_id,
            "approved_path": execution.approved_path_id,
            "estimated_tokens": estimated_tokens,
            "actual_tokens": actual_tokens,
            "variance": variance,
            "completed_at": now()
        })

        # Clear active execution
        project.active_workflow_execution = None
        database.save_project(project)

        # Emit completion event
        emit_event(WORKFLOW_NODE_COMPLETED, {"workflow_id": execution.workflow_id})

        # Phase may now advance if maturity sufficient
        return {"status": "workflow_completed"}
```

---

## Example Scenarios

### Scenario 1: Discovery Phase - Balanced Strategy

**Setup**:
- New project in Discovery phase
- Workflow optimization enabled
- Strategy: BALANCED

**Workflow Definition**:
```
Path A (Quick Start):
  - 3 questions covering basic categories
  - 8,000 tokens, $0.36
  - 40% coverage, 55 risk score
  - Questions: goals, tech_stack, requirements

Path B (Standard):
  - 5 questions covering core categories
  - 12,000 tokens, $0.54
  - 65% coverage, 32 risk score
  - Questions: goals, requirements, tech_stack, constraints, timeline

Path C (Comprehensive):
  - 7 questions covering all categories
  - 16,000 tokens, $0.72
  - 90% coverage, 18 risk score
  - Questions: all 10 categories
```

**Optimization**:
```
QC Analysis:
  Path A: Fast but risky (70% rework probability)
          → Expected total cost: 8,000 + (0.70 × 15,000) = 18,500 tokens
  Path B: OPTIMAL - Good balance
          → Expected total cost: 12,000 + (0.35 × 15,000) = 17,250 tokens
  Path C: Thorough but expensive
          → Expected total cost: 16,000 + (0.15 × 15,000) = 18,250 tokens

Recommendation: Path B (Standard)
Reason: Lowest expected total cost when factoring rework
```

**User Approval**:
```
CLI Display:
┌────────────────────────────────────────────────────────────────┐
│         WORKFLOW APPROVAL REQUIRED - DISCOVERY PHASE           │
├────────────────────────────────────────────────────────────────┤
│ Path   Description    Tokens   Cost    Risk   Quality   ROI   │
├────────────────────────────────────────────────────────────────┤
│    1   Quick Start     8,000   $0.36   55.0     55      1.1   │
│ >> 2   Standard       12,000   $0.54   32.0     75      1.6   │  (RECOMMENDED)
│    3   Comprehensive  16,000   $0.72   18.0     92      1.4   │
└────────────────────────────────────────────────────────────────┘

User selects: [r] for recommended (Path 2)
```

**Execution**:
```
Question 1: "What are the primary goals of your project?"
  → Covers: goals
  → From: Path B Standard, node "core_questions"

Question 2: "What are your key requirements?"
  → Covers: requirements
  → From: Path B Standard, node "core_questions"

Question 3: "What technologies will you use?"
  → Covers: tech_stack
  → From: Path B Standard, node "core_questions"

Question 4: "What constraints do you have?"
  → Covers: constraints
  → From: Path B Standard, node "core_questions"

Question 5: "What's your timeline?"
  → Covers: timeline
  → From: Path B Standard, node "core_questions"

Node complete → Advance to "analysis" node → Process responses → END

Result:
  Actual tokens: 12,400 (3.3% over estimate)
  Coverage: 67% (close to estimate)
  Rework needed: No (proceeded to Analysis phase successfully)
```

### Scenario 2: Design Phase - Minimize Risk Strategy

**Setup**:
- Project in Design phase
- Complex technical requirements identified
- Strategy: MINIMIZE_RISK (user changed from default)

**Workflow Definition**:
```
Path A (Rapid Prototyping):
  - High-level architecture sketch
  - 6,000 tokens, 50% technical coverage
  - Risk: 65 (many unknowns)

Path B (Iterative Design):
  - Multiple refinement cycles
  - 15,000 tokens, 75% technical coverage
  - Risk: 35 (moderate validation)

Path C (Formal Design):
  - Comprehensive specs, validation, review
  - 25,000 tokens, 95% technical coverage
  - Risk: 15 (highly validated)
```

**Optimization**:
```
QC Analysis (MINIMIZE_RISK strategy):
  Path A: Risk=65 → REJECTED (too high)
  Path B: Risk=35 → ACCEPTABLE (moderate)
  Path C: Risk=15 → OPTIMAL (lowest risk)

Recommendation: Path C (Formal Design)
Reason: User selected MINIMIZE_RISK strategy, cost is secondary
```

**User Approval**:
```
User sees recommended Path C but chooses Path B:
Rationale: "Risk 35 is acceptable for our use case, cost savings worth it"

System: Allows user override, proceeds with Path B
```

### Scenario 3: Backward Compatibility - Existing Project

**Setup**:
- Project created before workflow optimization feature
- `use_workflow_optimization` not set (defaults to False)
- Legacy behavior expected

**Execution**:
```
SocraticCounselor._generate_question():
    if project.metadata.get("use_workflow_optimization", False):
        # NOT SET - defaults to False
        return _generate_question_legacy(project)  # OLD BEHAVIOR

_generate_question_legacy():
    # Original greedy question generation
    # No workflow optimization
    # No approval blocking
    # Questions chosen one-at-a-time for immediate informativeness
```

**Result**: Existing projects continue working exactly as before, no behavior change.

---

## Architecture Details

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                              │
│                      "Generate question"                          │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                   SOCRATIC COUNSELOR AGENT                        │
│  • Check: workflow_optimization_enabled?                          │
│  • Check: active_workflow_execution exists?                       │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                 ┌────────┴────────┐
                 │                 │
          [NO EXECUTION]    [HAS EXECUTION]
                 │                 │
                 ▼                 ▼
┌───────────────────────┐  ┌──────────────────────┐
│ INITIATE APPROVAL     │  │ GENERATE FROM PATH   │
│ (BLOCKING)            │  │ (CONSTRAINED)        │
└────────┬──────────────┘  └──────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    QUALITY CONTROLLER AGENT                       │
│  • Receive workflow definition                                    │
│  • Create approval request                                        │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                     WORKFLOW OPTIMIZER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐          │
│  │ PATH FINDER  │→ │COST CALCULATOR│→ │RISK CALCULATOR│          │
│  │   (DFS)      │  │ (Token sums)  │  │(Gap analysis) │          │
│  └──────────────┘  └──────────────┘  └───────────────┘          │
│                          ↓                                        │
│              ┌─────────────────────┐                             │
│              │ PATH SELECTOR       │                             │
│              │ (Strategy-based)    │                             │
│              └──────────┬──────────┘                             │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│              CREATE WORKFLOW APPROVAL REQUEST                     │
│  • Store as pending                                               │
│  • Emit WORKFLOW_APPROVAL_REQUESTED event                         │
│  • Return status="pending_approval" (BLOCKS EXECUTION)            │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                 ┌────────┴────────┐
                 │                 │
             [CLI MODE]        [API MODE]
                 │                 │
                 ▼                 ▼
┌─────────────────────────┐  ┌──────────────────────┐
│ WORKFLOW COMMANDS       │  │ WEBSOCKET EVENT      │
│ • Display table         │  │ • Notify frontend    │
│ • Get user input        │  │ • Fetch pending      │
│ • Submit approval       │  │ • Display UI         │
└────────┬────────────────┘  └──────┬───────────────┘
         │                          │
         └────────┬─────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────────────────────┐
│           QUALITY CONTROLLER - APPROVE WORKFLOW                   │
│  • Validate approval request                                      │
│  • Create WorkflowExecutionState                                  │
│  • Store in project                                               │
│  • Emit WORKFLOW_APPROVED event                                   │
│  • Return success (UNBLOCKS EXECUTION)                            │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│            SOCRATIC COUNSELOR - RESUME EXECUTION                  │
│  • Read active_workflow_execution                                 │
│  • Use QuestionSelector with approved path                        │
│  • Generate questions constrained to current node                 │
│  • Track progress through path                                    │
│  • Advance nodes when complete                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. WorkflowBuilder (`workflow_builder.py`)
- **Purpose**: Create workflow definitions with fluent API
- **Methods**: `add_node()`, `add_edge()`, `set_entry()`, `add_exit()`, `build()`
- **Factory Methods**: `create_discovery_workflow_simple()`, `create_discovery_workflow_comprehensive()`

#### 2. WorkflowPathFinder (`workflow_path_finder.py`)
- **Purpose**: Enumerate all valid paths through workflow graph
- **Algorithm**: Depth-First Search with cycle detection
- **Input**: WorkflowDefinition
- **Output**: List[WorkflowPath] with complete node/edge sequences

#### 3. WorkflowCostCalculator (`workflow_cost_calculator.py`)
- **Purpose**: Estimate API token costs for each path
- **Constants**: Token costs per operation type
- **Calculation**: Sum node tokens + edge costs, convert to USD

#### 4. WorkflowRiskCalculator (`workflow_risk_calculator.py`)
- **Purpose**: Assess multi-dimensional risk for each path
- **Components**: Incompleteness (40%), Complexity (30%), Rework (30%)
- **Output**: Weighted risk score + breakdown

#### 5. WorkflowOptimizer (`workflow_optimizer.py`)
- **Purpose**: Orchestrate path finding, cost/risk calculation, selection
- **Process**: Enumerate → Calculate → Select → Create approval request
- **Strategies**: MINIMIZE_COST, MINIMIZE_RISK, BALANCED, MAXIMIZE_QUALITY, USER_CHOICE

#### 6. QuestionSelector (`question_selector.py`)
- **Purpose**: Generate questions aligned with approved path
- **Constraint**: Only ask questions for categories in current node's target list
- **Prevents**: Deviation from approved path

#### 7. WorkflowCommands (`workflow_commands.py`)
- **Purpose**: CLI interface for workflow approval
- **Display**: Path comparison table with metrics
- **Input**: User selection (path number, recommended, cancel)

#### 8. Workflow API Router (`workflow.py`)
- **Endpoints**:
  - `GET /pending-approvals/{project_id}` - Fetch pending approvals
  - `POST /approve` - Submit approval decision
  - `POST /reject` - Reject workflow and request alternatives

### Database Schema Changes

**ProjectContext** (`project.py`):
```python
@dataclass
class ProjectContext:
    # Existing fields...

    # NEW: Workflow optimization fields
    workflow_definitions: Dict[str, WorkflowDefinition] = field(default_factory=dict)
        # Key: phase name, Value: workflow definition for that phase

    workflow_approval_requests: List[WorkflowApprovalRequest] = field(default_factory=list)
        # History of all approval requests for this project

    active_workflow_execution: Optional[WorkflowExecutionState] = None
        # Current workflow being executed (if any)

    workflow_history: List[Dict[str, Any]] = field(default_factory=list)
        # Completed workflows with actual vs estimated metrics
```

**Event Types** (`event_types.py`):
```python
# NEW: Workflow lifecycle events
WORKFLOW_APPROVAL_REQUESTED = "workflow.approval.requested"
WORKFLOW_APPROVED = "workflow.approved"
WORKFLOW_REJECTED = "workflow.rejected"
WORKFLOW_NODE_ENTERED = "workflow.node.entered"
WORKFLOW_NODE_COMPLETED = "workflow.node.completed"
```

---

## Migration Path

### For Existing Projects

**Default Behavior**: Workflow optimization **disabled** by default

```python
project.metadata.get("use_workflow_optimization", False)  # Returns False
```

All existing projects continue using legacy (greedy) question generation with no changes.

### Enabling Workflow Optimization

**Option 1: Per-Project Flag**

```python
project.metadata["use_workflow_optimization"] = True
database.save_project(project)
```

**Option 2: CLI Command** (future feature)

```bash
/project optimize enable
```

**Option 3: Project Template** (future feature)

```bash
/new project --template=optimized
```

### Gradual Rollout

**Stage 1: Opt-In Beta**
- Available for new projects only
- Existing projects unchanged
- Monitor: token savings, user satisfaction, approval friction

**Stage 2: Selective Rollout**
- Recommend for projects with high token usage
- Provide migration guide
- Collect feedback

**Stage 3: Default Enabled**
- New projects have optimization enabled by default
- Existing projects remain opt-in
- Provide disable option for edge cases

---

## Summary

### Current Quality Controller (Before)

✅ **Measures** phase maturity
✅ **Warns** about low scores
✅ **Reports** category breakdowns
❌ **Does NOT block** execution
❌ **Does NOT compare** alternative paths
❌ **Does NOT control** question generation

### Future Quality Controller (After)

✅ **Measures** phase maturity (retained)
✅ **Warns** about low scores (retained)
✅ **Reports** category breakdowns (retained)
✅ **Enumerates** all possible workflow paths
✅ **Calculates** cost (tokens) and risk (gaps, rework) for each path
✅ **Recommends** optimal path based on strategy
✅ **Blocks** execution until user approves a path
✅ **Constrains** question generation to approved path
✅ **Prevents** greedy algorithm behavior

### The Cause (Why It Exists)

Agents exhibit **greedy algorithm behavior**: making locally-optimal decisions without considering global consequences. This leads to:

- **Suboptimal paths**: Easy questions → expensive overall workflow
- **High costs**: More API tokens than necessary
- **High risk**: Specification gaps requiring rework
- **Wasted effort**: Backtracking and re-asking questions

**Solution**: Quality Controller as Workflow Optimizer forces agents to:
1. **Plan ahead**: Enumerate all possible paths before starting
2. **Compare alternatives**: Calculate cost/risk for complete workflows
3. **Commit**: Approve one path and stick to it
4. **Execute strategically**: Follow the globally-optimal plan, not greedy shortcuts

**Result**: 15-25% cost reduction, 30-40% rework reduction, better project outcomes.
