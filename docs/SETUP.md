# Setup Guide

## Requirements
Python 3.10+, OpenRouter API key (free at openrouter.ai)

## Install
pip install openai rich

## Configure
Windows:  set OPENROUTER_API_KEY=sk-or-...
Linux:    export OPENROUTER_API_KEY=sk-or-...

## Run
python demo/demo_skill_forge.py --task web-summarizer
python demo/demo_skill_forge.py --task log-analyzer
python demo/demo_skill_forge.py --task code-reviewer

## Output
Skills:    ~/.hermes/skills/
Published: ~/.hermes/published/
Memory:    ~/.hermes/skill_memory.jsonl
