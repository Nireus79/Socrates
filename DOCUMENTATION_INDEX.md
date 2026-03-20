# Documentation Index

Complete reference guide for all documentation files in the Socrates project.

## Quick Links

### Getting Started
- **README.md** - Project overview and setup instructions
- **QUICKSTART.md** - Quick start guide for new users
- **BEST_PRACTICES.md** - Development best practices and standards

### Code Quality & Maintenance
- **COMPREHENSIVE_FIXES_SUMMARY.md** - Summary of all 10 fixes implemented
- **REFACTORING_IMPROVEMENTS.md** - Large class refactoring documentation
- **MAGIC_STRINGS_REPORT.md** - Magic string identification report

### Development Guides
- **ERROR_HANDLING_GUIDE.md** - Exception handling patterns and best practices
- **ASYNC_PATTERNS_GUIDE.md** - Async/await patterns with examples
- **COMMAND_API_DOCUMENTATION.md** - Complete command API reference
- **SHELL_COMMAND_ALTERNATIVES.md** - Shell command security and alternatives
- **TODO_AND_FIXME_TRACKING.md** - Action items and GitHub issue suggestions

### Architecture & Design
- **CHANGELOG.md** - Version history and changes
- **MIGRATION_GUIDE.md** - Migration instructions for updates
- **DOCKER.md** - Docker deployment guide
- **INSTALL.md** - Installation instructions

## Documentation by Topic

### User Documentation
- QUICKSTART.md - Getting started as a user
- README.md - Project overview
- INSTALL.md - Installation guide

### Developer Documentation
- BEST_PRACTICES.md - Coding standards
- ERROR_HANDLING_GUIDE.md - Exception patterns
- ASYNC_PATTERNS_GUIDE.md - Async programming
- COMMAND_API_DOCUMENTATION.md - Command API
- SHELL_COMMAND_ALTERNATIVES.md - Security guide
- REFACTORING_IMPROVEMENTS.md - Code organization

### Project Management
- TODO_AND_FIXME_TRACKING.md - Action items
- COMPREHENSIVE_FIXES_SUMMARY.md - Fix tracking
- MAGIC_STRINGS_REPORT.md - Code quality report
- CHANGELOG.md - Version history

### Deployment
- DOCKER.md - Docker setup
- INSTALL.md - Installation
- MIGRATION_GUIDE.md - Upgrade guide

## File Organization

```
Socrates/
├── README.md                           # Project overview
├── QUICKSTART.md                       # Quick start guide
├── INSTALL.md                          # Installation guide
├── BEST_PRACTICES.md                   # Development standards
├── CHANGELOG.md                        # Version history
├── DOCKER.md                           # Docker guide
├── MIGRATION_GUIDE.md                  # Migration guide
│
├── CODE QUALITY & FIXES
├── COMPREHENSIVE_FIXES_SUMMARY.md      # Summary of 10 fixes
├── REFACTORING_IMPROVEMENTS.md         # Class refactoring
├── MAGIC_STRINGS_REPORT.md             # String extraction
│
├── DEVELOPMENT GUIDES
├── ERROR_HANDLING_GUIDE.md             # Exception handling
├── ASYNC_PATTERNS_GUIDE.md             # Async programming
├── COMMAND_API_DOCUMENTATION.md        # Command API
├── SHELL_COMMAND_ALTERNATIVES.md       # Security & alternatives
├── TODO_AND_FIXME_TRACKING.md          # Action items
│
├── SOURCE CODE
├── socratic_system/
│   ├── config/constants.py             # All constants
│   ├── ui/commands/                    # All command classes
│   ├── database/                       # Database operations
│   ├── orchestration/                  # Agent orchestration
│   └── utils/                          # Utility functions
└── tests/                              # Test suite
```

## How to Use This Documentation

### For New Developers
1. Start with **QUICKSTART.md**
2. Read **BEST_PRACTICES.md**
3. Review **COMMAND_API_DOCUMENTATION.md**
4. Study relevant guides (Error Handling, Async, etc.)

### For Code Review
1. Check **BEST_PRACTICES.md** for standards
2. Review **COMPREHENSIVE_FIXES_SUMMARY.md** for recent changes
3. Use **ERROR_HANDLING_GUIDE.md** for exception patterns
4. Reference **ASYNC_PATTERNS_GUIDE.md** for async code

