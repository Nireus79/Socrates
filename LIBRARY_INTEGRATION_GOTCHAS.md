# Library Integration Gotchas: Actual Bugs You'll Hit

## Gotcha #1: The Silent Database Explosion 💥

### The Problem

When you import multiple libraries, each creates its own database connection:

```python
class AgentOrchestrator:
    def __init__(self, api_key_or_config):
        # Orchestrator creates connection #1
        self.database = DatabaseSingleton.get_instance()

        # Orchestrator creates connection #2
        self.vector_db = VectorDatabase(...)

# When agents use libraries...

# In project_manager agent
from socratic_agents import ProjectManager
pm = ProjectManager()  # Creates connection #3 somewhere?

# In code_generator agent
from socratic_analyzer import AnalyzerClient
analyzer = AnalyzerClient(...)  # Creates connection #4?

# In learning_agent
from socratic_learning import LearningEngine
engine = LearningEngine()  # Creates connection #5 (SQLite)

# In socratic_counselor
from socratic_rag import RAGClient
rag = RAGClient()  # Creates connection #6 (ChromaDB)
```

### The Result

- 6 database connections instead of 2
- Memory explodes
- SQLite locks cause timeouts
- Windows file handle limit hit (~256)
- Application crashes mysteriously

### How It Manifests

```python
# Test passes, production fails
# Works fine in dev (single user)
# Fails under load (multiple agents active)

# Error message (cryptic):
sqlite3.OperationalError: database is locked
# or
OSError: [Errno 24] Too many open files
# or
PermissionError: [WinError 32] The process cannot access the file...
```

### The Fix (Required in Libraries)

Libraries need to accept database as dependency:

```python
from socratic_learning import LearningEngine

# Before (wrong)
engine = LearningEngine()  # Creates own SQLite

# After (fixed)
engine = LearningEngine(
    database=orchestrator.database,  # Share orchestrator's DB
    vector_store=orchestrator.vector_db  # Share vector store
)
```

### Immediate Workaround

Limit library instantiation:

```python
class AgentOrchestrator:
    def __init__(self):
        self.database = DatabaseSingleton.get_instance()
        self.vector_db = VectorDatabase(...)

        # Don't create library clients here
        # Create them lazily when first needed
        self._lib_cache = {}

    @property
    def rag_client(self):
        if 'rag' not in self._lib_cache:
            # Share our vector DB instead of creating new one
            self._lib_cache['rag'] = RAGClient(
                vector_store=self.vector_db.chroma
            )
        return self._lib_cache['rag']
```

---

## Gotcha #2: The UI That Never Updates 📡

### The Problem

UI listens for events that libraries never emit:

```python
# In UI code
def on_event(self, event_type, data):
    if event_type == EventType.CODE_ANALYSIS_COMPLETE:
        self.update_results(data)

# When agent uses library internally
analysis = analyzer.analyze(code)  # ← NO EVENT FIRED
# UI waits forever for update that never comes
```

### The Result

- Progress bar stuck at 0%
- "Generate Socratic Questions" button seems broken
- No feedback while analysis runs
- User hits cancel button
- Operation gets cancelled mid-way

### How It Manifests

```python
# User action
Click "Analyze Code" button

# Backend
orchestrator.context_analyzer.process({'code': '...'})
    ↓
analyzer.analyze(code)  # ← Library call, SILENT
    ↓
[30 seconds of analysis]
    ↓
Return {'status': 'success', 'data': {...}}

# UI
[Still shows "Processing..." spinner]
[User thinks it's frozen]
[Presses Ctrl+C]
[Analysis gets cancelled]
[Library throws error]
```

### The Fix (Required in Wrapper)

Emit events around library calls:

