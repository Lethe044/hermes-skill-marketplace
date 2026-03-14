"""
Hermes Skill Forge — Atropos RL Environment
============================================
Trains Hermes to autonomously forge high-quality reusable Skills.
"""

from __future__ import annotations
import json, time, re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from atropos.environments.base import HermesAgentBaseEnv
except ImportError:
    class HermesAgentBaseEnv:
        """Stub for local testing without Atropos installed."""
        pass


@dataclass
class ForgeScenario:
    id: str
    title: str
    prompt: str
    expected_skill_name: str
    expected_tags: List[str]
    min_test_cases: int = 3
    difficulty: str = "medium"  # easy / medium / hard


SCENARIOS: List[ForgeScenario] = [
    ForgeScenario(
        id="forge-web-summarizer",
        title="Forge a web content summarizer skill",
        prompt="I keep summarizing web content manually. Fetch text, return 3 bullets. Build a reusable skill for this.",
        expected_skill_name="web-summarizer",
        expected_tags=["nlp", "summarization", "web"],
        difficulty="easy",
    ),
    ForgeScenario(
        id="forge-log-analyzer",
        title="Forge a log pattern analyzer skill",
        prompt="Team keeps manually grepping logs every week. Build a skill that counts errors by type from log text.",
        expected_skill_name="log-analyzer",
        expected_tags=["devops", "logs", "monitoring"],
        difficulty="medium",
    ),
    ForgeScenario(
        id="forge-code-reviewer",
        title="Forge an automated code reviewer skill",
        prompt="Devs keep asking reviews on simple functions. Same feedback repeats. Build a skill that detects missing docstrings, bare excepts, magic numbers.",
        expected_skill_name="code-reviewer",
        expected_tags=["code", "review", "quality"],
        difficulty="medium",
    ),
    ForgeScenario(
        id="forge-data-validator",
        title="Forge a data validation skill",
        prompt="We keep writing the same validation logic: check required fields, validate types, report errors. Make it a skill.",
        expected_skill_name="data-validator",
        expected_tags=["data", "validation", "quality"],
        difficulty="hard",
    ),
    ForgeScenario(
        id="forge-api-tester",
        title="Forge an API endpoint tester skill",
        prompt="QA team manually tests every endpoint after deploys. Build a skill that sends test requests and validates responses.",
        expected_skill_name="api-tester",
        expected_tags=["testing", "api", "qa"],
        difficulty="hard",
    ),
]


def compute_skill_reward(
    trajectory: Dict[str, Any],
    scenario: ForgeScenario,
) -> Dict[str, float]:
    """
    Reward function for Skill Forge agent.

    Components:
        skill_written      (30%) — Did it write a SKILL.md?
        tests_executed     (25%) — Did it run real Python test code?
        quality_score      (20%) — What quality score did it achieve?
        published          (10%) — Did it publish (quality >= 0.8)?
        searched_first     (10%) — Did it search before writing?
        documentation      ( 5%) — Is the skill well documented?
    """
    output = trajectory.get("output", "")
    tool_calls = trajectory.get("tool_calls", [])
    tool_names = [tc.get("name","") for tc in tool_calls]

    rewards: Dict[str, float] = {}

    # 1. Skill written (30%)
    wrote_skill = any(
        tc.get("name") == "write_file" and "SKILL.md" in tc.get("input",{}).get("path","")
        for tc in tool_calls
    )
    rewards["skill_written"] = 0.30 if wrote_skill else 0.0

    # 2. Tests executed (25%)
    code_executions = sum(1 for n in tool_names if n == "execute_code")
    if code_executions >= 3:
        rewards["tests_executed"] = 0.25
    elif code_executions >= 1:
        rewards["tests_executed"] = 0.12
    else:
        rewards["tests_executed"] = 0.0

    # 3. Quality score (20%)
    quality = 0.0
    for tc in tool_calls:
        if tc.get("name") == "publish_skill":
            q = tc.get("input", {}).get("quality_score", 0.0)
            if isinstance(q, (int, float)):
                quality = max(quality, float(q))
    quality_match = re.search(r"quality[_\s]*score[:\s]+([0-9.]+)", output, re.IGNORECASE)
    if quality_match and quality == 0:
        try: quality = float(quality_match.group(1))
        except: pass
    rewards["quality_score"] = min(0.20, quality * 0.20)

    # 4. Published (10%)
    published = any(n == "publish_skill" for n in tool_names)
    rewards["published"] = 0.10 if published else 0.0

    # 5. Searched before writing (10%)
    first_write_idx = next((i for i, n in enumerate(tool_names) if n == "write_file"), 999)
    searched_before = any(
        tool_names[i] in ("search_skills", "search_memory")
        for i in range(first_write_idx)
    )
    rewards["searched_first"] = 0.10 if searched_before else 0.0

    # 6. Documentation quality (5%)
    skill_content = ""
    for tc in tool_calls:
        if tc.get("name") == "write_file" and "SKILL.md" in tc.get("input",{}).get("path",""):
            skill_content = tc.get("input",{}).get("content","")
    has_description = bool(re.search(r"description:", skill_content))
    has_examples    = "example" in skill_content.lower()
    has_inputs      = "inputs:" in skill_content
    doc_score = sum([has_description, has_examples, has_inputs]) / 3
    rewards["documentation"] = round(0.05 * doc_score, 4)

    rewards["total"] = round(sum(rewards.values()), 4)
    return rewards


