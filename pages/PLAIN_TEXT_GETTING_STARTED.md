GETTING STARTED - Socrates AI

Create Your First Project in 30 Minutes

Follow this step-by-step guide to go from zero to production-ready code.

STEP 1: INSTALLATION (5 minutes)

Choose your platform and install Socrates:

Windows Users:
1. Download from https://github.com/Nireus79/Socrates/releases/latest
2. Double-click socrates.exe
3. Follow the installer
4. Done!

See full installation guide at hermessoft.wordpress.com/socrates-ai/installation

macOS Users:
brew install socrates

Linux Users:
sudo apt install socrates

Docker Users:
docker run -it ghcr.io/nireus79/socrates:latest

STEP 2: SET YOUR API KEY (2 minutes)

Get your Claude API key:
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Click "API Keys"
4. Click "Create new secret key"
5. Copy the key

Set it in Socrates:
1. Open Socrates (browser opens automatically at http://localhost:8000)
2. Click Settings
3. Paste your API key
4. Click Save

STEP 3: CREATE YOUR FIRST PROJECT (23 minutes)

Let's build a simple Task Manager app as an example.

1. Click "Create New Project"
2. Name it: "Task Manager App"
3. Click "Begin Dialogue"

Now you'll go through 4 phases:

PHASE 1: DISCOVERY (5-10 questions)

Socrates asks about your project. Answer honestly:

"What problem are you solving?"
Answer: A simple app to help users manage their daily tasks

"Who are your users?"
Answer: Individual users managing personal tasks

"What's your main goal?"
Answer: Let users create, view, and mark tasks complete

"What's your timeline?"
Answer: Want it done this weekend

"Any budget constraints?"
Answer: Using free tier, no paid services

Result: Phase 1 Complete - Your project goal is documented

PHASE 2: ANALYSIS (8-12 questions)

Go deeper into requirements:

"What are specific requirements?"
Answer: Users can add tasks, mark complete, see all tasks, delete tasks

"What tech do you prefer?"
Answer: Python backend, React frontend, SQLite database

"What's the main workflow?"
Answer: User logs in, sees task list, adds tasks, clicks to mark complete

"Any external services needed?"
Answer: No, just local app

Result: Phase 2 Complete - Clear specification documented

PHASE 3: DESIGN (5-10 questions)

Architecture and technical design:

"How should the database be structured?"
Answer: Tasks table with id, title, description, completed flag, created_date

"How will authentication work?"
Answer: Simple local user auth, no complex security needed for personal app

"What API endpoints do you need?"
Answer: GET /tasks, POST /task, PUT /task/:id, DELETE /task/:id

"Any error handling special needs?"
Answer: Show friendly messages for validation errors

Result: Phase 3 Complete - Architecture is defined

PHASE 4: IMPLEMENTATION (Instant)

Ready for code generation:

1. Review your specification (shows all your answers organized)
2. Select programming language: Python
3. Click "Generate Code"
4. Wait 10-30 seconds
5. Your code appears ready to download

WHAT YOU GET

Your generated code includes:

Backend:
- Flask API with all endpoints
- SQLite database schema
- Authentication middleware
- Error handling and validation
- Proper project structure
- Configuration files
- Requirements.txt

Frontend:
- React components
- UI layout and styling
- API integration code
- User authentication
- Error messages
- Ready to run

Documentation:
- README with setup instructions
- API documentation
- Code comments
- Database schema diagram

Tests:
- Test structure setup
- Example tests
- Ready to extend

STEP 4: RUN YOUR CODE (5 minutes)

1. Download the generated code
2. Extract the folder
3. Follow the README instructions:

For Python/Flask backend:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

Backend runs at http://localhost:5000

For React frontend:
cd frontend
npm install
npm start

Frontend runs at http://localhost:3000

You now have a working Task Manager app!

NEXT STEPS

Customize Your Code:
1. The generated code is a starting point
2. You can edit and customize as needed
3. Add business logic specific to your needs
4. Extend with additional features

Deploy Your App:
1. Push to GitHub at https://github.com/Nireus79/Socrates
2. Deploy backend to Heroku or similar
3. Deploy frontend to Vercel or GitHub Pages
4. Set up CI/CD pipeline

Share with Your Team:
1. Pro tier lets you invite team members
2. Others can review your specification
3. Collaborate on future updates
4. Everyone stays aligned

THE 4 PHASES EXPLAINED

Phase 1: Discovery
Clarify the big picture. What problem does this solve? Who uses it? What's the success metric? Takes 5-10 minutes.

Phase 2: Analysis
Get into requirements. What features specifically? What constraints? What about integrations? Takes 10-15 minutes.

Phase 3: Design
Architecture and technical decisions. Database structure? API design? Error handling? Takes 10-15 minutes.

Phase 4: Implementation
Generate production-ready code from your specification. Select language. Generate. Takes 1-2 minutes.

Total Dialogue Time: 30 minutes to 2 hours depending on project complexity

Code Generation Time: 10-30 seconds regardless of project size

COMMON FIRST QUESTIONS

"Is the generated code production-ready?"

Nearly! The code is high quality, well-structured, and includes best practices. Before deploying:
- Review the code
- Add your specific business logic
- Test with real data
- Add your own error handling as needed
- Deploy to staging first

"Can I modify the generated code?"

Absolutely! The generated code is just a starting point. You can:
- Edit any file
- Add more features
- Change the structure
- Integrate with other services
- Use as reference only if you prefer

"What languages can I generate?"

Supported languages:
- Python (Django, Flask, FastAPI)
- JavaScript/TypeScript (Node, Express, Next.js)
- Go (Gin, Echo)
- Rust (Actix, Axum)
- Java (Spring)
- C# (.NET)
- Ruby (Rails)
- PHP (Laravel)

"Can I regenerate code?"

Yes! Anytime you want:
1. Modify your specification answers
2. Click "Regenerate Code"
3. New code appears with your changes

"What if I'm not happy with the code?"

Common reasons and solutions:
- Code doesn't match requirements: Review spec, update if needed, regenerate
- Want different tech stack: Go back to Phase 3, change tech choice, regenerate
- Need more features: Add questions, regenerate
- Code structure is different than expected: Still valid, adapt your workflow

Contact support@socrates-ai.com if you need help.

"How do I collaborate with my team?"

Free tier: 1 user only

Basic tier: Still 1 user, but can export and share specifications

Pro tier: Invite up to 5 team members
1. Go to Settings → Team
2. Click "Invite Members"
3. Enter their email addresses
4. They can see and edit your projects together
5. Real-time updates when others answer questions

"Can I save and share my specification?"

Yes! Your specification is always saved. You can:
- Export as JSON
- Export as Markdown (for docs)
- Export as PDF (for sharing)
- Share link with read-only access
- Share link with edit access (Pro tier)

"What about security?"

Your data is encrypted:
- AES-256 at rest
- TLS 1.3 in transit
- GDPR compliant
- We never train on your code
- Full data export anytime

"How much does it cost?"

Free tier: $0 + API costs (~$1-5 per project)
Pro tier with team: $15/month + API costs

See full pricing at hermessoft.wordpress.com/socrates-ai/pricing

KEYBOARD SHORTCUTS

Speed up your workflow:

Navigation:
Ctrl+N: New project
Ctrl+S: Save
Ctrl+E: Export specification

Dialogue:
Ctrl+Enter: Submit answer
Ctrl+Left: Previous question
Ctrl+Right: Next question
Ctrl+H: Show hint

TROUBLESHOOTING YOUR FIRST PROJECT

"I can't see the first question"

Check:
- Browser opened at http://localhost:8000
- Socrates is running (not closed)
- API key is set and valid
- Port 8000 is available

Solution:
1. Close browser tab
2. Stop Socrates
3. Verify API key at https://console.anthropic.com/
4. Restart Socrates
5. Try again

"API key error"

Check:
- Key starts with sk-ant-
- No spaces before or after
- Key is from https://console.anthropic.com/
- Key is not expired

Solution:
1. Generate new key at https://console.anthropic.com/
2. Paste new key in Settings
3. Save
4. Try again

"Code generation is slow"

Normal timing:
- Dialogue questions: 2-5 seconds each
- Code generation: 10-30 seconds
- Slow internet may add time

Check:
- Internet connection is stable
- Not too many background processes
- No VPN interference

"Generated code won't run"

Check:
- Followed the README exactly
- Installed all dependencies
- Set environment variables correctly
- Used correct Python/Node version

Solution:
1. Read the generated README carefully
2. Install dependencies as shown
3. Check error messages
4. Contact support@socrates-ai.com if stuck

LEARNING RESOURCES

Getting Help:

Documentation: https://github.com/Nireus79/Socrates/blob/master/docs/
Video Tutorials: https://youtube.com/@socrates-ai (coming soon)
Examples: https://github.com/Nireus79/Socrates/tree/master/examples
FAQ: hermessoft.wordpress.com/socrates-ai/faq
Community: https://discord.gg/socrates

Support:
Email: support@socrates-ai.com
Issues: https://github.com/Nireus79/Socrates/issues
Discussions: https://github.com/Nireus79/Socrates/discussions

WHAT TO LEARN NEXT

After your first project:

1. Advanced Features
- Document import for your own docs
- API integration for automation
- Team collaboration for multiple people
- Webhooks for CI/CD integration

2. Different Project Types
- Try a different tech stack
- Build an API project
- Build a full-stack application
- Build a microservice

3. Team Features (Pro tier)
- Invite team members
- Collaborate on specifications
- Real-time updates

4. Integrations (Pro tier)
- GitHub integration (v1.4)
- Slack notifications
- Jira ticket creation
- CI/CD pipeline integration

READY FOR YOUR NEXT PROJECT?

You now understand how Socrates works. Ready to build something real?

Start Your Next Project:

1. Click "Create New Project"
2. Go through 4 phases (now you know the process)
3. Generate code
4. Deploy and share

Questions?

FAQ: hermessoft.wordpress.com/socrates-ai/faq
Discord: https://discord.gg/socrates
Email: support@socrates-ai.com

Last Updated: January 2026
Version: 1.3.0

Happy building!
