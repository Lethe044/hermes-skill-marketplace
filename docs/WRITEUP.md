# Hermes Skill Forge — Technical Writeup

## The Problem

Every developer has a folder of one-off scripts.
The same patterns get rewritten every week.
Someone figures out the best way to parse a log file, summarize an article,
or review a function for code smells — and that knowledge disappears when the terminal closes.

Skills exist on agentskills.io. But today, humans write them.
What if Hermes wrote them itself?

## The Solution

Hermes Skill Forge is a self-evolving agent.
Give it a repeated task. It abstracts the reusable pattern, writes a Skill,
tests it in a Python sandbox with 3 test cases, refines it until quality >= 0.8,
and publishes it — so every Hermes agent in the community benefits forever.

## The Full Loop

```
OBSERVE → ABSTRACT → WRITE → TEST → REFINE → PUBLISH
```

**OBSERVE:** After completing a task, Hermes searches its memory and the marketplace.
Has this pattern been solved before? If yes — use the existing skill. If no — proceed.

**ABSTRACT:** Extract the reusable core. Strip task-specific details.
Define generic inputs, expected outputs, and failure modes.

**WRITE:** Create a SKILL.md with YAML frontmatter: name, version, description,
author, tags, inputs, outputs.

**TEST:** Execute 3 real Python test cases in a sandbox:
- Happy path (normal input → correct output)
- Edge case (unusual but valid input → graceful handling)
- Error case (invalid input → no crash, clear error message)

**REFINE:** If quality_score < 0.8, identify failures, rewrite the skill, retest.
The agent never gives up after a single failure.

**PUBLISH:** If quality_score >= 0.8, simulate a PR to agentskills.io.
The skill is stored locally and logged to memory for future reference.

## Auto-Evaluator

After each round of test executions, an auto-evaluator injects a quality assessment
into the conversation: `quality_score = passing_tests / 3`.

If score >= 0.8, it explicitly tells the agent to call `publish_skill` immediately.
This closes the loop reliably without the agent losing track of its goal.

## Atropos RL Integration

The reward function trains Hermes to become a better skill forger over time:

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Skill Written | 30% | Did it create a SKILL.md? |
| Tests Executed | 25% | Did it run real Python tests? |
| Quality Score | 20% | Did it achieve quality >= 0.8? |
| Published | 10% | Did it complete the full loop? |
| Searched First | 10% | Did it check for duplicates? |
| Documentation | 5% | Is the skill clear and usable? |

5 training scenarios of increasing difficulty (easy → hard) ensure the agent
learns to handle simple and complex skill-forging tasks alike.

## Why This Matters

NousResearch's vision is self-improving agents.
Hermes Skill Forge makes that concrete and measurable:
- Each task → one new community skill
- Each skill → Hermes gets permanently better
- Each session → the whole ecosystem improves

That's not automation. It's **self-directed skill acquisition at community scale**.
