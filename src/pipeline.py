"""
Pipeline Module
Main pipeline orchestration for 100 TIMES AI WORLD BUILDING
"""

from typing import Dict, Any, Optional
from loguru import logger
from tqdm import tqdm

from .ollama_client import OllamaClient
from .checkpoint_manager import CheckpointManager
from .utils import (
    load_config,
    load_prompts,
    format_prompt,
    dict_to_yaml,
    save_yaml,
    save_text,
)


class Pipeline:
    """Main pipeline for AI world building"""

    def __init__(
        self,
        config_path: str = "config/ollama_config.yaml",
        prompts_dir: str = "config/prompts",
    ):
        """
        Initialize pipeline

        Args:
            config_path: Path to configuration file
            prompts_dir: Directory containing prompt templates
        """
        # Load configuration
        self.config = load_config(config_path)

        # Initialize components
        server_config = self.config.get("server", {})
        model_config = self.config.get("model", {})

        self.client = OllamaClient(
            host=server_config.get("host", "http://localhost"),
            port=server_config.get("port", 11434),
            model=model_config.get("name", "gpt-oss:20b"),
            timeout=server_config.get("timeout", 300),
            max_retries=server_config.get("max_retries", 3),
            retry_delay=server_config.get("retry_delay", 5),
        )

        checkpoint_config = self.config.get("checkpointing", {})
        self.checkpoint_manager = CheckpointManager(
            checkpoint_dir=checkpoint_config.get("output_dir", "./output/checkpoints"),
            auto_save=checkpoint_config.get("auto_save", True),
            compression=checkpoint_config.get("compression", False),
        )

        # Load prompts
        self.prompts = load_prompts(prompts_dir)

        # Output configuration
        self.output_config = self.config.get("output", {})
        self.base_dir = self.output_config.get("base_dir", "./output")

        logger.info("Pipeline initialized")

    def check_prerequisites(self) -> bool:
        """
        Check if all prerequisites are met

        Returns:
            True if ready, False otherwise
        """
        logger.info("Checking prerequisites...")

        # Check Ollama server
        if not self.client.check_server():
            logger.error("Ollama server is not running. Please start it with: ollama serve")
            return False

        # Check model availability
        if not self.client.ensure_model_ready():
            logger.error("Model is not available and could not be downloaded")
            return False

        logger.info("✓ All prerequisites met")
        return True

    def run_phase0_context_extraction(self) -> str:
        """
        Phase 0: User context extraction
        Interactive dialog to extract user context

        Returns:
            User context as YAML string
        """
        logger.info("=== Phase 0: User Context Extraction ===")

        phase_config = self.config.get("phases", {}).get(
            "phase0_context_extraction", {}
        )

        # TODO: Implement interactive question generation
        # For now, return a placeholder
        user_context = """
        context:
          theme: "未来都市での人間と人工知能の共存"
          mood: "希望と不安が交錯する"
          setting: "2080年代の東京"
        """

        # Save checkpoint
        self.checkpoint_manager.save_checkpoint(
            "phase0_context",
            {"user_context": user_context}
        )

        # Save to intermediate directory
        save_yaml(
            {"user_context": user_context},
            f"{self.base_dir}/intermediate/00_user_context.yaml"
        )

        logger.info("✓ Phase 0 completed")
        return user_context

    def run_phase1_expansion(self, user_context: str) -> Dict[str, str]:
        """
        Phase 1: 100x expansion
        Generate desire list, ability list, role list, plot types

        Args:
            user_context: User context YAML string

        Returns:
            Dictionary of generated lists
        """
        logger.info("=== Phase 1: 100x Expansion ===")

        phase_config = self.config.get("phases", {}).get("phase1_expansion", {})
        results = {}

        # 1. Desire list
        logger.info("Generating desire list...")
        desire_prompt = self.prompts.get("desire_list", {})
        if desire_prompt:
            prompt = format_prompt(
                desire_prompt.get("user", ""),
                user_context=user_context
            )
            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.8),
                max_tokens=phase_config.get("num_predict", 4096),
            )
            if response:
                results["desire_list"] = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/01_desire_list.yaml")

        # 2. Ability list
        logger.info("Generating ability list...")
        ability_prompt = self.prompts.get("ability_list", {})
        if ability_prompt:
            prompt = format_prompt(
                ability_prompt.get("user", ""),
                user_context=user_context
            )
            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.8),
                max_tokens=phase_config.get("num_predict", 4096),
            )
            if response:
                results["ability_list"] = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/02_ability_list.yaml")

        # 3. Role list
        logger.info("Generating role list...")
        role_prompt = self.prompts.get("role_list", {})
        if role_prompt:
            prompt = format_prompt(
                role_prompt.get("user", ""),
                user_context=user_context
            )
            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.8),
                max_tokens=phase_config.get("num_predict", 4096),
            )
            if response:
                results["role_list"] = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/03_role_list.yaml")

        # 4. Plot type list
        logger.info("Generating plot type list...")
        plottype_list_prompt = self.prompts.get("plottype_list", {})
        if plottype_list_prompt:
            prompt = plottype_list_prompt.get("user", "")
            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.8),
                max_tokens=phase_config.get("num_predict", 4096),
            )
            if response:
                results["plottype_list"] = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/04_plottype_list.yaml")

        # 5. Select plot type
        logger.info("Selecting plot type...")
        plottype_selection_prompt = self.prompts.get("plottype_selection", {})
        if plottype_selection_prompt and "plottype_list" in results:
            prompt = format_prompt(
                plottype_selection_prompt.get("user", ""),
                user_context=user_context,
                plottype_list=results["plottype_list"]
            )
            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.8),
                max_tokens=phase_config.get("num_predict", 4096),
            )
            if response:
                results["plottype"] = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/05_plottype.yaml")

        # Save checkpoint
        self.checkpoint_manager.save_checkpoint("phase1_expansion", results)

        logger.info("✓ Phase 1 completed")
        return results

    def run_phase2_characters(self, user_context: str, phase1_results: Dict[str, str]) -> str:
        """
        Phase 2: Character generation
        Generate 4 main characters

        Args:
            user_context: User context YAML string
            phase1_results: Results from Phase 1

        Returns:
            Characters list as YAML string
        """
        logger.info("=== Phase 2: Character Generation ===")

        phase_config = self.config.get("phases", {}).get("phase2_characters", {})

        # Sample from lists for character assignment
        import random
        import yaml as yaml_lib

        desire_data = yaml_lib.safe_load(phase1_results.get("desire_list", "desires: []"))
        ability_data = yaml_lib.safe_load(phase1_results.get("ability_list", "abilities: []"))
        role_data = yaml_lib.safe_load(phase1_results.get("role_list", "roles: []"))

        desire_sample = random.sample(desire_data.get("desires", []), min(10, len(desire_data.get("desires", []))))
        ability_sample = random.sample(ability_data.get("abilities", []), min(10, len(ability_data.get("abilities", []))))
        role_sample = random.sample(role_data.get("roles", []), min(10, len(role_data.get("roles", []))))

        characters_prompt = self.prompts.get("characters", {})
        if characters_prompt:
            prompt = format_prompt(
                characters_prompt.get("user", ""),
                user_context=user_context,
                plottype=phase1_results.get("plottype", ""),
                desire_sample=str(desire_sample),
                ability_sample=str(ability_sample),
                role_sample=str(role_sample)
            )
            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.9),
                max_tokens=phase_config.get("num_predict", 2048),
            )
            if response:
                characters_yaml = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/06_characters_list.yaml")
                self.checkpoint_manager.save_checkpoint("phase2_characters", {"characters_list": characters_yaml})
                logger.info("✓ Phase 2 completed")
                return characters_yaml

        logger.warning("Phase 2 failed")
        return ""

    def run_phase3_world_building(self, phase1_results: Dict[str, str]) -> Dict[str, str]:
        """
        Phase 3: World building
        Generate all world setting elements

        Args:
            phase1_results: Results from Phase 1

        Returns:
            Dictionary of world settings
        """
        logger.info("=== Phase 3: World Building ===")

        phase_config = self.config.get("phases", {}).get("phase3_world", {})
        world_data = {}

        # List of world elements to generate (in order)
        elements = [
            ("events", {}),
            ("observation", {"events": "events"}),
            ("interpretation", {"events": "events", "observation": "observation"}),
            ("media", {"events": "events", "observation": "observation", "interpretation": "interpretation"}),
            ("important_past_events", {"events": "events", "observation": "observation", "interpretation": "interpretation", "media": "media"}),
            ("social_structure", {"events": "events", "observation": "observation", "interpretation": "interpretation", "media": "media", "important_past_events": "important_past_events"}),
            ("living_environment", {"social_structure": "social_structure"}),
            ("social_groups", {"social_structure": "social_structure", "living_environment": "living_environment"}),
            ("people_list", {"social_structure": "social_structure", "living_environment": "living_environment", "social_groups": "social_groups"}),
            ("future_scenarios", {}),  # Uses all accumulated context
        ]

        for i, (element_name, dependencies) in enumerate(elements, start=10):
            logger.info(f"Generating {element_name}...")

            element_prompt = self.prompts.get(element_name, {})
            if not element_prompt:
                logger.warning(f"No prompt found for {element_name}")
                continue

            # Build prompt with dependencies
            prompt_vars = {"plottype": phase1_results.get("plottype", "")}
            for dep_key, dep_value in dependencies.items():
                prompt_vars[dep_key] = world_data.get(dep_value, "")

            prompt = format_prompt(element_prompt.get("user", ""), **prompt_vars)

            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.7),
                max_tokens=phase_config.get("num_predict", 4096),
            )

            if response:
                world_data[element_name] = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/{i:02d}_{element_name}.yaml")

        # Save checkpoint
        self.checkpoint_manager.save_checkpoint("phase3_world", world_data)
        logger.info("✓ Phase 3 completed")
        return world_data

    def run_full_pipeline(self, user_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete pipeline

        Args:
            user_context: Optional pre-extracted user context

        Returns:
            Dictionary of all generated content
        """
        logger.info("=" * 60)
        logger.info("Starting Full Pipeline Execution")
        logger.info("=" * 60)

        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("Prerequisites not met. Aborting.")
            return {}

        results = {}

        # Phase 0: Context extraction
        if user_context is None:
            user_context = self.run_phase0_context_extraction()
        results["user_context"] = user_context

        # Phase 1: 100x expansion
        phase1_results = self.run_phase1_expansion(user_context)
        results.update(phase1_results)

        # Phase 2: Character generation
        characters_list = self.run_phase2_characters(user_context, phase1_results)
        results["characters_list"] = characters_list

        # Phase 3: World building
        world_data = self.run_phase3_world_building(phase1_results)
        results.update(world_data)

        # Phase 4: Plot generation
        plot_data = self.run_phase4_plot_generation(user_context, phase1_results, characters_list, world_data)
        results.update(plot_data)

        # Phase 5: Novel generation
        novels = self.run_phase5_novel_generation(characters_list, plot_data)
        results["novels"] = novels

        # Phase 6: Reference material generation
        references = self.run_phase6_reference_generation(user_context, phase1_results, characters_list, world_data, plot_data)
        results["references"] = references

        logger.info("=" * 60)
        logger.info("Pipeline Execution Complete")
        logger.info("=" * 60)

        return results

    def run_phase4_plot_generation(
        self,
        user_context: str,
        phase1_results: Dict[str, str],
        characters_list: str,
        world_data: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Phase 4: Plot generation
        Generate 10-chapter plot and extract keywords/references

        Args:
            user_context: User context
            phase1_results: Phase 1 results
            characters_list: Characters list
            world_data: World building data

        Returns:
            Dictionary of plot data
        """
        logger.info("=== Phase 4: Plot Generation ===")

        phase_config = self.config.get("phases", {}).get("phase4_plot", {})
        plot_data = {}

        # Generate main plot
        logger.info("Generating main plot...")
        plot_prompt = self.prompts.get("plot", {})
        if plot_prompt:
            prompt = format_prompt(
                plot_prompt.get("user", ""),
                user_context=user_context,
                plottype=phase1_results.get("plottype", ""),
                characters_list=characters_list
            )
            response = self.client.generate_json(
                prompt,
                temperature=phase_config.get("temperature", 0.8),
                max_tokens=phase_config.get("num_predict", 3072),
            )
            if response:
                plot_data["plot"] = dict_to_yaml(response)
                save_yaml(response, f"{self.base_dir}/intermediate/20_plot.yaml")

        # Extract and process each chapter
        logger.info("Processing chapters...")
        for chapter_num in tqdm(range(1, 11), desc="Chapters"):
            # Extract chapter
            extract_prompt = self.prompts.get("extract_chapter", {})
            if extract_prompt and "plot" in plot_data:
                prompt = format_prompt(
                    extract_prompt.get("user", ""),
                    plot=plot_data["plot"],
                    chapter_number=chapter_num
                )
                chapter_response = self.client.generate_json(prompt)
                if chapter_response:
                    plot_data[f"plot_{chapter_num}"] = dict_to_yaml(chapter_response)
                    save_yaml(chapter_response, f"{self.base_dir}/intermediate/{20 + chapter_num}_plot_{chapter_num}.yaml")

            # Extract keywords
            keywords_prompt = self.prompts.get("extract_keywords", {})
            if keywords_prompt and f"plot_{chapter_num}" in plot_data:
                prompt = format_prompt(
                    keywords_prompt.get("user", ""),
                    chapter_plot=plot_data[f"plot_{chapter_num}"]
                )
                keywords_response = self.client.generate_json(prompt)
                if keywords_response:
                    plot_data[f"plot_keywords_{chapter_num}"] = dict_to_yaml(keywords_response)
                    save_yaml(keywords_response, f"{self.base_dir}/intermediate/{30 + chapter_num}_plot_keywords_{chapter_num}.yaml")

            # Search references
            references_prompt = self.prompts.get("search_references", {})
            if references_prompt and f"plot_keywords_{chapter_num}" in plot_data:
                prompt = format_prompt(
                    references_prompt.get("user", ""),
                    keywords=plot_data[f"plot_keywords_{chapter_num}"],
                    world_data=str(world_data)[:2000]  # Truncate for context window
                )
                references_response = self.client.generate_json(prompt)
                if references_response:
                    plot_data[f"plot_reference_{chapter_num}"] = dict_to_yaml(references_response)
                    save_yaml(references_response, f"{self.base_dir}/intermediate/{40 + chapter_num}_plot_reference_{chapter_num}.yaml")

        self.checkpoint_manager.save_checkpoint("phase4_plot", plot_data)
        logger.info("✓ Phase 4 completed")
        return plot_data

    def run_phase5_novel_generation(
        self,
        characters_list: str,
        plot_data: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Phase 5: Novel generation
        Generate novel text for all 10 chapters

        Args:
            characters_list: Characters list
            plot_data: Plot data from Phase 4

        Returns:
            Dictionary of generated novels
        """
        logger.info("=== Phase 5: Novel Generation ===")

        phase_config = self.config.get("phases", {}).get("phase5_novel", {})
        novels = {}

        story_prompt = self.prompts.get("story_chapter", {})
        if not story_prompt:
            logger.error("No story prompt found")
            return novels

        for chapter_num in tqdm(range(1, 11), desc="Generating novels"):
            logger.info(f"Generating Chapter {chapter_num}...")

            prompt = format_prompt(
                story_prompt.get("user", ""),
                chapter_number=chapter_num,
                characters_list=characters_list,
                chapter_plot=plot_data.get(f"plot_{chapter_num}", ""),
                chapter_references=plot_data.get(f"plot_reference_{chapter_num}", "")
            )

            response = self.client.generate_text(
                prompt,
                temperature=phase_config.get("temperature", 1.0),
                max_tokens=phase_config.get("num_predict", 4096),
                system_prompt=story_prompt.get("system", "")
            )

            if response:
                novels[f"story_{chapter_num}"] = response
                save_text(response, f"{self.base_dir}/novels/chapter_{chapter_num:02d}.txt")

        self.checkpoint_manager.save_checkpoint("phase5_novels", novels)
        logger.info("✓ Phase 5 completed")
        return novels

    def run_phase6_reference_generation(
        self,
        user_context: str,
        phase1_results: Dict[str, str],
        characters_list: str,
        world_data: Dict[str, str],
        plot_data: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Phase 6: Reference material generation
        Generate detailed reference materials

        Args:
            user_context: User context
            phase1_results: Phase 1 results
            characters_list: Characters list
            world_data: World building data
            plot_data: Plot data

        Returns:
            Dictionary of generated references
        """
        logger.info("=== Phase 6: Reference Generation ===")

        phase_config = self.config.get("phases", {}).get("phase6_references", {})
        references = {}

        # List of references to generate
        reference_types = [
            ("reference_characters", "characters.md", {"characters_list": characters_list}),
            ("reference_plot", "plot.md", {"plot": plot_data.get("plot", "")}),
            ("reference_user_context", "user_context.md", {"user_context": user_context}),
            ("reference_desire_list", "desire_list.md", {"desire_list": phase1_results.get("desire_list", "")}),
            ("reference_ability_list", "ability_list.md", {"ability_list": phase1_results.get("ability_list", "")}),
            ("reference_role_list", "role_list.md", {"role_list": phase1_results.get("role_list", "")}),
            ("reference_plottype_list", "plottype_list.md", {"plottype_list": phase1_results.get("plottype_list", ""), "plottype": phase1_results.get("plottype", "")}),
        ]

        # Add world elements
        for element_name in world_data.keys():
            reference_types.append(
                ("reference_world_element", f"{element_name}.md", {"element_name": element_name, "element_data": world_data[element_name]})
            )

        for prompt_name, filename, prompt_vars in tqdm(reference_types, desc="Generating references"):
            logger.info(f"Generating {filename}...")

            ref_prompt = self.prompts.get(prompt_name, {})
            if not ref_prompt:
                logger.warning(f"No prompt found for {prompt_name}")
                continue

            prompt = format_prompt(ref_prompt.get("user", ""), **prompt_vars)

            response = self.client.generate_text(
                prompt,
                temperature=phase_config.get("temperature", 0.7),
                max_tokens=phase_config.get("num_predict", 4096),
                system_prompt=ref_prompt.get("system", "")
            )

            if response:
                references[filename] = response
                save_text(response, f"{self.base_dir}/references/{filename}")

        self.checkpoint_manager.save_checkpoint("phase6_references", references)
        logger.info("✓ Phase 6 completed")
        return references

    def resume_from_checkpoint(self, phase_name: str) -> bool:
        """
        Resume pipeline from a checkpoint

        Args:
            phase_name: Name of the phase to resume from

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Resuming from checkpoint: {phase_name}")

        checkpoint_data = self.checkpoint_manager.load_checkpoint(phase_name)
        if checkpoint_data is None:
            logger.error(f"Failed to load checkpoint: {phase_name}")
            return False

        # Load state
        for key, value in checkpoint_data.items():
            self.checkpoint_manager.update_state(key, value)

        logger.info("✓ Checkpoint loaded successfully")
        return True
