"""
Ollama client for Socrates AI

Provides both synchronous and asynchronous interfaces for calling local Ollama API,
with automatic token tracking and structured error handling.
"""

import asyncio
import base64
import hashlib
import json
import logging
from typing import TYPE_CHECKING, Any, Dict

import requests
from cryptography.fernet import Fernet

from socratic_system.events import EventType
from socratic_system.exceptions import APIError
from socratic_system.models import ConflictInfo, ProjectContext

if TYPE_CHECKING:
    from socratic_system.orchestration.orchestrator import AgentOrchestrator


class OllamaClient:
    """
    Client for interacting with local Ollama API.

    Supports both synchronous and asynchronous operations with automatic
    token usage tracking and event emission. Ollama runs locally and provides
    free access to open-source LLMs like Mistral, Llama, etc.
    """

    def __init__(
        self, api_key: str = None, orchestrator: "AgentOrchestrator" = None, subscription_token: str = None
    ):
        """
        Initialize Ollama client.

        Args:
            api_key: Optional API key for Ollama (if using authenticated Ollama server)
            orchestrator: Reference to AgentOrchestrator for event emission and token tracking
            subscription_token: Optional - subscription token for Ollama server
        """
        self.api_key = api_key
        self.subscription_token = subscription_token
        self.orchestrator = orchestrator
        self.model = orchestrator.config.ollama_model if orchestrator else "mistral"
        self.base_url = orchestrator.config.ollama_url if orchestrator else "http://localhost:11434"
        self.logger = logging.getLogger("socrates.clients.ollama")

        # Client connections
        self.client = None
        self.async_client = None

        # Initialize clients
        try:
            self.client = requests.Session()
            self.async_client = requests.Session()
            self.logger.info("Ollama client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Ollama client: {e}")

        # Cache for insights extraction to avoid redundant Ollama API calls
        # Maps message hash -> extracted insights
        self._insights_cache: Dict[str, Dict[str, Any]] = {}

        # Cache for question generation to avoid redundant Ollama API calls
        # Maps question_cache_key (project_id:phase:question_count) -> generated question
        self._question_cache: Dict[str, str] = {}

    def get_auth_credential(self, user_auth_method: str = "api_key") -> str:
        """
        Get the appropriate credential based on user's preferred auth method.

        Args:
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')

        Returns:
            The appropriate credential (API key or subscription token)

        Raises:
            ValueError: If the requested auth method is not configured
        """
        if user_auth_method == "subscription":
            if not self.subscription_token:
                raise ValueError(
                    "Subscription token not configured. "
                    "Set OLLAMA_SUBSCRIPTION_TOKEN environment variable."
                )
            return self.subscription_token
        elif user_auth_method == "api_key":
            # Ollama typically doesn't require auth for local access
            if self.api_key and not self.api_key.startswith("placeholder"):
                return self.api_key
            return None  # Local access doesn't require key
        else:
            raise ValueError(f"Unknown auth method: {user_auth_method}")

    def _get_user_api_key(self, user_id: str = None) -> tuple:
        """
        Get the API key for a specific user from the database.

        Returns tuple of (api_key, is_user_specific).
        Falls back to environment/default API key if user-specific key not found.

        Args:
            user_id: User ID to fetch API key for

        Returns:
            Tuple of (api_key, is_user_specific) where is_user_specific is True if the key
            came from the database
        """
        if user_id:
            stored_key = self.orchestrator.database.get_api_key(user_id, "ollama")
            if stored_key:
                decrypted_key = self._decrypt_api_key_from_db(stored_key)
                return decrypted_key, True

        env_key = self.api_key
        if env_key and not env_key.startswith("placeholder"):
            return env_key, False

        return None, False

    def _decrypt_api_key_from_db(self, encrypted_key: str) -> str:
        """
        Decrypt API key stored in database.

        Tries three decryption methods in order:
        1. SHA256-Fernet with SOCRATES_ENCRYPTION_KEY environment variable
        2. PBKDF2-based Fernet decryption (for older keys)
        3. Base64 fallback (for keys saved with base64 encoding)

        Args:
            encrypted_key: Encrypted API key from database

        Returns:
            Decrypted API key or None if all methods fail
        """
        import os
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        encryption_key_base = os.getenv("SOCRATES_ENCRYPTION_KEY", "default-socrates-key")

        # Method 1: Try SHA256-based Fernet decryption (primary method)
        try:
            key_hash = hashlib.sha256(encryption_key_base.encode()).digest()
            encryption_key = base64.urlsafe_b64encode(key_hash)
            cipher = Fernet(encryption_key)
            decrypted = cipher.decrypt(encrypted_key.encode())
            self.logger.info("API key decrypted successfully using SHA256-Fernet")
            return decrypted.decode()
        except ImportError:
            self.logger.debug("Fernet not available, skipping SHA256 decryption")
        except Exception as e:
            self.logger.debug(f"SHA256-Fernet decryption failed: {e}")

        # Method 2: Try PBKDF2-based Fernet decryption (for older keys encrypted with PBKDF2)
        try:
            salt = b"socrates-salt"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend(),
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(encryption_key_base.encode()))
            cipher = Fernet(derived_key)
            decrypted = cipher.decrypt(encrypted_key.encode())
            self.logger.info("API key decrypted successfully using PBKDF2-Fernet")
            return decrypted.decode()
        except ImportError:
            self.logger.debug("PBKDF2 not available, skipping PBKDF2 decryption")
        except Exception as e:
            self.logger.debug(f"PBKDF2-Fernet decryption failed: {e}")

        # Method 3: Try base64 fallback (for keys saved with base64 encoding)
        try:
            self.logger.info("Attempting base64 decoding as fallback...")
            decrypted = base64.b64decode(encrypted_key.encode()).decode()
            self.logger.info("API key decoded successfully using base64 fallback")
            return decrypted
        except Exception as e:
            self.logger.debug(f"Base64 decoding failed: {e}")

        # All methods failed
        self.logger.error("All decryption methods failed for API key")
        self.logger.error(
            "If key was encrypted with custom SOCRATES_ENCRYPTION_KEY, ensure it's set."
        )
        return None

    def _get_client(self, user_auth_method: str = "api_key", user_id: str = None):
        """
        Get the appropriate sync client session.

        For Ollama, this is typically just a requests.Session with the base URL configured.

        Args:
            user_auth_method: User's preferred auth method (not typically used for local Ollama)
            user_id: Optional user ID to fetch user-specific API key

        Returns:
            Requests Session instance configured for Ollama

        Raises:
            APIError: If Ollama server is not accessible
        """
        try:
            # Verify Ollama is running
            response = self.client.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise APIError(
                    f"Ollama server returned status {response.status_code}. "
                    f"Ensure Ollama is running at {self.base_url}",
                    error_type="CONNECTION_ERROR",
                )
            self.logger.debug("Ollama server connection verified")
            return self.client
        except requests.exceptions.ConnectionError as e:
            raise APIError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Ensure Ollama is running locally with: ollama serve",
                error_type="CONNECTION_ERROR",
            ) from e
        except Exception as e:
            raise APIError(
                f"Error connecting to Ollama: {e}",
                error_type="CONNECTION_ERROR",
            ) from e

    def _get_async_client(self, user_auth_method: str = "api_key", user_id: str = None):
        """
        Get the appropriate async client session.

        For Ollama, this is typically just a requests.Session with the base URL configured.
        (Ollama doesn't have native async support, so we use thread pooling)

        Args:
            user_auth_method: User's preferred auth method (not typically used for local Ollama)
            user_id: Optional user ID to fetch user-specific API key

        Returns:
            Requests Session instance configured for Ollama

        Raises:
            APIError: If Ollama server is not accessible
        """
        try:
            # Verify Ollama is running
            response = self.async_client.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise APIError(
                    f"Ollama server returned status {response.status_code}. "
                    f"Ensure Ollama is running at {self.base_url}",
                    error_type="CONNECTION_ERROR",
                )
            self.logger.debug("Ollama server connection verified")
            return self.async_client
        except requests.exceptions.ConnectionError as e:
            raise APIError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Ensure Ollama is running locally with: ollama serve",
                error_type="CONNECTION_ERROR",
            ) from e
        except Exception as e:
            raise APIError(
                f"Error connecting to Ollama: {e}",
                error_type="CONNECTION_ERROR",
            ) from e

    def extract_insights(
        self,
        user_response: str,
        project: ProjectContext,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> Dict:
        """
        Extract insights from user response using Ollama (synchronous) with caching.

        Args:
            user_response: The user's response text
            project: The project context
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Dictionary of extracted insights
        """
        # Handle empty or non-informative responses
        if not user_response or len(user_response.strip()) < 3:
            return {}

        # Handle common non-informative responses
        non_informative = ["i don't know", "idk", "not sure", "no idea", "dunno", "unsure"]
        if user_response.lower().strip() in non_informative:
            return {"note": "User expressed uncertainty - may need more guidance"}

        # Check cache first to avoid redundant Ollama API calls
        cache_key = self._get_cache_key(user_response)
        if cache_key in self._insights_cache:
            self.logger.debug("Cache hit for insights extraction")
            return self._insights_cache[cache_key]

        # Build prompt
        prompt = f"""
        Analyze this user response in the context of their project and extract structured insights:

        Project Context:
        - Goals: {project.goals or 'Not specified'}
        - Phase: {project.phase}
        - Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}

        User Response: "{user_response}"

        Please extract and return any mentions of:
        1. Goals or objectives
        2. Technical requirements
        3. Technology preferences
        4. Constraints or limitations
        5. Team structure preferences

        IMPORTANT: Return ONLY valid JSON. Each field should be a string or array of strings.
        Example format:
        {{
            "goals": "string describing the goal",
            "requirements": ["requirement 1", "requirement 2"],
            "tech_stack": ["technology 1", "technology 2"],
            "constraints": ["constraint 1", "constraint 2"],
            "team_structure": "description of team structure"
        }}

        If no insights found, return: {{}}
        """

        try:
            # Get the appropriate client
            client = self._get_client(user_auth_method, user_id)

            # Call Ollama API
            response = client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=300,
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "")

            # Track token usage
            self._track_token_usage_ollama(len(prompt), len(response_text), "extract_insights")

            # Try to parse JSON response
            insights = self._parse_json_response(response_text.strip())

            # Cache the result for future identical messages
            self._insights_cache[cache_key] = insights

            return insights

        except Exception as e:
            self.logger.error(f"Error extracting insights: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to extract insights: {e}"}
            )
            return {}

    async def extract_insights_async(
        self, user_response: str, project: ProjectContext, user_auth_method: str = "api_key"
    ) -> Dict:
        """
        Extract insights from user response asynchronously with caching.

        Args:
            user_response: The user's response text
            project: The project context
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')

        Returns:
            Dictionary of extracted insights
        """
        # Handle empty or non-informative responses
        if not user_response or len(user_response.strip()) < 3:
            return {}

        if user_response.lower().strip() in [
            "i don't know",
            "idk",
            "not sure",
            "no idea",
            "dunno",
            "unsure",
        ]:
            return {"note": "User expressed uncertainty - may need more guidance"}

        # Check cache first to avoid redundant Ollama API calls
        cache_key = self._get_cache_key(user_response)
        if cache_key in self._insights_cache:
            self.logger.debug("Cache hit for insights extraction")
            return self._insights_cache[cache_key]

        prompt = f"""
        Analyze this user response in the context of their project and extract structured insights:

        Project Context:
        - Goals: {project.goals or 'Not specified'}
        - Phase: {project.phase}
        - Tech Stack: {', '.join(project.tech_stack) if project.tech_stack else 'Not specified'}

        User Response: "{user_response}"

        Please extract and return any mentions of:
        1. Goals or objectives
        2. Technical requirements
        3. Technology preferences
        4. Constraints or limitations
        5. Team structure preferences

        IMPORTANT: Return ONLY valid JSON.
        """

        try:
            # Get the appropriate async client
            async_client = self._get_async_client(user_auth_method, user_id=None)
            # Use thread pool for async-like behavior
            response_text = await asyncio.to_thread(
                self._sync_generate,
                async_client,
                prompt
            )

            # Track token usage asynchronously
            await self._track_token_usage_async(len(prompt), len(response_text), "extract_insights_async")

            insights = self._parse_json_response(response_text.strip())

            # Cache the result for future identical messages
            self._insights_cache[cache_key] = insights

            return insights

        except Exception as e:
            self.logger.error(f"Error extracting insights (async): {e}")
            return {}

    def generate_code(
        self, context: str, user_auth_method: str = "api_key", user_id: str = None
    ) -> str:
        """Generate code based on project context"""
        prompt = f"""
You are a software architect generating code for a specific project phase.

PROJECT CONTEXT:
{context}

CODE GENERATION GUIDELINES:

1. UNDERSTAND THE PROJECT:
   - Identify the core problem to solve in this phase
   - Determine if this integrates with existing systems
   - Check for architectural constraints and dependencies

2. ARCHITECTURE & INTEGRATION:
   - If this is part of a larger system, design it as a MODULE/COMPONENT, not standalone
   - Follow the project's established patterns and conventions
   - Design REST/gRPC endpoints where appropriate

3. IMPLEMENTATION REQUIREMENTS:
   - Include DETAILED docstrings explaining module purpose and usage
   - Implement proper error handling and logging
   - Add type hints for all function parameters and returns

4. CODE STRUCTURE:
   - Organize into logical modules/classes
   - Keep functions/methods focused and single-purpose
   - Use appropriate design patterns for the problem domain

5. DOCUMENTATION:
   - Add module-level docstring with purpose
   - Document key classes and functions with examples

OUTPUT FORMAT - CRITICAL:
- Return ONLY raw, executable Python code
- Do NOT include markdown formatting
- Do NOT include code fences (```python ```)
- Do NOT include explanatory text outside of docstrings
        """

        try:
            client = self._get_client(user_auth_method, user_id)

            response = client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=300,
            )
            response.raise_for_status()

            result = response.json()
            code = result.get("response", "")

            # Track token usage
            self.orchestrator.system_monitor.process(
                {
                    "action": "track_tokens",
                    "input_tokens": len(prompt),
                    "output_tokens": len(code),
                    "total_tokens": len(prompt) + len(code),
                    "cost_estimate": 0.0,  # Ollama is free (local)
                }
            )

            return code

        except Exception as e:
            return f"Error generating code: {e}"

    def generate_socratic_question(
        self,
        prompt: str,
        cache_key: str = None,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
        """
        Generate a Socratic question using Ollama with optional caching.

        Args:
            prompt: The prompt for question generation
            cache_key: Optional cache key (not used, for backward compatibility)
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Generated Socratic question

        Raises:
            APIError: If API call fails
        """
        try:
            # Get the appropriate client
            client = self._get_client(user_auth_method, user_id)

            response = client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=300,
            )
            response.raise_for_status()

            result = response.json()
            question = result.get("response", "").strip()

            # Track token usage
            self._track_token_usage_ollama(len(prompt), len(question), "generate_socratic_question")

            return question

        except Exception as e:
            self.logger.error(f"Error generating Socratic question: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to generate Socratic question: {e}"}
            )
            raise APIError(
                f"Error generating Socratic question: {e}", error_type="GENERATION_ERROR"
            ) from e

    async def generate_socratic_question_async(
        self,
        prompt: str,
        cache_key: str = None,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
        """
        Generate socratic question asynchronously (high-frequency operation).

        Args:
            prompt: The prompt for question generation
            cache_key: Optional cache key (not used, for backward compatibility)
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Generated Socratic question
        """
        try:
            # Get the appropriate async client
            async_client = self._get_async_client(user_auth_method, user_id)
            question = await asyncio.to_thread(
                self._sync_generate,
                async_client,
                prompt
            )

            await self._track_token_usage_async(len(prompt), len(question), "generate_socratic_question_async")
            return question.strip()

        except Exception as e:
            self.logger.error(f"Error generating socratic question (async): {e}")
            return "I'd like to understand your thinking better. Can you elaborate?"

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
        """
        Generate a general response from Ollama for any prompt.

        Args:
            prompt: The prompt to send to Ollama
            max_tokens: Maximum tokens in response (default: 2000)
            temperature: Temperature for response generation (default: 0.7)
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Ollama's response as a string

        Raises:
            APIError: If API call fails
        """
        try:
            # Get the appropriate client
            client = self._get_client(user_auth_method, user_id)

            response = client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
                timeout=300,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_ERROR, {"message": f"Failed to generate response: {e}"}
            )
            raise APIError(f"Error generating response: {e}", error_type="GENERATION_ERROR") from e

    async def generate_response_async(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        user_auth_method: str = "api_key",
        user_id: str = None,
    ) -> str:
        """
        Generate a general response from Ollama asynchronously.

        Args:
            prompt: The prompt to send to Ollama
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            user_auth_method: User's preferred auth method ('api_key' or 'subscription')
            user_id: Optional user ID for fetching user-specific API key

        Returns:
            Ollama's response as a string

        Raises:
            APIError: If API call fails
        """
        try:
            # Get the appropriate async client
            async_client = self._get_async_client(user_auth_method, user_id)

            response_text = await asyncio.to_thread(
                lambda: async_client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                    timeout=300,
                )
            )

            response_text.raise_for_status()
            result = response_text.json()
            return result.get("response", "").strip()

        except Exception as e:
            self.logger.error(f"Error generating response (async): {e}")
            raise APIError(f"Error generating response: {e}", error_type="GENERATION_ERROR") from e

    def test_connection(self, user_auth_method: str = "api_key") -> bool:
        """Test connection to Ollama API"""
        try:
            client = self._get_client(user_auth_method)
            response = client.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            self.logger.info("Ollama API connection test successful")
            return True
        except APIError:
            self.logger.warning("Ollama connection test failed - Ollama server not accessible")
            return False
        except Exception as e:
            self.logger.error(f"Ollama API connection test failed: {e}")
            raise APIError(
                f"Failed to connect to Ollama API at {self.base_url}: {e}", error_type="CONNECTION_ERROR"
            ) from e

    # Helper Methods

    def _sync_generate(self, client, prompt: str) -> str:
        """Synchronous generate for use in async context via thread pool"""
        response = client.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=300,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")

    def _get_cache_key(self, message: str) -> str:
        """Generate cache key for a message using SHA256 hash"""
        return hashlib.sha256(message.encode()).hexdigest()

    def _track_token_usage_ollama(self, input_len: int, output_len: int, operation: str) -> None:
        """Track token usage and emit event (Ollama doesn't provide token counts, use text length)"""
        # Rough estimate: 4 chars ≈ 1 token
        input_tokens = max(1, input_len // 4)
        output_tokens = max(1, output_len // 4)
        total_tokens = input_tokens + output_tokens

        self.orchestrator.system_monitor.process(
            {
                "action": "track_tokens",
                "operation": operation,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_estimate": 0.0,  # Ollama is free (local)
            }
        )

        self.orchestrator.event_emitter.emit(
            EventType.TOKEN_USAGE,
            {
                "operation": operation,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_estimate": 0.0,
            },
        )

    async def _track_token_usage_async(self, input_len: int, output_len: int, operation: str) -> None:
        """Track token usage asynchronously"""
        await asyncio.to_thread(self._track_token_usage_ollama, input_len, output_len, operation)

    def _parse_json_response(self, response_text: str) -> any:
        """Parse JSON from Ollama response with error handling. Returns dict or list."""
        try:
            # Clean up markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            # Try to find JSON array first [...]
            start_array = response_text.find("[")
            end_array = response_text.rfind("]") + 1

            # Then try to find JSON object {...}
            start_obj = response_text.find("{")
            end_obj = response_text.rfind("}") + 1

            # Prefer whichever starts first (appears earlier in the response)
            json_text = None
            if start_array >= 0 and end_array > start_array:
                if start_obj >= 0 and start_obj < start_array:
                    # Object starts before array
                    if 0 <= start_obj < end_obj:
                        json_text = response_text[start_obj:end_obj]
                else:
                    # Array starts first or no object
                    json_text = response_text[start_array:end_array]
            elif 0 <= start_obj < end_obj:
                # Only object found
                json_text = response_text[start_obj:end_obj]

            if json_text:
                parsed_data = json.loads(json_text)
                # Return the parsed data as-is (could be dict or list)
                return parsed_data
            else:
                self.logger.warning("No JSON object or array found in response")
                return {}

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            self.orchestrator.event_emitter.emit(
                EventType.LOG_WARNING, {"message": f"Could not parse JSON response: {e}"}
            )
            return {}