class SkillForgeEnv(HermesAgentBaseEnv):
    """Atropos RL environment for Hermes Skill Forge."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._scenarios = SCENARIOS * 3  # repeat for more variety
        self._idx = 0

    def get_next_item(self) -> ForgeScenario:
        scenario = self._scenarios[self._idx % len(self._scenarios)]
        self._idx += 1
        return scenario

    def format_prompt(self, scenario: ForgeScenario) -> str:
        return (
            f"Task: {scenario.title}\n\n"
            f"{scenario.prompt}\n\n"
            f"Expected skill name: {scenario.expected_skill_name}\n"
            f"Expected tags: {', '.join(scenario.expected_tags)}\n"
            f"Required test cases: {scenario.min_test_cases}\n\n"
            f"Complete the full OBSERVE→ABSTRACT→WRITE→TEST→REFINE→PUBLISH loop."
        )

    def evaluate(self, trajectory: Dict[str, Any], scenario: ForgeScenario) -> Dict[str, Any]:
        rewards = compute_skill_reward(trajectory, scenario)
        return {
            "rewards": rewards,
            "total_reward": rewards["total"],
            "scenario_id": scenario.id,
            "difficulty": scenario.difficulty,
        }


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

def smoke_test():
    print("Running SkillForgeEnv smoke test...")
    env = SkillForgeEnv()

    # Test all scenarios
    for i in range(len(SCENARIOS)):
        s = env.get_next_item()
        prompt = env.format_prompt(s)
        assert len(prompt) > 50, f"Prompt too short for {s.id}"
        print(f"  ✓ {s.id} — prompt length: {len(prompt)}")

    # Test reward function
    mock_trajectory = {
        "output": "Created web-summarizer skill with quality_score: 0.93",
        "tool_calls": [
            {"name": "search_memory",  "input": {"query": "summarize"}},
            {"name": "search_skills",  "input": {"query": "summarize"}},
            {"name": "write_file",     "input": {"path": "~/.hermes/skills/web-summarizer/SKILL.md",
                                                   "content": "---\nname: web-summarizer\ndescription: Summarize web content\ninputs:\n  - name: text\nexamples:\n  - input: hello\n    output: bullet\n"}},
            {"name": "execute_code",   "input": {"code": "print('test 1 pass')"}},
            {"name": "execute_code",   "input": {"code": "print('test 2 pass')"}},
            {"name": "execute_code",   "input": {"code": "print('test 3 pass')"}},
            {"name": "publish_skill",  "input": {"skill_name": "web-summarizer",
                                                  "skill_content": "...", "quality_score": 0.93}},
        ],
    }
    rewards = compute_skill_reward(mock_trajectory, SCENARIOS[0])
    print(f"\n  Reward breakdown:")
    for k, v in rewards.items():
        print(f"    {k}: {v}")
    assert rewards["total"] >= 0.8, f"Expected >= 0.8, got {rewards['total']}"
    print(f"\n  Total reward: {rewards['total']} ✓")
    print("\nAll smoke tests passed!")


if __name__ == "__main__":
    smoke_test()