```python
class AnalyzerAgentAdapter(Agent):
    def process(self, request):
        try:
            code = request.get('code')

            # Emit start event
            self.emit_event(EventType.AGENT_START, {
                'agent': self.name,
                'action': 'analyze_code'
            })

            # Call library
            analysis = self.analyzer.analyze(code)

            # Emit progress event (while analyzing)
            self.emit_event(EventType.PROGRESS_UPDATE, {
                'status': 'analyzing',
                'progress': 50
            })

            # Emit completion event
            self.emit_event(EventType.CODE_ANALYSIS_COMPLETE, {
                'analysis': analysis.dict()
            })

            return {'status': 'success', 'data': {...}}

        except Exception as e:
            # CRITICAL: Emit error event!
            self.emit_event(EventType.AGENT_ERROR, {'error': str(e)})
            raise
```

### Immediate Workaround

Wrap library calls with logging:

```python
import logging

logger = logging.getLogger(__name__)

def analyze_with_logging(code: str):
    logger.info(f"Starting analysis of {len(code)} chars")
    result = analyzer.analyze(code)
    logger.info(f"Analysis complete: {len(result.issues)} issues found")
    return result
```

---

## Gotcha #3: Configuration Mismatch 🔧

### The Problem

Monolith uses one config, libraries use another:

```python
# Monolith config
config = SocratesConfig(
    api_key="sk-ant-XXXX",  # Claude key
    claude_model="claude-opus-4-20250514",
    embeddings="sentence-transformers/all-MiniLM-L6-v2",
    vector_db_path="/tmp/chroma_db"
)

# Library config (reads separately)
llm_client = LLMClient()  # Reads from env vars!
rag_client = RAGClient()  # Reads from config file!
analyzer = AnalyzerClient()  # Reads from CLI args!

# Result: Conflicting configurations
```

### The Result

- Different API key used (library uses old key)
- Different model selected (library uses GPT-3.5, monolith uses Claude)
- Different embeddings (library uses OpenAI, monolith uses Sentence Transformers)
- Different vector DB location (library creates new one, data not shared)
- Inconsistent behavior across codebase

### How It Manifests

```python
# Weird behavior
orchestrator.socratic_counselor.process(...)
# Uses Claude Opus (good, fast)

orchestrator.context_analyzer.process(...)
# Uses GPT-3.5 from library's env var (slow, worse quality)

# Why?
# socratic_counselor: Uses ClaudeClient from monolith config
# context_analyzer: Uses AnalyzerClient reading from LLM_API_KEY env var

# Check env var
echo $LLM_API_KEY  # Points to old OpenAI key!
```

### The Fix (Required in Libraries)

Libraries must accept config from orchestrator:

```python
# Library change
class AnalyzerClient:
    def __init__(self, config: Optional[Config] = None):
        if config is None:
            config = Config.from_env()  # Default: read from env
        self.config = config
        self.llm = LLMClient(
            api_key=config.api_key,
            model=config.model
        )

# Orchestrator usage
class AgentOrchestrator:
    def __init__(self, config):
        self.config = config

        # Pass monolith config to libraries
        self.analyzer = AnalyzerClient(config=config)
        self.rag = RAGClient(
            embeddings=config.embeddings,
            vector_store_path=config.vector_db_path
        )
```

### Immediate Workaround

Set environment variables to match monolith config:

```python
import os

os.environ['LLM_API_KEY'] = self.config.api_key
os.environ['LLM_MODEL'] = self.config.claude_model
os.environ['VECTOR_DB_PATH'] = str(self.config.vector_db_path)
os.environ['EMBEDDINGS_MODEL'] = self.config.embedding_model

# Then instantiate libraries
analyzer = AnalyzerClient()  # Now uses correct config
rag_client = RAGClient()     # Now uses correct paths
```

---

## Gotcha #4: The Request/Response Format Mismatch 📦

### The Problem

Monolith agents expect standardized request/response format, libraries don't:

