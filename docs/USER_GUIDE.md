# Socratic RAG Enhanced - User Guide

**Version:** 7.4.0
**Last Updated:** October 2024
**Audience:** End Users

## Table of Contents

1. [Getting Started](#getting-started)
2. [Projects](#projects)
3. [Socratic Sessions](#socratic-sessions)
4. [Code Generation](#code-generation)
5. [Repository Management](#repository-management)
6. [Document Management](#document-management)
7. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Accessing the Application
1. Navigate to your Socratic RAG Enhanced instance URL
2. Sign up for a new account or log in with existing credentials
3. Complete your profile setup
4. Start creating projects!

### Dashboard Overview
The Dashboard provides:
- **Quick stats** - Active projects, recent sessions, total generations
- **Recent activity** - Latest projects, sessions, and generated code
- **Quick actions** - Common tasks (New Project, New Session, Generate Code)
- **Analytics** - Usage trends and productivity metrics

---

## Projects

### Creating a Project

1. Click **"New Project"** on the dashboard
2. Fill in project details:
   - **Project Name** (required) - Descriptive name for your project
   - **Description** (optional) - What your project is about
   - **Project Type** - Select from: Web Application, Mobile App, API, Library, Microservice, etc.
   - **Framework** - Your preferred technology framework
   - **Complexity Level** - Beginner, Intermediate, Advanced

3. Click **"Create Project"**

### Managing Projects

#### View Project Details
- Click on any project card to view:
  - Project overview and description
  - All sessions within the project
  - Generated code and generations
  - Team members and collaborators
  - Project settings

#### Edit Project
1. Navigate to project detail page
2. Click **"Edit"** button
3. Update project information
4. Click **"Save Changes"**

#### Delete Project
1. Navigate to project detail page
2. Click **"Delete"** button
3. Confirm deletion (⚠️ This cannot be undone)

#### Add Collaborators
1. Go to project settings
2. Click **"Add Collaborator"**
3. Enter team member email
4. Select permission level:
   - **Owner** - Full access, can delete
   - **Editor** - Can create and modify content
   - **Viewer** - Read-only access
5. Click **"Invite"**

---

## Socratic Sessions

### What is a Socratic Session?
A Socratic Session is an AI-guided learning experience where Claude asks you strategic questions to help you explore and develop your ideas about your project.

### Creating a Session

1. Navigate to your project
2. Click **"New Socratic Session"** or **"New Session"**
3. Configure your session:
   - **Session Name** - What to call this session
   - **Your Role** - Choose your perspective:
     - Developer - Focus on technical implementation
     - Project Manager - Focus on planning and coordination
     - Designer - Focus on UX/UI
     - QA Tester - Focus on quality and testing
     - Business Analyst - Focus on requirements
     - DevOps Engineer - Focus on deployment
     - Solution Architect - Focus on system design
   - **Project Context** - Select the associated project
   - **Initial Idea** - Describe what you want to explore

4. Click **"Start Session"**

### During a Session

#### Message Input
- Type your response or answer in the message box
- Press **Enter** (or Shift+Enter for new line) to send
- Use **quick response suggestions** for common answers

#### Session Controls
- **Mode Toggle** - Switch between Socratic (questions) and Chat (free conversation)
- **Pause** - Temporarily pause the session
- **Resume** - Continue a paused session
- **Export** - Download session as JSON
- **Complete** - Mark session as complete when done

#### Session Info
- View **progress percentage** showing conversation depth
- See **current phase** indicator
- Check **statistics** (questions asked, responses received)
- View **timestamps** for each exchange

### Session Best Practices

✅ **Do:**
- Be specific about your project needs
- Ask clarifying questions when needed
- Explore multiple perspectives before deciding
- Save important insights by exporting sessions

❌ **Don't:**
- Rush through the questioning process
- Ignore edge cases or concerns raised
- Skip non-functional requirements
- Move forward without addressing identified risks

---

## Code Generation

### Generating Code

1. Navigate to your project
2. Click **"Generate Code"** or **"New Generation"**
3. Configure generation parameters:
   - **Generation Name** - What to call this generation
   - **Architecture Pattern** - Select: MVC, REST API, Microservices, Monolith, Serverless
   - **Generation Type** - Full Project or Specific Component
   - **Primary Language** - Python, JavaScript, Java, Go, Rust, etc.
   - **Backend Framework** - Django, FastAPI, Express, Spring, etc.
   - **Frontend Framework** - React, Vue, Angular, Svelte, etc.
   - **Database** - PostgreSQL, MongoDB, Redis, etc.
   - **Additional Features**:
     - ✓ Authentication & Authorization
     - ✓ API Documentation
     - ✓ Unit Tests
     - ✓ Docker Configuration
     - ✓ CI/CD Configuration

4. Click **"Generate Code"**

### During Generation

#### Progress Tracking
- Overall progress bar shows generation status
- File counter displays (X of Y files generated)
- Stage indicators show current phase:
  1. Planning architecture
  2. Generating files
  3. Creating documentation
  4. Finalizing project

#### Real-Time Updates
- Progress updates every 2 seconds
- Page automatically refreshes when complete
- Notification appears on completion

### Viewing Generated Code

1. Once generated, navigate to the **Code Viewer**
2. **File tree** on left shows project structure
3. **Code editor** displays file contents with:
   - Syntax highlighting
   - Line numbers
   - Dark mode support
4. **File actions**:
   - **Copy** - Copy code to clipboard
   - **Download** - Download individual file

### Downloading Generated Code

#### Download Individual File
1. Select file in code viewer
2. Click **"Download"** button
3. File saves to your downloads folder

#### Download All Files
1. Click **"Download All"** button in generation header
2. Creates ZIP file with all generated code
3. Filename format: `project_name_generation_name_YYYYMMDD.zip`

#### Export Configuration
- Export generation metadata as JSON
- Includes specifications, settings, metadata
- Useful for documentation and archival

---

## Repository Management

### Importing a Repository

1. Click **"Import Repository"** from sidebar
2. Enter repository details:
   - **Repository URL** - HTTPS or SSH URL from GitHub, GitLab, Bitbucket, or any Git host
   - **Branch** (optional) - Specific branch to import (defaults to main/master)
   - **Project** (optional) - Associate with existing project
   - **Vectorization** (✓ recommended) - Enable RAG for AI Q&A

3. Click **"Import Repository"**

#### Supported Platforms
- ✅ GitHub (public & private)
- ✅ GitLab (cloud & self-hosted)
- ✅ Bitbucket (cloud & server)
- ✅ Any Git repository (with HTTPS/SSH access)

### What Gets Analyzed

During import, the system analyzes:
- **Languages** - 30+ programming languages detected
- **Frameworks** - Popular frameworks identified
- **Dependencies** - requirements.txt, package.json, go.mod, etc.
- **Project Structure** - Source, tests, configs, documentation
- **Code Metrics** - File count, line count, complexity

### Repository Details

View comprehensive analysis:
- **Total Files** - Number of source files
- **Lines of Code** - Total LOC across repository
- **Vector Chunks** - Number of code segments for RAG search
- **Primary Language** - Most used language
- **Code Complexity** - Low, Medium, or High

### Repository Actions

#### Ask AI About Code
1. Open repository details
2. Click **"Ask AI About This Code"**
3. Create new Socratic session with repository context
4. Ask questions about the codebase
5. Get AI-powered answers based on actual code

#### Re-import Repository
1. Click **"Re-import Repository"**
2. Updates analysis with latest code
3. Useful for tracking changes over time

#### Export Analysis
1. Click **"Export Analysis"**
2. Downloads analysis report as JSON
3. Includes: languages, frameworks, dependencies, metrics

#### Delete Repository
1. Click **"Delete Repository"**
2. Confirm deletion
3. ⚠️ Removes all analysis data and vectors

---

## Document Management

### Uploading Documents

1. Click **"Upload Document"** from sidebar
2. Select document file:
   - **Supported formats**: PDF, DOCX, TXT, Markdown, Python, JavaScript, HTML, CSS

3. Provide details:
   - **Document Name** (auto-filled from filename)
   - **Project** (optional) - Associate with a project

4. Click **"Upload Document"**

### Upload Progress

During upload, you'll see:
1. **Upload Stage** - File uploading to server
2. **Processing Stage** - Content extraction (PDF → text, DOCX → paragraphs)
3. **Vectorization Stage** - Converting text to embeddings for RAG

### Using Uploaded Documents

#### In Socratic Sessions
- References to uploaded documents appear in session context
- AI can reference specific sections and content
- Allows learning from documentation

#### In Code Generation
- Document content influences code structure
- API documentation can be generated from specifications
- Requirements from documents guide generation

#### Search & Reference
- Search uploaded documents by content
- View document processing summary
- Track document usage across projects

---

## Tips & Best Practices

### For Effective Socratic Sessions

1. **Start with a Clear Goal**
   - Define what you want to achieve
   - Set realistic scope
   - Identify key stakeholders

2. **Engage with Questions**
   - Don't just give one-word answers
   - Explain your reasoning
   - Challenge assumptions when appropriate

3. **Document Important Decisions**
   - Export session when you reach conclusions
   - Keep notes of action items
   - Review sessions before implementation

4. **Use Different Roles**
   - Create multiple sessions with different perspectives
   - Compare insights from different roles
   - Use all perspectives to create holistic design

### For Code Generation

1. **Prepare Technical Specifications**
   - Run Socratic session first for clarity
   - Document all requirements
   - List architectural constraints

2. **Choose Appropriate Architecture**
   - Monolith: Small to medium projects
   - Microservices: Complex, distributed systems
   - Serverless: Event-driven, scalable functions
   - REST API: Standard web APIs

3. **Include Tests and Documentation**
   - Always enable test generation
   - Include API documentation
   - Generate Docker configuration for consistency

4. **Review and Customize**
   - Don't assume generated code is final
   - Review architecture and design decisions
   - Customize for your specific needs

### For Repository Analysis

1. **Import Representative Repositories**
   - Import similar projects for comparison
   - Analyze best-practice examples
   - Learn from established patterns

2. **Ask Specific Questions**
   - Ask about patterns and practices
   - Inquire about error handling
   - Explore testing strategies
   - Learn about dependencies

3. **Compare Multiple Repositories**
   - Different implementations of same problem
   - Different technology stacks
   - Best practices from industry

### Performance Tips

- ✅ Keep sessions focused and scoped
- ✅ Use vectorization for repositories you'll query frequently
- ✅ Export long sessions to archive them
- ✅ Delete old repositories no longer needed
- ✅ Use dark mode for reduced eye strain during long sessions

### Collaboration Tips

- Share generated code with team members via export
- Use project collaborators for team work
- Document decisions in session exports
- Create templates for common project types
- Review code with team before implementation

---

## Common Tasks

### Task: Design a Web Application
1. Create new project (Web Application type)
2. Create Socratic session (Developer role)
3. Explore requirements through questions
4. Run another session (Manager role) for planning
5. Run third session (Designer role) for UX
6. Generate code with combined insights
7. Review and customize generated code

### Task: Analyze Third-Party Code
1. Import repository from GitHub
2. Review analysis results
3. Create Socratic session (Developer role)
4. Ask about architecture, patterns, best practices
5. Export session for team review

### Task: Understand a Framework
1. Import framework repository
2. Create Socratic session (learner perspective)
3. Ask questions about how framework works
4. Follow up questions on specific components
5. Generate example project using framework

### Task: Create API Documentation
1. Generate code with API Documentation option enabled
2. Review generated OpenAPI/Swagger documentation
3. Customize documentation for your API
4. Export for team distribution

---

## Troubleshooting

**Q: Code generation is taking too long**
- A: Large projects can take 1-2 minutes. Don't refresh the page; the system is working. Check progress bar for updates.

**Q: Repository import failed**
- A: Ensure URL is correct, repository is accessible, and branch exists. Check network connectivity.

**Q: Generated code doesn't compile**
- A: Generated code is a template. Review error messages and install required dependencies first.

**Q: Can't find uploaded document**
- A: Document may still be processing. Wait a moment and refresh the page.

**Q: Session paused unexpectedly**
- A: Session may have timed out for security. You can resume or start a new session.

For more help, see the Troubleshooting Guide: `docs/TROUBLESHOOTING.md`

---

## Next Steps

1. ✅ Read this guide (you are here!)
2. 📖 Learn system architecture: `docs/ARCHITECTURE.md`
3. 🔧 Explore API documentation: `docs/API_DOCUMENTATION.md`
4. 🚀 Check deployment guide: `docs/DEPLOYMENT.md`
5. ❓ See troubleshooting: `docs/TROUBLESHOOTING.md`

## Support

- 📧 Email: support@socratic-rag.com
- 💬 Chat: Available in-app help widget
- 📚 Documentation: See `/docs` directory
- 🐛 Bug Reports: GitHub Issues
- 💡 Feature Requests: Discussions on GitHub