### For Feature Development
1. Review **COMMAND_API_DOCUMENTATION.md** for command patterns
2. Follow **BEST_PRACTICES.md** for code organization
3. Use **ERROR_HANDLING_GUIDE.md** for exception handling
4. Reference **ASYNC_PATTERNS_GUIDE.md** if using async

### For Deployment
1. Follow **INSTALL.md** for setup
2. Review **DOCKER.md** for containerization
3. Check **MIGRATION_GUIDE.md** for updates
4. Consult **CHANGELOG.md** for version info

## Key Constants

All constants defined in: `socratic_system/config/constants.py`

### Timeout Constants
- GIT_OPERATION_TIMEOUT_SECONDS = 10
- GIT_VERSION_CHECK_TIMEOUT_SECONDS = 5
- SHELL_COMMAND_TIMEOUT_SECONDS = 30
- API_REQUEST_TIMEOUT_SECONDS = 30
- CLAUDE_API_TIMEOUT_SECONDS = 60
- DB_QUERY_TIMEOUT_SECONDS = 30

### Configuration
- MAX_DB_CONNECTIONS = 10
- MAX_CACHE_SIZE_MB = 100
- MAX_FILE_SIZE_MB = 10
- MAX_API_RETRIES = 3
- MAX_QUESTIONS_PER_SESSION = 50

### Thresholds
- TOKEN_WARNING_THRESHOLD = 50000
- MATURITY_THRESHOLD_HIGH = 20.0
- ENGAGEMENT_THRESHOLD_HIGH = 10
- VECTOR_SIMILARITY_THRESHOLD = 0.6

## Command Categories

All commands implement BaseCommand interface in: `socratic_system/ui/commands/`

### Project Management
- ProjectCreateCommand
- ProjectLoadCommand
- ProjectListCommand
- ProjectAnalyzeCommand
- ProjectTestCommand
- ProjectValidateCommand

### Analytics
- AnalyticsStatusCommand
- AnalyticsSummaryCommand
- AnalyticsTrendsCommand
- AnalyticsBreakdownCommand
- AnalyticsRecommendCommand

### Code Operations
- CodeGenerateCommand
- CodeDocsCommand

### Document Management
- DocImportCommand
- DocListCommand

### System Control
- HelpCommand
- ExitCommand
- BackCommand
- MenuCommand

## Performance Guidelines

### Database
- Use connection pooling (MAX_DB_CONNECTIONS)
- Set query timeouts (DB_QUERY_TIMEOUT_SECONDS)
- Implement caching for hot data
- See: connection_pool.py, query_profiler.py

### API Calls
- Always set timeouts (API_REQUEST_TIMEOUT_SECONDS)
- Implement retry logic (MAX_API_RETRIES)
- Use exponential backoff
- See: ASYNC_PATTERNS_GUIDE.md

### Command Execution
- Validate arguments before processing
- Catch specific exceptions
- Log operations and errors
- Return consistent response format
- See: COMMAND_API_DOCUMENTATION.md

## Error Handling

See ERROR_HANDLING_GUIDE.md for comprehensive patterns.

### Exception Hierarchy
- GitInitializationError (git operations)
- GitOperationError (git commands)
- GitHubError (GitHub API)
- ModuleError (base for custom exceptions)

### Logging Levels
- DEBUG: Detailed diagnostic info
- INFO: Successful operations
- WARNING: Unexpected but recoverable
- ERROR: Serious problems
- CRITICAL: Fatal errors

## Testing

### Unit Tests
- Run: `pytest tests/`
- Coverage: `pytest --cov`

### Async Tests
- Use: `@pytest.mark.asyncio`
- Mock: `AsyncMock` from unittest.mock
- See: ASYNC_PATTERNS_GUIDE.md

### Integration Tests
- Test with real database
- Test with real API (mocked responses)
- Test command chains

## Additional Resources

### External Documentation
- Python async/await: https://docs.python.org/3/library/asyncio.html
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Git operations: https://gitpython.readthedocs.io/

### Code Examples
- See individual .md files for code samples
- Check test files for usage examples
- Review command classes for patterns

## Questions & Support

- Check relevant documentation file first
- Review similar code patterns
- Check existing issues/PRs
- Create GitHub issue for bugs/features

## Summary

This documentation set provides:
- 2,500+ lines of best practices
- 50+ code examples
- Complete API reference
- Troubleshooting guides
- Architecture documentation
- Performance optimization tips
- Security guidelines
- Testing strategies

All 10 major improvements documented and implemented.
