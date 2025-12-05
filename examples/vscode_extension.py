"""
VS Code Extension Integration Example for Socrates AI

This example demonstrates how to integrate the Socrates AI library with VS Code
using a JSON-RPC server that the extension communicates with via stdio.

The extension provides:
- Command palette commands for Socratic learning
- Code lens for inline questions
- Terminal for interactive sessions
- Sidebar panel for project management

Installation:
1. Create VS Code extension in TypeScript/JavaScript
2. Run this server as subprocess: code-extension-server
3. Extension communicates via JSON-RPC protocol
4. Server uses socrates-ai library for AI operations

VS Code Extension side (TypeScript):
```typescript
import * as cp from 'child_process';
import * as rpc from 'jsonrpc2';

const server = cp.spawn('python', ['-m', 'socrates_vscode_server']);
const connection = rpc.createMessageConnection(
    new rpc.StreamMessageReader(server.stdout),
    new rpc.StreamMessageWriter(server.stdin)
);
```

Server side (this file):
Implements JSON-RPC methods that VS Code extension calls.
"""

import json
import logging
import sys
from typing import Any, Dict, Optional

try:
    import socrates
except ImportError:
    print("Install socrates-ai: pip install socrates-ai")
    raise


class SocratesRPCServer:
    """
    JSON-RPC Server for VS Code Extension integration

    Implements the following methods:
    - initialize(api_key: str, workspace_dir: str) -> SystemInfo
    - createProject(name: str, owner: str, description: str) -> Project
    - listProjects(owner: str) -> List[Project]
    - askQuestion(project_id: str, topic: str) -> Question
    - evaluateResponse(project_id: str, question_id: str, response: str) -> Feedback
    - generateCode(project_id: str, specification: str, language: str) -> Code
    """

    def __init__(self):
        """Initialize RPC server"""
        self.logger = logging.getLogger("socrates.vscode.server")
        self.orchestrator: Optional[socrates.AgentOrchestrator] = None
        self.initialized = False

        # Setup logging to file (stderr is reserved for RPC protocol)
        fh = logging.FileHandler("/tmp/socrates_vscode.log")
        fh.setLevel(logging.INFO)
        self.logger.addHandler(fh)

    def initialize(self, api_key: str, workspace_dir: Optional[str] = None) -> Dict[str, Any]:
        """Initialize Socrates library connection"""
        try:
            from pathlib import Path

            config_builder = socrates.ConfigBuilder(api_key)
            if workspace_dir:
                data_dir = Path(workspace_dir) / ".socrates"
                config_builder = config_builder.with_data_dir(data_dir)

            config = config_builder.build()
            self.orchestrator = socrates.create_orchestrator(config)

            # Test connection
            self.orchestrator.claude_client.test_connection()

            self.initialized = True
            self.logger.info("Socrates initialized successfully")

            return {
                "status": "success",
                "version": socrates.__version__,
                "model": config.claude_model,
                "data_dir": str(config.data_dir),
            }
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return {"status": "error", "message": str(e)}

    def _check_initialized(self) -> bool:
        """Check if server is initialized"""
        if not self.initialized or not self.orchestrator:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return True

    def createProject(self, name: str, owner: str, description: str = "") -> Dict[str, Any]:
        """Create a new project"""
        self._check_initialized()

        result = self.orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": name,
                "owner": owner,
                "description": description,
            },
        )

        if result.get("status") == "success":
            project = result.get("project")
            return {
                "status": "success",
                "project": {
                    "project_id": project.project_id,
                    "name": project.name,
                    "owner": project.owner,
                    "description": project.description,
                    "phase": project.phase,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                },
            }
        return {"status": "error", "message": result.get("message", "Failed to create project")}

    def listProjects(self, owner: Optional[str] = None) -> Dict[str, Any]:
        """List projects"""
        self._check_initialized()

        result = self.orchestrator.process_request(
            "project_manager", {"action": "list_projects", "owner": owner}
        )

        projects = []
        for p in result.get("projects", []):
            projects.append(
                {
                    "project_id": p["project_id"],
                    "name": p["name"],
                    "owner": p["owner"],
                    "phase": p["phase"],
                    "updated_at": (
                        p.get("updated_at", "").isoformat()
                        if hasattr(p.get("updated_at"), "isoformat")
                        else str(p.get("updated_at", ""))
                    ),
                }
            )

        return {"status": "success", "projects": projects, "total": len(projects)}

    def askQuestion(
        self, project_id: str, topic: Optional[str] = None, difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """Ask a Socratic question"""
        self._check_initialized()

        result = self.orchestrator.process_request(
            "question_generator",
            {
                "action": "generate_question",
                "project_id": project_id,
                "topic": topic,
                "difficulty_level": difficulty,
            },
        )

        if result.get("status") == "success":
            return {
                "status": "success",
                "question_id": result.get("question_id"),
                "question": result.get("question"),
                "context": result.get("context"),
                "hints": result.get("hints", []),
            }
        return {"status": "error", "message": result.get("message", "Failed to generate question")}

    def evaluateResponse(self, project_id: str, question_id: str, response: str) -> Dict[str, Any]:
        """Evaluate user response"""
        self._check_initialized()

        result = self.orchestrator.process_request(
            "response_evaluator",
            {
                "action": "evaluate_response",
                "project_id": project_id,
                "question_id": question_id,
                "user_response": response,
            },
        )

        if result.get("status") == "success":
            return {
                "status": "success",
                "feedback": result.get("feedback"),
                "is_correct": result.get("is_correct", False),
                "insights": result.get("insights", []),
                "next_topic": result.get("next_topic"),
            }
        return {"status": "error", "message": result.get("message", "Failed to evaluate response")}

    def generateCode(
        self, project_id: str, specification: str = "", language: str = "python"
    ) -> Dict[str, Any]:
        """Generate code"""
        self._check_initialized()

        # Load project first
        project_result = self.orchestrator.process_request(
            "project_manager", {"action": "load_project", "project_id": project_id}
        )

        if project_result.get("status") != "success":
            return {"status": "error", "message": f"Project {project_id} not found"}

        project = project_result["project"]

        # Generate code
        result = self.orchestrator.process_request(
            "code_generator",
            {
                "action": "generate_code",
                "project": project,
                "specification": specification,
                "language": language,
            },
        )

        if result.get("status") == "success":
            return {
                "status": "success",
                "code": result.get("script", ""),
                "explanation": result.get("explanation"),
                "language": language,
                "token_usage": result.get("token_usage"),
            }
        return {"status": "error", "message": result.get("message", "Failed to generate code")}

    def getInfo(self) -> Dict[str, Any]:
        """Get server info"""
        if self.orchestrator:
            return {
                "status": "success",
                "initialized": True,
                "version": socrates.__version__,
                "model": self.orchestrator.config.claude_model,
            }
        return {"status": "success", "initialized": False, "version": socrates.__version__}


class JSONRPCHandler:
    """Handles JSON-RPC protocol communication"""

    def __init__(self, server: SocratesRPCServer):
        self.server = server
        self.message_id = 0

    def handle_message(self, message: str) -> str:
        """Handle incoming JSON-RPC message"""
        try:
            request = json.loads(message)
            method = request.get("method")
            params = request.get("params", {})
            msg_id = request.get("id")

            # Call method on server
            if hasattr(self.server, method):
                fn = getattr(self.server, method)
                result = fn(**params) if isinstance(params, dict) else fn(*params)
                response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            return json.dumps(response)
        except Exception as e:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if "request" in locals() else None,
                    "error": {"code": -32603, "message": str(e)},
                }
            )

    def run(self):
        """Run the JSON-RPC server reading from stdin"""
        handler = JSONRPCHandler(self.server)

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                response = handler.handle_message(line.strip())
                print(response)
                sys.stdout.flush()
            except Exception as e:
                print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}))
                sys.stdout.flush()