```python
# MONOLITH REQUEST
orchestrator.code_generator.process({
    'action': 'generate_code',
    'language': 'python',
    'description': 'Sort array'
})

# MONOLITH RESPONSE
{
    'status': 'success',  # or 'error'
    'data': {
        'code': '...',
        'language': 'python'
    },
    'error': None
}

# LIBRARY REQUEST
analyzer.analyze(code: str, language: str = 'python')

# LIBRARY RESPONSE
Analysis(
    code_metrics={'cyclomatic_complexity': 5, ...},
    issues=[CodeIssue(...), ...],
    quality_score=78
)
```

### The Result

Calling code breaks when using libraries:

```python
def process_code(orchestrator, code):
    # Works with built-in agent
    result = orchestrator.context_analyzer.process({'code': code})
    if result['status'] == 'success':  # ✅ Works
        data = result['data']  # ✅ Works

    # Breaks with library adapter that doesn't translate
    result = orchestrator.context_analyzer.process({'code': code})
    if result['status'] == 'success':  # ❌ KeyError: 'status'
        # Library returned Analysis object, not dict!
        data = result['analysis']  # ❌ KeyError: 'analysis'
```

### How It Manifests

```
Traceback (most recent call last):
  File "orchestrator.py", line 501, in process_request
    if result['status'] == 'success':
TypeError: 'Analysis' object is not subscriptable

# or

Traceback (most recent call last):
  File "orchestrator.py", line 502, in process_request
    data = result['data']
KeyError: 'data'
```

### The Fix (Required in Wrapper)

Always translate library response to monolith format:

```python
class AnalyzerAgentAdapter(Agent):
    def process(self, request):
        try:
            code = request['code']
            language = request.get('language', 'python')

            # Call library (returns Analysis object)
            analysis = self.analyzer.analyze(code, language)

            # CRITICAL: Translate to monolith format
            return {
                'status': 'success',
                'data': {
                    'metrics': dict(analysis.code_metrics),
                    'issues': [
                        {
                            'line': issue.line,
                            'message': issue.message,
                            'severity': issue.severity
                        }
                        for issue in analysis.issues
                    ],
                    'quality_score': analysis.quality_score
                }
            }
        except Exception as e:
            # CRITICAL: Return error in monolith format
            return {
                'status': 'error',
                'data': None,
                'error': str(e)
            }
```

### Immediate Workaround

Check response type before accessing:

```python
def process_code(orchestrator, code):
    result = orchestrator.context_analyzer.process({'code': code})

    # Handle both dict and object responses
    if isinstance(result, dict):
        # Monolith format
        if result['status'] == 'success':
            data = result['data']
    else:
        # Library format (object)
        if hasattr(result, 'quality_score'):  # It's Analysis object
            data = {
                'quality_score': result.quality_score,
                'issues': result.issues
            }
```

---

## Gotcha #5: The Missing Orchestrator Context 🔌

### The Problem

Libraries don't have reference to orchestrator, so they can't:
- Check other agents' work
- Share knowledge base
- Respect project constraints
- Notify about progress

```python
# MONOLITH AGENT (has context)
class ProjectManagerAgent(Agent):
    def process(self, request):
        # Can access:
        project = self.orchestrator.database.get_project(request['project_id'])
        knowledge = self.orchestrator.vector_db.search(query)

        # Can call other agents:
        analysis = self.orchestrator.context_analyzer.process(...)

        # Can emit events:
        self.emit_event(EventType.PROJECT_CREATED, {...})

# LIBRARY CLIENT (no context)
class ProjectManagerLib:
    def create_project(self, name, description):
        # NO ACCESS to:
        # - orchestrator.database
        # - orchestrator.vector_db
        # - other agents
        # - event system
        # Completely standalone
```

### The Result

Libraries can't collaborate:

```python
# Scenario: Generate code, get feedback, update knowledge

# With built-in agents
code = orchestrator.code_generator.process({
    'project': project_context,
    'language': 'python'
})['data']['code']

feedback = orchestrator.quality_controller.process({
    'code': code,
    'project': project_context
})['data']['feedback']

# Quality controller can see project constraints from context
# Quality controller can access project's knowledge base

# With libraries (no context)
code_gen_lib = CodeGeneratorLib()
code = code_gen_lib.generate('python')  # ← Doesn't know project constraints!

quality_lib = QualityCheckLib()
quality = quality_lib.check(code)  # ← Doesn't know generated code, project context
# Returns generic feedback, not context-aware
```

