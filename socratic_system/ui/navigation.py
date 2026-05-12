"""Navigation stack for managing context and state transitions"""

from typing import Any, Dict, List, Optional, Tuple


class NavigationStack:
    """
    Manages navigation history and context preservation.

    Supports /back and /menu commands by maintaining a stack of contexts.
    Each context is a named location (e.g., 'main_menu', 'project_view') with associated state.
    """

    def __init__(self):
        """Initialize navigation stack."""
        self.stack: list[tuple[str, dict[str, Any]]] = []
        self.home = "main_menu"  # Default home context

    def push(self, context_name: str, state: dict[str, Any] | None = None) -> None:
        """
        Push a new context onto the stack.

        Args:
            context_name: Name of the context (e.g., 'project_view', 'note_editor')
            state: Optional state dictionary to preserve context-specific data
        """
        if state is None:
            state = {}

        self.stack.append((context_name, state.copy()))

    def pop(self) -> tuple[str | None, dict[str, Any] | None]:
        """
        Pop the current context from the stack.

        Returns:
            Tuple of (context_name, state) if stack not empty, else (None, None)
        """
        if not self.stack:
            return None, None

        context_name, state = self.stack.pop()
        return context_name, state

    def peek(self) -> tuple[str | None, dict[str, Any] | None]:
        """
        Look at the current context without popping it.

        Returns:
            Tuple of (context_name, state) if stack not empty, else (None, None)
        """
        if not self.stack:
            return None, None

        context_name, state = self.stack[-1]
        return context_name, state.copy()

    def go_back(self) -> tuple[str | None, dict[str, Any] | None]:
        """
        Go back to the previous context (alias for pop).

        Returns:
            Tuple of (context_name, state) if previous context exists, else (None, None)
        """
        return self.pop()

    def go_home(self) -> tuple[str, dict[str, Any]]:
        """
        Clear stack and return to home context.

        Returns:
            Tuple of (home_context, empty_state)
        """
        self.stack.clear()
        return self.home, {}

    def clear(self) -> None:
        """Clear the entire navigation stack."""
        self.stack.clear()

    def depth(self) -> int:
        """
        Get current depth of navigation stack.

        Returns:
            Number of contexts on the stack
        """
        return len(self.stack)

    def get_breadcrumb(self) -> str:
        """
        Get a breadcrumb representation of current navigation path.

        Returns:
            Breadcrumb string like "main_menu > project_view > editor"
        """
        if not self.stack:
            return self.home

        breadcrumb = self.home
        for context_name, _ in self.stack:
            breadcrumb += f" > {context_name}"

        return breadcrumb

    def history(self) -> list[str]:
        """
        Get list of context names in order from bottom to top.

        Returns:
            List of context names
        """
        return [context_name for context_name, _ in self.stack]

    def update_current_state(self, state_updates: dict[str, Any]) -> None:
        """
        Update the state of the current context without popping.

        Args:
            state_updates: Dictionary of state updates to merge into current state
        """
        if not self.stack:
            return

        context_name, current_state = self.stack[-1]
        current_state.update(state_updates)
        self.stack[-1] = (context_name, current_state)

    def get_current_state(self) -> dict[str, Any]:
        """
        Get the state of the current context.

        Returns:
            Copy of current context state, or empty dict if no context
        """
        _, state = self.peek()
        return state if state is not None else {}