# VS Code Extension TypeScript Example
VSCODE_EXTENSION_EXAMPLE = """
// extension.ts - VS Code Extension example

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as rpc from 'vscode-jsonrpc/node';

let connection: rpc.MessageConnection;

export function activate(context: vscode.ExtensionContext) {
    // Start the Python RPC server
    const server = cp.spawn('python', ['-m', 'socrates_vscode_server']);

    connection = rpc.createMessageConnection(
        new rpc.StreamMessageReader(server.stdout),
        new rpc.StreamMessageWriter(server.stdin)
    );
    connection.listen();

    // Register commands
    let initCmd = vscode.commands.registerCommand('socrates.initialize', () => {
        const apiKey = vscode.workspace.getConfiguration('socrates').get('apiKey');
        const workspaceDir = vscode.workspace.workspaceFolders?.[0].uri.fsPath;

        connection.sendRequest('initialize', { api_key: apiKey, workspace_dir: workspaceDir })
            .then(result => {
                vscode.window.showInformationMessage('Socrates initialized!');
            });
    });

    let askQuestionCmd = vscode.commands.registerCommand('socrates.askQuestion', () => {
        const projectId = 'proj_abc123'; // Would get from context

        connection.sendRequest('askQuestion', {
            project_id: projectId,
            topic: 'API design',
            difficulty: 'intermediate'
        }).then(result => {
            if (result.status === 'success') {
                vscode.window.showInformationMessage(result.question);
            }
        });
    });

    let generateCodeCmd = vscode.commands.registerCommand('socrates.generateCode', () => {
        const projectId = 'proj_abc123';

        connection.sendRequest('generateCode', {
            project_id: projectId,
            specification: 'Create authentication middleware',
            language: 'python'
        }).then(result => {
            if (result.status === 'success') {
                const editor = vscode.window.activeTextEditor;
                if (editor) {
                    editor.insertSnippet(new vscode.SnippetString(result.code));
                }
            }
        });
    });

    context.subscriptions.push(initCmd, askQuestionCmd, generateCodeCmd);
}

export function deactivate() {
    connection.dispose();
}
"""


def main():
    """Main entry point for the RPC server"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    server = SocratesRPCServer()
    handler = JSONRPCHandler(server)
    handler.run()


if __name__ == "__main__":
    # Print example instead of running
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        print("VS Code Extension Integration Example")
        print("-" * 50)
        print()
        print("Extension TypeScript code:")
        print(VSCODE_EXTENSION_EXAMPLE)
    else:
        main()
