"""
Tests for OllamaClient module
"""

import pytest
from unittest.mock import Mock, patch
from src.ollama_client import OllamaClient


class TestOllamaClient:
    """Test cases for OllamaClient"""

    def test_initialization(self):
        """Test client initialization"""
        client = OllamaClient(
            host="http://localhost",
            port=11434,
            model="gpt-oss:20b"
        )

        assert client.base_url == "http://localhost:11434"
        assert client.model == "gpt-oss:20b"
        assert client.timeout == 300
        assert client.max_retries == 3

    def test_check_server_success(self):
        """Test server check when server is running"""
        client = OllamaClient()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = client.check_server()
            assert result is True

    def test_check_server_failure(self):
        """Test server check when server is not running"""
        client = OllamaClient()

        with patch('requests.get') as mock_get:
            mock_get.side_effect = ConnectionError()

            result = client.check_server()
            assert result is False

    @patch('requests.post')
    def test_generate_success(self, mock_post):
        """Test successful text generation"""
        client = OllamaClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated text"
        }
        mock_post.return_value = mock_response

        result = client.generate("Test prompt")
        assert result == "Generated text"

    @patch('requests.post')
    def test_generate_json_success(self, mock_post):
        """Test successful JSON generation"""
        client = OllamaClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"key": "value"}'
        }
        mock_post.return_value = mock_response

        result = client.generate_json("Test prompt")
        assert result == {"key": "value"}

    @patch('requests.post')
    def test_generate_retry_on_failure(self, mock_post):
        """Test retry mechanism on failure"""
        client = OllamaClient(max_retries=2, retry_delay=0)

        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.json.return_value = {"response": ""}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "response": "Success"
        }

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        result = client.generate("Test prompt")
        assert result == "Success"
        assert mock_post.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
