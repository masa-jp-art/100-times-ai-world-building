"""
Tests for Pipeline module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.pipeline import Pipeline


class TestPipeline:
    """Test cases for Pipeline"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        return {
            "server": {
                "host": "http://localhost",
                "port": 11434,
                "timeout": 300,
                "max_retries": 3,
                "retry_delay": 5
            },
            "model": {
                "name": "gpt-oss:20b"
            },
            "checkpointing": {
                "output_dir": "./output/checkpoints",
                "auto_save": True,
                "compression": False
            },
            "output": {
                "base_dir": "./output"
            },
            "phases": {
                "phase1_expansion": {
                    "temperature": 0.8,
                    "num_predict": 4096
                }
            }
        }

    @pytest.fixture
    def mock_prompts(self):
        """Mock prompts"""
        return {
            "desire_list": {
                "system": "System prompt",
                "user": "Generate desires from: {user_context}"
            }
        }

    @patch('src.pipeline.load_config')
    @patch('src.pipeline.load_prompts')
    def test_initialization(self, mock_load_prompts, mock_load_config, mock_config, mock_prompts):
        """Test pipeline initialization"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts

        pipeline = Pipeline()

        assert pipeline.config == mock_config
        assert pipeline.prompts == mock_prompts
        assert pipeline.client is not None
        assert pipeline.checkpoint_manager is not None

    @patch('src.pipeline.load_config')
    @patch('src.pipeline.load_prompts')
    @patch.object(Pipeline, 'check_prerequisites')
    def test_check_prerequisites_success(
        self,
        mock_check_prereq,
        mock_load_prompts,
        mock_load_config,
        mock_config,
        mock_prompts
    ):
        """Test prerequisites check when all conditions are met"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts
        mock_check_prereq.return_value = True

        pipeline = Pipeline()
        result = pipeline.check_prerequisites()

        assert result is True

    @patch('src.pipeline.load_config')
    @patch('src.pipeline.load_prompts')
    def test_run_phase1_expansion(self, mock_load_prompts, mock_load_config, mock_config, mock_prompts):
        """Test Phase 1 expansion"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts

        pipeline = Pipeline()

        # Mock client responses
        pipeline.client.generate_json = Mock(return_value={
            "desires": ["desire1", "desire2"]
        })

        user_context = "Test context"
        results = pipeline.run_phase1_expansion(user_context)

        assert "desire_list" in results
        assert pipeline.client.generate_json.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