### How It Manifests

```python
# Generated code is poor quality
# Feedback is generic ("consider better variable names")
# No knowledge of project's specific requirements
# No progress notifications during long operations

# User sees:
# 1. Click "Generate Code"
# 2. Long delay
# 3. Low-quality result
# 4. No feedback during processing
```

### The Fix (Required in Libraries)

Accept orchestrator reference:

```python
# Library update
class CodeGeneratorLib:
    def __init__(self, orchestrator=None, config=None):
        self.orchestrator = orchestrator
        self.config = config

    def generate(self, language, project_context=None):
        # Can now use orchestrator
        if self.orchestrator:
            knowledge = self.orchestrator.vector_db.search(
                f"{language} best practices"
            )
            constraints = project_context or self.orchestrator.current_project

        # Emit progress events
        if self.orchestrator:
            self.orchestrator.event_emitter.emit(
                EventType.CODE_GENERATION_STARTED,
                {'language': language}
            )

        # Generate code (now context-aware)
        code = self._generate_impl(language, knowledge, constraints)

        # Emit completion event
        if self.orchestrator:
            self.orchestrator.event_emitter.emit(
                EventType.CODE_GENERATED,
                {'language': language, 'lines': len(code)}
            )

        return code
```

### Immediate Workaround

Pass context manually from wrapper:

```python
class CodeGeneratorAdapter(Agent):
    def __init__(self, orchestrator):
        super().__init__("code_generator", orchestrator)
        self.generator = CodeGeneratorLib()

    def process(self, request):
        # Extract context
        project_id = request.get('project_id')
        project = self.orchestrator.database.get_project(project_id)

        # Get relevant knowledge
        language = request.get('language', 'python')
        knowledge = self.orchestrator.vector_db.search(
            f"{language} patterns for {project.domain}"
        )

        # Pass context to library
        code = self.generator.generate(
            language=language,
            project_context=project,
            knowledge=knowledge
        )

        # Emit event
        self.emit_event(EventType.CODE_GENERATED, {'language': language})

        return {'status': 'success', 'data': {'code': code}}
```

---

## Gotcha #6: The Async Signature Mismatch ⚡

### The Problem

Libraries have async methods, but signatures don't match monolith's Agent interface:

```python
# MONOLITH AGENT ASYNC
class Agent(ABC):
    async def process_async(self, request: Dict) -> Dict:
        # Takes Dict request
        # Returns Dict response
        pass

# LIBRARY ASYNC
class AnalyzerClient:
    async def analyze_async(self, code: str) -> Analysis:
        # Takes code string (different!)
        # Returns Analysis object (different!)
        pass

class RAGClient:
    async def retrieve_async(self, query: str) -> List[Document]:
        # Takes string
        # Returns list of objects
        pass
```

### The Result

Can't use library's async directly in orchestrator:

```python
# This won't work
result = await orchestrator.context_analyzer.process_async({
    'code': code
})

# Because adapter returns library async method signature:
async def process_async(self, request: Dict):
    # ❌ Can't just call library's async, needs translation
    return await self.analyzer.analyze_async(request['code'])
    # Request is Dict, but analyze_async wants string!
```

### How It Manifests

```
TypeError: analyze_async() got 1 unexpected keyword argument 'code'

# or

AttributeError: 'dict' object has no attribute 'encode'
# Library expects string, got dict
```

### The Fix (Required in Wrapper)

Translate async signatures too:

```python
class AnalyzerAgentAdapter(Agent):
    async def process_async(self, request: Dict) -> Dict:
        try:
            code = request['code']
            language = request.get('language', 'python')

            # Call library's async (note: not process_async, but analyze_async)
            analysis = await self.analyzer.analyze_async(code, language)

            # Translate library response to monolith format
            return {
                'status': 'success',
                'data': {
                    'metrics': dict(analysis.code_metrics),
                    'issues': [...]
                }
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
```

