# Hermes Skill Forge 🔨

**Self-evolving agent that turns repeated tasks into reusable Skills - autonomously.**

> Built for the NousResearch "Show us what Hermes Agent can do" hackathon.

## What It Does

Hermes Skill Forge watches itself complete tasks, identifies reusable patterns,
writes a Skill, tests it in a Python sandbox, refines it until quality >= 0.8,
then publishes it to the agentskills.io marketplace.

**The more it works, the smarter it gets.**

## Architecture

```mermaid
flowchart TD
    A([🔔 Repeated Task Detected]) --> B
    B[🔍 OBSERVE<br/>Search memory + marketplace<br/>Avoid duplication] --> C
    C[💡 ABSTRACT<br/>Extract reusable pattern<br/>Define inputs & outputs] --> D
    D[📝 WRITE<br/>Create SKILL.md<br/>With YAML frontmatter] --> E
    E[🧪 TEST<br/>Run 3 test cases in sandbox<br/>Happy · Edge · Error] --> F
    F{quality_score >= 0.8?}
    F -- Yes --> G[🚀 PUBLISH<br/>Simulate PR to<br/>agentskills.io]
    F -- No  --> H[🔧 REFINE<br/>Fix failures<br/>Rewrite skill]
    H --> E
    G --> I([🧠 UPDATE MEMORY<br/>Skill stored forever<br/>Never duplicated])

    style A fill:#c0392b,color:#fff
    style G fill:#27ae60,color:#fff
    style F fill:#e67e22,color:#fff
    style I fill:#8e44ad,color:#fff
```

## Hermes Features Used

| Feature | How It's Used |
|---------|--------------|
| **Memory** | Remembers every skill ever created - searches before writing to avoid duplication |
| **Skills** | Writes and self-installs new SKILL.md files to `~/.hermes/skills/` |
| **execute_code** | Tests each skill with 3 real Python test cases in a sandbox |
| **Auto-Evaluator** | After tests run, automatically calculates quality_score and triggers publish if >= 0.8 |
| **Subagents** | Parallel refinement loops when quality < 0.8 - rewrite and retest |
| **Atropos RL** | Reward function trains Hermes to forge better skills over time |
| **Gateway** | Simulates PR submission to agentskills.io community marketplace |

## Reward Function

```mermaid
pie title Skill Forge Reward Components
    "Skill Written - SKILL.md created?" : 30
    "Tests Executed - Real Python run?" : 25
    "Quality Score - Achieved >= 0.8?" : 20
    "Published - Passed quality gate?" : 10
    "Searched First - No duplication?" : 10
    "Documentation - Clear + examples?" : 5
```

## Quick Start

```bash
pip install openai rich
set OPENROUTER_API_KEY=sk-or-...

python demo/demo_skill_forge.py --task web-summarizer
python demo/demo_skill_forge.py --task log-analyzer
python demo/demo_skill_forge.py --task code-reviewer
```

## Demo Output (web-summarizer)

```
🧠 search_memory     → Memory is empty.
🔍 search_skills     → No matching skills found.
📝 write_file        → Written SKILL.md to ~/.hermes/skills/web-summarizer/
🧪 execute_code      → HAPPY ['sentence one', 'sentence two', 'sentence three']
🧪 execute_code      → EDGE  ['No content to summarize']
🧪 execute_code      → ERROR ValueError (handled gracefully)
[AUTO EVALUATOR]     → quality_score=1.00 ✓ - calling publish_skill
🚀 publish_skill     → Published! PR: github.com/NousResearch/agentskills/pull/1890

Quality score: 1.00 | Skills written: 1 | Published: 1
```

## Demo Scenarios

| Scenario | What Hermes Forges | Difficulty |
|----------|-------------------|------------|
| `web-summarizer` | Fetch text → 3 bullet summary | Easy |
| `log-analyzer` | Parse logs → count errors by type | Medium |
| `code-reviewer` | Detect code smells automatically | Medium |

## Project Structure

```mermaid
graph LR
    A[hermes-skill-marketplace] --> B[skills/]
    A --> C[environments/]
    A --> D[demo/]
    A --> E[tests/]
    A --> F[docs/]

    B --> B1[skill-forge/SKILL.md<br/>Agent playbook]
    C --> C1[skill_forge_env.py<br/>Atropos RL environment]
    C --> C2[skill_forge_config.yaml<br/>Training config]
    D --> D1[demo_skill_forge.py<br/>Standalone demo]
    E --> E1[test_skill_forge_env.py<br/>Pytest suite]

    style B1 fill:#27ae60,color:#fff
    style C1 fill:#8e44ad,color:#fff
    style D1 fill:#e67e22,color:#fff
```

## Running Tests

```bash
python -m pytest tests/ -v
# or without pytest:
python -c "from environments.skill_forge_env import smoke_test; smoke_test()"
```

## Why This Wins

Most agents do a task and stop. Hermes Skill Forge does a task
and makes itself better at that task forever.

Every skill it publishes becomes available to every other Hermes agent.
That's not automation - it's **self-directed skill acquisition at community scale**.
