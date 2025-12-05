# User Guide - Socratic RAG System

Complete guide for end users on how to use the Socratic RAG System effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Your First Project](#creating-your-first-project)
3. [The Socratic Dialogue](#the-socratic-dialogue)
4. [Project Management](#project-management)
5. [Code Generation](#code-generation)
6. [Knowledge Management](#knowledge-management)
7. [Collaboration](#collaboration)
8. [Tips & Best Practices](#tips--best-practices)
9. [Common Commands](#common-commands)

---

## Getting Started

### Launching Socrates

```bash
# Activate virtual environment (if needed)
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Start the system
python Socrates.py
```

You'll see the banner and authentication prompt:
```
╔══════════════════════════════════════════════════════╗
║         🤔 Socratic RAG System                       ║
║      Version 7.0 - "Know Thyself"                    ║
╚══════════════════════════════════════════════════════╝

Username: alice
Password: ****
```

### Login or Create Account

**First time?** Answer `y` when asked "New user?":
```
Username: alice
New user? (y/n): y
Create passcode: (enter secure passcode)
```

**Returning user?** Just enter your existing credentials.

### Main Menu

After authentication:
```
Welcome, alice!

🎯 Available Actions:
   /project create    - Start a new project
   /project list      - View your projects
   /continue          - Resume a project
   /help              - Show all commands
```

---

## Creating Your First Project

### Step 1: Create Project

```bash
/project create
```

Follow the prompts:
```
Project name: My Mobile App
```

Project created! You're now in the **Discovery Phase**.

### Step 2: Discovery Phase

The system asks clarifying questions to understand your project:

```
🤔 What specific problem or frustration in people's daily lives
   are you hoping this project will solve, and how did you first
   become aware that this problem exists?

Your response (or use /done, /advance, /help, /back, /exit):
> People spend too much time organizing their photos. I realized this
> when my grandmother couldn't find photos from her vacation.
```

**Key concepts in Discovery:**
- **Problem**: What problem does it solve?
- **Target Users**: Who are the users?
- **Success Metrics**: How will you measure success?

**Commands during dialogue:**
- `/done` - Finish with current phase
- `/continue` - Get next question
- `/hint` - Get help with current question
- `/advance` - Move to next phase (when ready)
- `/back` - Revert last response
- `/exit` - Exit without saving

### Step 3: Respond to Questions

Type detailed responses - the more specific, the better:

```
> People spend too much time organizing photos. Users could benefit from
> automatic organization by date, location, and people. My grandmother
> needs this to find family photos easily.
```

The system:
1. Analyzes your response
2. Extracts key information (goals, requirements, tech preferences)
3. Detects any conflicts or contradictions
4. Moves to next question

### Step 4: Progress Through Phases

Projects advance through 4 phases:

```
Phase 1: DISCOVERY
  ↓ Understand the problem and goals
Phase 2: ANALYSIS
  ↓ Define requirements and constraints
Phase 3: DESIGN
  ↓ Plan architecture and technology stack
Phase 4: IMPLEMENTATION
  ↓ Generate code and documentation
```

Advance using `/advance` when ready:
```
/advance

Advancing to Analysis phase...
Now focusing on: What features and requirements
does the system need to fulfill the goals?
```

---

## The Socratic Dialogue

### Understanding Questions

The system asks **guided questions** - not just any questions. Each is designed to:

1. **Clarify thinking** - What exactly do you mean?
2. **Uncover assumptions** - Have you considered...?
3. **Identify conflicts** - Do these contradict?
4. **Drive completeness** - What's missing?

### Example Dialogue Flow

**Discovery Phase - Question 1:**
```
What specific problem or frustration...?
> Auto-organize photos by date and people
```

**System extracts:**
- Goals: ✓ Photo organization
- Target users: ✓ Grandparents, busy professionals
- Key insight: ✓ Simplicity is critical

**Discovery Phase - Question 2:**
```
What assumptions are you making about your users?
> That they value simplicity over advanced features
```

**System checks for conflicts:**
- ✓ No conflicts detected
- ✓ Assumption aligned with previous goal

**Analysis Phase - Question 3:**
```
What specific features must the system have?
> 1. Auto-organize by date
> 2. Recognize people
> 3. Search by location
> 4. Share with family
```

**System extracts requirements** and **checks for conflicts**:
- Requirement: AI-based face recognition
- Requirement: Cloud storage for sharing
- ⚠️ Conflict: Privacy concern with face recognition + sharing

**Conflict Resolution:**
```
CONFLICT DETECTED!
  Feature: Face recognition for people
  Feature: Share with family
  Issue: Privacy - might share biometric data

How would you like to resolve this?
> I'll add explicit consent before sharing
```

### Getting Hints

Stuck on a question?

```
/hint
```

The system provides:
- **Phase context** - What phase are you in and why
- **Question intent** - What the question is trying to uncover
- **Example answer** - Pattern of good responses
- **Relevant knowledge** - Related information from knowledge base

```
Phase: Discovery
Question Intent: Understand the core problem being solved
Example: "People waste 30 minutes weekly searching for photos..."
Related Knowledge: User persona development, problem statement definition
```

### Viewing Conversation History

See everything discussed so far:

```
/prompt
```

Shows:
- Current project name and phase
- All Q&A exchanges so far
- Extracted insights (goals, requirements, etc.)
- Identified conflicts

---

## Project Management

### List Your Projects

```bash
/project list
```

Output:
```
Your Projects:
  1. My Mobile App        Phase: Design      Progress: 60%
  2. Website Redesign     Phase: Discovery   Progress: 20%
  3. API Backend          Phase: Implementation (archived)

Use /project load <name> to continue
```

### Load a Project

Resume where you left off:

```bash
/project load "My Mobile App"

Loading project: My Mobile App
Current phase: Design
Progress: 60%

Next question:
🤔 What technologies will you use...?
```

### Archive a Project

Put project on hold:

```bash
/project archive "My Mobile App"

Project archived. Use /project restore to bring it back.
```

### Restore Archived Project

Resume archived work:

```bash
/project restore "My Mobile App"

Project restored and ready to continue.
```

### Delete a Project

Permanently remove (use with caution):

```bash
/project delete "My Mobile App"

⚠️ Are you sure? This cannot be undone.
Type the project name to confirm: My Mobile App

Project deleted permanently.
```

---

## Code Generation

### Generate Code

Once you've completed the Design phase, generate code:

```bash
/code generate
```

The system:
1. Gathers all project context
2. Builds comprehensive specification
3. Calls Claude AI to generate code
4. Returns production-ready code

```
Generating code for: My Mobile App
Using framework: React (from your tech stack)
Language: JavaScript
Estimated tokens: ~2000
Cost: ~$0.02

Generating... ⏳

✓ Code generated successfully!

// Generated code follows...
import React from 'react';
// ... complete, documented code
```

### Generate Documentation

Auto-generate project documentation:

```bash
/docs generate
```

Creates:
- Project README
- API documentation
- Setup instructions
- Architecture overview
- Deployment guide

---

## Knowledge Management

### Understanding the Knowledge Base

Socrates includes a semantic knowledge base covering:

**Programming**:
- Python (decorators, generators, async/await, type hints)
- JavaScript/TypeScript (promises, closures, ES6+)
- Web development (REST, databases, security)

**Professional**:
- Project management
- Team collaboration
- Business strategy
- Product management

**Design**:
- UX/UI design
- Visual design
- User research

**Writing**:
- Technical writing
- Documentation
- Communication

### Search Knowledge

Find relevant information:

```bash
/query ask "How do I implement user authentication?"
```

The system searches the knowledge base and provides:
- Relevant articles
- Best practices
- Code examples
- Related concepts

```
Found 3 relevant articles:

1. User Authentication Patterns
   - OAuth 2.0 flow
   - JWT tokens
   - Session management
   - Security best practices

2. Password Security
   - Hashing algorithms (bcrypt, argon2)
   - Salt and pepper
   - Password validation rules

3. Multi-factor Authentication
   - TOTP/HOTP tokens
   - SMS-based 2FA
   - Hardware security keys
```

### Import Documents

Add your own documents to knowledge base:

```bash
/document import path/to/your/document.pdf
/document import path/to/your/codebase
/document import path/to/guidelines.txt
```

Supported formats:
- PDF documents (text extracted automatically)
- Code files (.py, .js, .java, etc.)
- Text files (.txt, .md)
- Documentation

Imported documents are:
- Converted to embeddings
- Indexed for semantic search
- Made available throughout dialogue
- Project-specific if loaded within project context

### View Imported Documents

```bash
/document list

Imported Documents:
  1. company_guidelines.pdf     (5 pages)
  2. architecture.md            (2 sections)
  3. api_spec.json              (15 endpoints)
```

---

## Collaboration

### Add Collaborators

Invite others to work on your project:

```bash
/add_collaborator "team_member_username"
```

Collaborator can now:
- View project details
- Continue dialogue
- See generated code
- Add notes
- Access knowledge base

### List Collaborators

See who's working on project:

```bash
/list_collaborators

Collaborators on "My Mobile App":
  - alice (owner)
  - bob (contributor)
  - charlie (contributor)
```

### Remove Collaborator

```bash
/remove_collaborator bob

Removed bob from project.
```

---

## Project Notes & Annotations

### Add a Note

Capture decisions, ideas, and blockers:

```bash
/note add "Design Decision: Using React hooks for state management"
```

Note types:
- `design` - Architecture decisions
- `bug` - Issues found
- `idea` - Feature ideas
- `task` - Action items
- `general` - General notes

```bash
/note add --type design "Using microservices for scalability"
/note add --type bug "Login fails with special characters"
/note add --type idea "Add dark mode theme"
/note add --type task "Setup CI/CD pipeline"
```

### List Notes

View all project notes:

```bash
/note list

Project Notes:
  1. [DESIGN] Using React hooks for state
  2. [TASK] Setup CI/CD pipeline
  3. [BUG] Login fails with special chars
  4. [IDEA] Add dark mode theme
```

Filter by type:

```bash
/note list --type task

Tasks:
  1. Setup CI/CD pipeline
  2. Write API tests
  3. Deploy to production
```

### Search Notes

```bash
/note search "authentication"

Found 2 notes containing "authentication":
  1. [DESIGN] OAuth 2.0 for authentication flow
  2. [BUG] Google OAuth integration failing
```

### Delete a Note

```bash
/note delete 1

Note deleted.
```

---

## Tips & Best Practices

### 1. Be Specific in Responses

**❌ Vague**:
```
> It's an app for social media
```

**✅ Specific**:
```
> A photo-sharing app for family members ages 60+ to easily
> find and share memories. Users should be able to upload photos,
> auto-organize by date/location, and invite family members
> to shared albums without complex privacy settings.
```

More detail → Better conflicts detected → Better code generated

### 2. Complete All Phases

Each phase builds on previous:
- **Discovery**: Define the problem
- **Analysis**: Specify requirements
- **Design**: Plan the solution
- **Implementation**: Generate code

Skipping phases = incomplete specification = poor code

### 3. Use Hints When Stuck

Don't guess at question intent:

```
/hint
```

Hints provide:
- Phase context
- What the question is trying to uncover
- Example responses
- Relevant knowledge articles

### 4. Review Conflict Detections

Pay attention when conflicts detected:

```
⚠️ CONFLICT DETECTED!
  Requirement: Support 10,000 users
  Constraint: $50/month budget
  Issue: Scalability vs. cost
```

Resolve proactively - don't ignore!

### 5. Leverage Knowledge Base

When uncertain about technology choices:

```
/query ask "Should I use SQL or NoSQL for this project?"
/query ask "What are the pros/cons of different deployment options?"
```

Knowledge base provides best practices, not marketing hype.

### 6. Document Decisions in Notes

Keep track of why you decided things:

```
/note add --type design "Chose PostgreSQL over MongoDB because of ACID
guarantees and relational data needs (users, photos, albums, permissions)"
```

Helps future team members understand reasoning.

### 7. Use Natural Language

You can use plain English instead of slash commands (if enabled):

```
How do I set up authentication?
```

Instead of:
```
/query ask "How do I set up authentication?"
```

Enable/disable NLU:
```
/nlu enable    # Use plain English
/nlu disable   # Use /slash commands only
```

### 8. Save Your Work

Always complete or save before exiting:

```
/done      # Complete phase
/continue  # Get next question
/advance   # Move to next phase
/exit      # Exit and save
```

### 9. Collaborate Early

Invite team members to provide perspectives:

```
/add_collaborator team_member
```

More eyes catch:
- Missing requirements
- Unrealistic timelines
- Technology mismatches
- Better solutions

### 10. Review Generated Code

Generated code is starting point, not final:

```
/code generate
```

Always:
- Review for correctness
- Add error handling
- Add tests
- Check security
- Optimize performance

---

## Common Commands

### Project Commands
```bash
/project create      # Create new project
/project list        # List all projects
/project load NAME   # Load existing project
/project archive     # Archive current project
/project restore     # Restore archived project
/project delete      # Delete project permanently
```

### Dialogue Commands
```bash
/continue           # Get next question
/advance            # Advance to next phase
/hint               # Get help with current question
/done               # Complete current phase
/back               # Revert last response
```

### Code & Documentation
```bash
/code generate      # Generate code
/docs generate      # Generate documentation
```

### Knowledge
```bash
/query ask "..."    # Ask knowledge base
/document import    # Import file/document
/document list      # List imported documents
/knowledge add      # Add custom knowledge
```

### Collaboration
```bash
/add_collaborator   # Add team member
/list_collaborators # View collaborators
/remove_collaborator# Remove from project
```

### Notes
```bash
/note add           # Create note
/note list          # List all notes
/note search        # Search notes
/note delete        # Delete note
```

### System
```bash
/help               # Show all commands
/help COMMAND       # Show help for specific command
/status             # System status & token usage
/info               # System information
/debug on|off       # Toggle debug logging
/logs [N]           # View last N log lines
/prompt             # Show current project summary
/clear              # Clear screen
```

### Account
```bash
/logout             # Logout from account
/exit               # Exit system
```

---

## Project Types & Knowledge Domains

Socratic supports projects across multiple domains:

### Programming
- Python projects (backend, data science, automation)
- JavaScript/TypeScript projects (web, Node.js)
- Web development
- API development
- DevOps & deployment

### Design
- UX/UI design projects
- User research
- Visual design

### Business
- Product management
- Project management
- Team collaboration
- Business strategy

### Content
- Technical writing
- Documentation
- Content creation

### Process
- Problem solving
- Analysis techniques
- Research methods

Choose the domain relevant to your project, and Socrates will emphasize relevant knowledge.

---

## Troubleshooting

### Project Won't Load

```bash
/project list       # Verify project exists
/project load NAME  # Try exact name
/status             # Check system status
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for details.

### Questions Keep Repeating

Usually means phase not advancing properly:

```
/advance            # Manually advance phase
```

If issue persists, reset dialogue:
```
/back               # Revert responses
/continue           # Get fresh questions
```

### Generated Code Incomplete

Code generation uses project context. Improve by:

```bash
/prompt             # Review your project specification
/continue           # Answer more detailed questions
/advance            # Complete remaining phases
/code generate      # Try again with complete context
```

---

## Advanced Usage

### Natural Language Understanding

Enable plain English commands:

```bash
/nlu enable
```

Now you can use natural language:
```
Create a new project called "Blog Platform"
What features do I need for authentication?
Generate code for the backend
```

### Debug Mode

View detailed system logs:

```bash
/debug on
```

Logs show:
- Every API call
- Token usage
- Agent processing
- Knowledge base searches
- Event emissions

```bash
/logs 50            # View last 50 log lines
/logs               # View default 20 lines
```

### Token Tracking

Monitor API costs:

```bash
/status
```

Shows:
- Total tokens used
- Estimated cost
- API calls made
- Token warning threshold

Control costs:

```python
# In configuration
ConfigBuilder("api_key")
    .with_token_warning_threshold(0.5)  # Warn at 50% usage
```

---

## Getting Help

**In-system help**:
```bash
/help               # All commands
/help command_name  # Specific command
/hint               # Help with current phase
/info               # System information
```

**External help**:
- [ARCHITECTURE.md](ARCHITECTURE.md) - How system works
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [API_REFERENCE.md](API_REFERENCE.md) - Detailed API docs
- [CONFIGURATION.md](CONFIGURATION.md) - Customize behavior

---

**Last Updated**: December 2025
**Version**: 7.0
