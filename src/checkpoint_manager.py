"""
Checkpoint Manager Module
Handles saving and loading of checkpoints during pipeline execution
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger


class CheckpointManager:
    """Manages checkpoints for the AI world building pipeline"""

    def __init__(
        self,
        checkpoint_dir: str = "./output/checkpoints",
        auto_save: bool = True,
        compression: bool = False,
    ):
        """
        Initialize checkpoint manager

        Args:
            checkpoint_dir: Directory to store checkpoints
            auto_save: Whether to auto-save after each phase
            compression: Whether to compress checkpoint files (not implemented yet)
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save = auto_save
        self.compression = compression

        # In-memory state
        self.current_state: Dict[str, Any] = {}

        logger.info(f"CheckpointManager initialized: {self.checkpoint_dir}")

    def save_checkpoint(
        self,
        phase_name: str,
        data: Dict[str, Any],
        timestamp: Optional[str] = None,
    ) -> str:
        """
        Save checkpoint data

        Args:
            phase_name: Name of the phase (e.g., "phase1_expansion")
            data: Data to save
            timestamp: Optional timestamp (auto-generated if None)

        Returns:
            Path to saved checkpoint file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{phase_name}_{timestamp}.json"
        filepath = self.checkpoint_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ Checkpoint saved: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save checkpoint {filepath}: {e}")
            raise

    def load_checkpoint(self, phase_name: str) -> Optional[Dict[str, Any]]:
        """
        Load the latest checkpoint for a phase

        Args:
            phase_name: Name of the phase

        Returns:
            Checkpoint data, or None if not found
        """
        pattern = f"{phase_name}_*.json"
        checkpoint_files = sorted(
            self.checkpoint_dir.glob(pattern),
            reverse=True,  # Latest first
        )

        if not checkpoint_files:
            logger.warning(f"No checkpoint found for phase: {phase_name}")
            return None

        latest_checkpoint = checkpoint_files[0]

        try:
            with open(latest_checkpoint, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Loaded checkpoint: {latest_checkpoint}")
            return data

        except Exception as e:
            logger.error(f"Failed to load checkpoint {latest_checkpoint}: {e}")
            return None

    def load_specific_checkpoint(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific checkpoint file

        Args:
            filepath: Path to checkpoint file

        Returns:
            Checkpoint data, or None on error
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Loaded checkpoint: {filepath}")
            return data

        except FileNotFoundError:
            logger.error(f"Checkpoint file not found: {filepath}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in checkpoint {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load checkpoint {filepath}: {e}")
            return None

    def list_checkpoints(self, phase_name: Optional[str] = None) -> List[str]:
        """
        List all checkpoint files

        Args:
            phase_name: Optional phase name filter

        Returns:
            List of checkpoint file paths
        """
        if phase_name:
            pattern = f"{phase_name}_*.json"
        else:
            pattern = "*.json"

        checkpoint_files = sorted(
            self.checkpoint_dir.glob(pattern),
            reverse=True,
        )

        filepaths = [str(f) for f in checkpoint_files]
        logger.info(f"Found {len(filepaths)} checkpoint(s)")
        return filepaths

    def delete_checkpoint(self, filepath: str) -> bool:
        """
        Delete a checkpoint file

        Args:
            filepath: Path to checkpoint file

        Returns:
            True if successful, False otherwise
        """
        try:
            Path(filepath).unlink()
            logger.info(f"Deleted checkpoint: {filepath}")
            return True
        except FileNotFoundError:
            logger.error(f"Checkpoint file not found: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {filepath}: {e}")
            return False

    def clear_phase_checkpoints(self, phase_name: str) -> int:
        """
        Delete all checkpoints for a specific phase

        Args:
            phase_name: Name of the phase

        Returns:
            Number of deleted checkpoints
        """
        pattern = f"{phase_name}_*.json"
        checkpoint_files = list(self.checkpoint_dir.glob(pattern))

        deleted_count = 0
        for filepath in checkpoint_files:
            try:
                filepath.unlink()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete {filepath}: {e}")

        logger.info(f"Deleted {deleted_count} checkpoint(s) for phase: {phase_name}")
        return deleted_count

    def update_state(self, key: str, value: Any) -> None:
        """
        Update in-memory state

        Args:
            key: State key
            value: State value
        """
        self.current_state[key] = value
        logger.debug(f"Updated state: {key}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get value from in-memory state

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value
        """
        return self.current_state.get(key, default)

    def save_state(self, phase_name: str = "current_state") -> str:
        """
        Save current in-memory state to checkpoint

        Args:
            phase_name: Name for the state checkpoint

        Returns:
            Path to saved checkpoint
        """
        return self.save_checkpoint(phase_name, self.current_state)

    def load_state(self, phase_name: str = "current_state") -> bool:
        """
        Load checkpoint into in-memory state

        Args:
            phase_name: Name of the state checkpoint

        Returns:
            True if successful, False otherwise
        """
        data = self.load_checkpoint(phase_name)
        if data is not None:
            self.current_state = data
            logger.info("State loaded successfully")
            return True

        logger.warning("Failed to load state")
        return False

    def get_full_state(self) -> Dict[str, Any]:
        """
        Get the complete in-memory state

        Returns:
            Copy of current state dictionary
        """
        return self.current_state.copy()

    def clear_state(self) -> None:
        """Clear in-memory state"""
        self.current_state = {}
        logger.info("State cleared")

    def export_state_summary(self) -> str:
        """
        Export a summary of current state

        Returns:
            Human-readable summary string
        """
        lines = ["=" * 60]
        lines.append("Current State Summary")
        lines.append("=" * 60)

        if not self.current_state:
            lines.append("(empty)")
        else:
            for key, value in self.current_state.items():
                if isinstance(value, str):
                    preview = (
                        value[:100] + "..." if len(value) > 100 else value
                    )
                elif isinstance(value, (list, dict)):
                    preview = f"<{type(value).__name__} with {len(value)} items>"
                else:
                    preview = str(value)

                lines.append(f"{key}: {preview}")

        lines.append("=" * 60)
        return "\n".join(lines)
