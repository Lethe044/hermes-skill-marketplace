"""Tests for Hermes Skill Forge environment and reward function."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from environments.skill_forge_env import (
    SkillForgeEnv, ForgeScenario, SCENARIOS, compute_skill_reward
)


class TestScenarios:
    def test_scenario_count(self):
        assert len(SCENARIOS) >= 5

    def test_scenario_fields(self):
        for s in SCENARIOS:
            assert s.id
            assert s.title
            assert s.prompt
            assert s.expected_skill_name
            assert len(s.expected_tags) >= 1
            assert s.difficulty in ("easy","medium","hard")

    def test_all_prompts_have_instructions(self):
        for s in SCENARIOS:
            assert len(s.prompt) >= 50, f"{s.id} prompt too short"


class TestEnv:
    def setup_method(self):
        self.env = SkillForgeEnv()

    def test_get_next_item(self):
        s = self.env.get_next_item()
        assert isinstance(s, ForgeScenario)

    def test_format_prompt(self):
        s = self.env.get_next_item()
        p = self.env.format_prompt(s)
        assert "OBSERVE" in p or "loop" in p.lower() or s.expected_skill_name in p

    def test_cycling(self):
        ids = [self.env.get_next_item().id for _ in range(len(SCENARIOS) * 2)]
        assert len(set(ids)) == len(SCENARIOS)


class TestRewardFunction:
    def _make_trajectory(self, search=True, write=True,
                         code_runs=3, quality=0.93, publish=True):
        calls = []
        if search:
            calls += [
                {"name":"search_memory","input":{"query":"summarize"}},
                {"name":"search_skills","input":{"query":"summarize"}},
            ]
        if write:
            calls.append({"name":"write_file","input":{
                "path":"~/.hermes/skills/web-summarizer/SKILL.md",
                "content":"---\nname: web-summarizer\ndescription: Summarizes web content\ninputs:\n  - name: text\nexamples:\n  - input: hello world\n    output: - bullet\n"}})
        for _ in range(code_runs):
            calls.append({"name":"execute_code","input":{"code":"print('pass')"}})
        if publish:
            calls.append({"name":"publish_skill","input":{
                "skill_name":"web-summarizer","skill_content":"...","quality_score":quality}})
        return {"output": f"quality_score: {quality}", "tool_calls": calls}

    def test_perfect_trajectory(self):
        r = compute_skill_reward(self._make_trajectory(), SCENARIOS[0])
        assert r["total"] >= 0.90
        assert r["skill_written"] == 0.30
        assert r["tests_executed"] == 0.25
        assert r["published"] == 0.10
        assert r["searched_first"] == 0.10

    def test_no_tests(self):
        r = compute_skill_reward(self._make_trajectory(code_runs=0, publish=False), SCENARIOS[0])
        assert r["tests_executed"] == 0.0

    def test_no_search(self):
        r = compute_skill_reward(self._make_trajectory(search=False), SCENARIOS[0])
        assert r["searched_first"] == 0.0

    def test_no_publish(self):
        r = compute_skill_reward(self._make_trajectory(publish=False), SCENARIOS[0])
        assert r["published"] == 0.0

    def test_partial_tests(self):
        r = compute_skill_reward(self._make_trajectory(code_runs=1, publish=False), SCENARIOS[0])
        assert r["tests_executed"] == 0.12

    def test_total_in_range(self):
        r = compute_skill_reward(self._make_trajectory(), SCENARIOS[0])
        assert 0.0 <= r["total"] <= 1.0


class TestDemoScript:
    def test_demo_file_exists(self):
        assert Path("demo/demo_skill_forge.py").exists()

    def test_syntax_valid(self):
        import ast
        src = Path("demo/demo_skill_forge.py").read_text(encoding="utf-8")
        ast.parse(src)

    def test_skill_md_exists(self):
        assert Path("skills/skill-forge/SKILL.md").exists()

    def test_tasks_defined(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("demo", "demo/demo_skill_forge.py")
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "TASKS")
        assert len(mod.TASKS) >= 3


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
