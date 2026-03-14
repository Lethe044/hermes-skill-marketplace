"""
Tests for Hermes Skill Forge
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from environments.skill_forge_env import (
    SkillForgeEnv,
    SkillScenario,
    SKILL_SCENARIOS,
    compute_skill_reward,
)


class TestScenarios:
    def test_scenarios_exist(self):
        assert len(SKILL_SCENARIOS) >= 5

    def test_scenario_fields(self):
        for s in SKILL_SCENARIOS:
            assert s.id
            assert s.category
            assert s.title
            assert s.task_prompt
            assert len(s.success_criteria) >= 2
            assert len(s.partial_criteria) >= 1

    def test_scenario_ids_unique(self):
        ids = [s.id for s in SKILL_SCENARIOS]
        assert len(ids) == len(set(ids))


class TestReward:
    def _make_reward(self, tools, inputs, outputs, response="done"):
        scenario = SKILL_SCENARIOS[0]
        return compute_skill_reward(tools, inputs, outputs, response, scenario)

    def test_perfect_agent_gets_high_reward(self):
        r = self._make_reward(
            tools=["search_memory", "execute_code", "write_skill", "simulate_publish", "update_memory"],
            inputs=[
                {"query": "test"},
                {"code": "print('ok')"},
                {"skill_name": "test", "content": "---\nname: x\ndescription: y\n---\n## Steps\n1. x\n## Error Handling\nhandle"},
                {"skill_name": "test", "skill_content": "...", "test_passed": True},
                {"key": "k", "value": "v"},
            ],
            outputs=["found", "[exit_code=0]", "Written", "Published", "Updated"],
        )
        assert r["total"] >= 0.9

    def test_lazy_agent_gets_low_reward(self):
        r = self._make_reward(tools=[], inputs=[], outputs=[])
        assert r["total"] == 0.0

    def test_partial_agent_gets_partial_reward(self):
        r = self._make_reward(
            tools=["write_skill"],
            inputs=[{"skill_name": "test", "content": "basic content"}],
            outputs=["Written"],
        )
        assert 0.2 < r["total"] < 0.8

    def test_publish_without_test_gets_partial(self):
        r = self._make_reward(
            tools=["write_skill", "simulate_publish"],
            inputs=[
                {"skill_name": "test", "content": "content"},
                {"skill_name": "test", "skill_content": "...", "test_passed": False},
            ],
            outputs=["Written", "Rejected"],
        )
        assert r["skill_published"] == 0.05

    def test_reward_components_sum_correctly(self):
        r = self._make_reward(
            tools=["search_memory", "execute_code", "write_skill", "simulate_publish", "update_memory"],
            inputs=[
                {"query": "x"},
                {"code": "x=1"},
                {"skill_name": "s", "content": "---\nname: s\ndescription: d\n---\n## Steps\n1.x\n## Error Handling\ne"},
                {"skill_name": "s", "skill_content": "...", "test_passed": True},
                {"key": "k", "value": "v"},
            ],
            outputs=["", "", "", "", ""],
        )
        component_sum = sum(v for k, v in r.items() if k != "total")
        assert abs(component_sum - r["total"]) < 0.01


class TestEnvironment:
    def test_env_creates(self):
        env = SkillForgeEnv()
        assert env is not None

    def test_get_next_scenario_cycles(self):
        env = SkillForgeEnv()
        seen = set()
        for _ in range(len(SKILL_SCENARIOS) * 2):
            s = env.get_next_scenario()
            seen.add(s.id)
        assert len(seen) == len(SKILL_SCENARIOS)

    def test_format_prompt_contains_task(self):
        env = SkillForgeEnv()
        s = SKILL_SCENARIOS[0]
        prompt = env.format_prompt(s)
        assert s.title in prompt
        assert "skill" in prompt.lower()

    def test_evaluate_returns_reward(self):
        env = SkillForgeEnv()
        s = SKILL_SCENARIOS[0]
        result = env.evaluate(
            s,
            tool_calls=["write_skill", "execute_code"],
            tool_inputs=[
                {"skill_name": "x", "content": "content"},
                {"code": "print('ok')"},
            ],
            tool_outputs=["Written", "[exit_code=0]"],
            final_response="Done",
        )
        assert "total_reward" in result
        assert 0.0 <= result["total_reward"] <= 1.0


class TestSkillFile:
    def test_skill_md_exists(self):
        skill_path = Path(__file__).parent.parent / "skills" / "skill-forge" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    def test_skill_md_has_required_sections(self):
        skill_path = Path(__file__).parent.parent / "skills" / "skill-forge" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "OBSERVE" in content
        assert "WRITE" in content
        assert "TEST" in content
        assert "PUBLISH" in content

    def test_skill_md_has_core_loop(self):
        skill_path = Path(__file__).parent.parent / "skills" / "skill-forge" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "Core Loop" in content or "core loop" in content.lower()


class TestDemoScript:
    def test_demo_script_exists(self):
        demo_path = Path(__file__).parent.parent / "demo" / "demo_skill_forge.py"
        assert demo_path.exists()

    def test_demo_tasks_defined(self):
        demo_path = Path(__file__).parent.parent / "demo" / "demo_skill_forge.py"
        content = demo_path.read_text(encoding="utf-8")
        assert "summarize" in content
        assert "code-review" in content
        assert "data-clean" in content
        assert "research" in content

    def test_all_tools_have_dispatch(self):
        demo_path = Path(__file__).parent.parent / "demo" / "demo_skill_forge.py"
        content = demo_path.read_text(encoding="utf-8")
        for tool in ["execute_code", "write_skill", "read_skill", "simulate_publish", "update_memory"]:
            assert tool in content, f"Tool {tool} missing from demo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
