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
    def test_default_model_is_gpt_oss_20b(self, mock_load_prompts, mock_load_config, mock_config, mock_prompts):
        """Default local model must be gpt-oss:20b"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts

        pipeline = Pipeline()

        assert pipeline.client.model == "gpt-oss:20b"

    @patch('src.pipeline.load_config')
    @patch('src.pipeline.load_prompts')
    def test_model_override(self, mock_load_prompts, mock_load_config, mock_config, mock_prompts):
        """Explicit model parameter must override config value"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts

        for model_name in ("gpt-oss:20b-q8", "gpt-oss:20b-q4", "gpt-oss:120b"):
            pipeline = Pipeline(model=model_name)
            assert pipeline.client.model == model_name

    @patch('src.pipeline.load_config')
    @patch('src.pipeline.load_prompts')
    def test_per_run_output_directory(self, mock_load_prompts, mock_load_config, mock_config, mock_prompts):
        """Each pipeline instance must use a unique per-run output directory"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts

        p1 = Pipeline(run_id="20260101_000000")
        p2 = Pipeline(run_id="20260101_000001")

        assert p1.base_dir == "./output/run_20260101_000000"
        assert p2.base_dir == "./output/run_20260101_000001"
        assert p1.base_dir != p2.base_dir

    @patch('src.pipeline.load_config')
    @patch('src.pipeline.load_prompts')
    def test_run_id_is_set(self, mock_load_prompts, mock_load_config, mock_config, mock_prompts):
        """Pipeline must expose its run_id attribute"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts

        pipeline = Pipeline(run_id="test_run_42")

        assert pipeline.run_id == "test_run_42"

    @patch('src.pipeline.load_config')
    @patch('src.pipeline.load_prompts')
    def test_checkpoint_dir_uses_run_id(self, mock_load_prompts, mock_load_config, mock_config, mock_prompts):
        """Checkpoint directory must be nested inside the per-run output directory"""
        mock_load_config.return_value = mock_config
        mock_load_prompts.return_value = mock_prompts

        pipeline = Pipeline(run_id="abc")

        assert pipeline.checkpoint_manager.checkpoint_dir == Path("./output/run_abc/checkpoints")

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