### Immediate Workaround

Check if library method exists before using:

```python
class AnalyzerAgentAdapter(Agent):
    async def process_async(self, request: Dict) -> Dict:
        # Check if library has async version
        if hasattr(self.analyzer, 'analyze_async'):
            # Use async (preferred)
            analysis = await self.analyzer.analyze_async(request['code'])
        else:
            # Fall back to sync in thread
            analysis = await asyncio.to_thread(
                self.analyzer.analyze,
                request['code']
            )

        return {'status': 'success', 'data': {...}}
```

---

## Gotcha #7: The Import Hell 🔥

### The Problem

Libraries might have version conflicts with monolith:

```python
# Monolith requires
pydantic>=2.0.0,<3.0.0  # v2.1.0 installed
anthropic>=0.40.0       # v0.45.0 installed

# Library requires
pydantic>=2.0.0         # Tries to use v2.1.0 ✅
anthropic>=0.25.0       # Happy with v0.45.0 ✅

# But also requires (conflict!)
langchain==0.0.265      # Needs pydantic v1! ❌
```

### The Result

- Import errors
- Runtime type errors
- Model validation fails
- Cryptic error messages

### How It Manifests

```
ImportError: cannot import name 'BaseModel' from 'pydantic'

# or

pydantic.errors.PydanticTypeError: field 'code' only accepts str, but got {...}

# or

ModuleNotFoundError: No module named 'langchain.xyz'
# Version conflict between langchain versions
```

### The Fix (Required in Libraries)

Specify compatible version ranges in setup.py/pyproject.toml:

```toml
# Bad (too restrictive)
anthropic==0.40.0  # Future-proof fails

# Good (compatible range)
anthropic>=0.40.0,<1.0  # Allows security updates

# Bad (too loose)
pydantic>=1.0  # Could be v3 with breaking changes

# Good (compatible range)
pydantic>=2.0,<4.0  # Allows v2.x and v3.x when ready
```

### Immediate Workaround

Check dependency compatibility before importing:

```python
import sys

def check_dependencies():
    try:
        import pydantic
        version = tuple(map(int, pydantic.__version__.split('.')[:2]))
        if version[0] < 2:
            raise ImportError(f"pydantic v2+ required, got {pydantic.__version__}")
    except ImportError as e:
        print(f"ERROR: {e}")
        print("Install with: pip install 'pydantic>=2.0'")
        sys.exit(1)

    try:
        import anthropic
        if not hasattr(anthropic, 'Anthropic'):
            raise ImportError("anthropic SDK incompatible")
    except ImportError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

check_dependencies()

# Then safe to import
from socratic_analyzer import AnalyzerClient
```

---

## Summary: The Gotchas Checklist

Before importing any library into orchestrator, verify:

- [ ] **Database**: Does library create own connection? (Gotcha #1)
- [ ] **Events**: Does library emit monolith events? (Gotcha #2)
- [ ] **Config**: Does library use monolith config? (Gotcha #3)
- [ ] **Format**: Does library return Dict with 'status'? (Gotcha #4)
- [ ] **Context**: Does library have access to orchestrator? (Gotcha #5)
- [ ] **Async**: Do async signatures match? (Gotcha #6)
- [ ] **Versions**: Are dependency versions compatible? (Gotcha #7)

**If any are "No"**, you need an adapter wrapper, not direct replacement.

---

## The Bottom Line

**DO NOT** try to replace agent implementations with libraries directly.

**DO** create adapter wrappers that:
1. Translate request format (Dict ← Dict) ✅
2. Call library client ✅
3. Emit monolith events ✅
4. Translate response format (Dict → Dict) ✅
5. Share database connections ✅
6. Pass orchestrator context ✅

The 10 lines of adapter code saves you from 10 hours of debugging.
