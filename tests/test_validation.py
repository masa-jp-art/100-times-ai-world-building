"""Tests for generated artifact contracts."""

from src.validation import validate_artifact, validate_phase_state


def test_phase1_count_validation():
    assert validate_artifact("desire_list", {"desires": ["one"]})
    assert not validate_artifact(
        "desire_list", {"desires": [str(index) for index in range(100)]}
    )


def test_phase4_requires_all_ten_chapter_artifacts():
    state = {"plot": {"plot": {"chapters": []}}}
    errors = validate_phase_state("phase4_plot", state)
    assert any("plot.chapters" in error for error in errors)
    assert any("missing plot_1" in error for error in errors)


def test_future_scenarios_require_three_types():
    errors = validate_artifact(
        "future_scenarios",
        {"scenarios": [{"scenario_type": "optimistic"}]},
    )
    assert any("3 items" in error for error in errors)
    assert any("pessimistic" in error for error in errors)
