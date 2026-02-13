"""
Ollama Client Module
Handles all interactions with Ollama API
"""

import json
import time
from typing import Optional, Dict, Any, List
import requests
from loguru import logger


class OllamaClient:
    """Client for interacting with Ollama API"""

    def __init__(
        self,
        host: str = "http://localhost",
        port: int = 11434,
        model: str = "gpt-oss:20b",
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        """
        Initialize Ollama client

        Args:
            host: Ollama server host
            port: Ollama server port
            model: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
        """
        self.base_url = f"{host}:{port}"
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        logger.info(f"Initialized OllamaClient: {self.base_url}, model: {self.model}")

    def check_server(self) -> bool:
        """
        Check if Ollama server is running

        Returns:
            True if server is accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama server is running")
                return True
            logger.warning(f"Ollama server returned status {response.status_code}")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama server")
            return False
        except Exception as e:
            logger.error(f"Error checking Ollama server: {e}")
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models

        Returns:
            List of model information dictionaries
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            logger.info(f"Found {len(models)} models")
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def check_model_available(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a specific model is available

        Args:
            model_name: Model name to check (uses self.model if None)

        Returns:
            True if model is available, False otherwise
        """
        if model_name is None:
            model_name = self.model

        models = self.list_models()
        model_names = [m.get("name", "") for m in models]

        if model_name in model_names:
            logger.info(f"Model {model_name} is available")
            return True

        logger.warning(f"Model {model_name} is not available")
        return False

    def pull_model(self, model_name: Optional[str] = None) -> bool:
        """
        Pull (download) a model from Ollama registry

        Args:
            model_name: Model name to pull (uses self.model if None)

        Returns:
            True if successful, False otherwise
        """
        if model_name is None:
            model_name = self.model

        logger.info(f"Pulling model: {model_name}")

        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Stream progress updates
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    if status:
                        logger.info(f"Pull status: {status}")

            logger.info(f"Model {model_name} pulled successfully")
            return True

        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False

    def ensure_model_ready(self) -> bool:
        """
        Ensure the configured model is ready to use
        Downloads it if not available

        Returns:
            True if model is ready, False otherwise
        """
        if self.check_model_available():
            return True

        logger.info(f"Model {self.model} not found, attempting to pull...")
        return self.pull_model()

    def generate(
        self,
        prompt: str,
        format: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Generate text using Ollama API

        Args:
            prompt: Input prompt
            format: Output format ("json" or "" for free text)
            temperature: Generation temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional options to pass to Ollama

        Returns:
            Generated text, or None on failure
        """
        # Combine system prompt with user prompt if provided
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs,
            },
        }

        # Add format if specified
        if format:
            payload["format"] = format

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Generating (attempt {attempt + 1}/{self.max_retries})")

                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()
                generated_text = data.get("response", "")

                if generated_text:
                    logger.debug(f"Generated {len(generated_text)} characters")
                    return generated_text

                logger.warning("Empty response from Ollama")

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

            # Wait before retry
            if attempt < self.max_retries - 1:
                logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

        logger.error("All retry attempts failed")
        return None

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        validate: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate JSON output

        Args:
            prompt: Input prompt
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            validate: Whether to validate JSON output

        Returns:
            Parsed JSON dictionary, or None on failure
        """
        # Ensure prompt explicitly requests JSON
        if "JSON" not in prompt and "json" not in prompt:
            prompt = f"{prompt}\n\n重要: 必ず有効なJSON形式で出力してください。"

        response = self.generate(
            prompt=prompt,
            format="json",
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        if response is None:
            return None

        # Try to parse JSON
        for attempt in range(3 if validate else 1):
            try:
                data = json.loads(response)
                logger.debug("Successfully parsed JSON")
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")

                if validate and attempt < 2:
                    # Try to fix common JSON issues
                    response = response.strip()
                    if not response.startswith("{") and not response.startswith("["):
                        # Try to extract JSON from markdown code blocks
                        if "```json" in response:
                            response = response.split("```json")[1].split("```")[0]
                        elif "```" in response:
                            response = response.split("```")[1].split("```")[0]
                else:
                    break

        logger.error("Failed to parse JSON after all attempts")
        return None

    def generate_text(
        self,
        prompt: str,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate free-form text (for novels, references)

        Args:
            prompt: Input prompt
            temperature: Generation temperature (higher = more creative)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            Generated text, or None on failure
        """
        return self.generate(
            prompt=prompt,
            format="",  # Free text
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )
