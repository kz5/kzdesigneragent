# Antigravity Designer Agent

This repository contains the native Antigravity implementation of the Designer Agent, utilizing the **CLI-Driven Background Orchestrator** architecture to perform complex map-reduce design tasks via concurrent sub-agents.

## Prerequisites
- **Antigravity CLI**: You must have Antigravity installed and accessible via your terminal.
- **Python 3.7+**: Required to run the orchestration script.

## Setup
1. **Configure the Orchestrator**: 
   Open `orchestrator.py` and ensure the `ANTIGRAVITY_CLI_COMMAND` variable matches how you invoke Antigravity on your machine (e.g., `antigravity run --prompt`, `npx antigravity`, or a direct binary path).

## Installation
Antigravity officially supports Native Skill Packages. You can install the Designer Agent either globally across your machine, or locally for a specific project.

**Option 1: Global Installation (Recommended)**
Clone or copy this entire repository folder into your global skills directory:
```bash
mkdir -p ~/.gemini/antigravity/skills/designer-agent
cp -r * ~/.gemini/antigravity/skills/designer-agent/
```

**Option 2: Workspace Installation**
If you only want this agent available in a specific project, copy the repository into your project's local agent folder:
```bash
mkdir -p .agents/skills/designer-agent
cp -r * .agents/skills/designer-agent/
```

## How to Use
Once installed, you do not need any special CLI commands or bash aliases. 

1. Open your Antigravity chat interface.
2. Tag the skill by name and provide your prompt:
   > `@designer-agent Design a scalable microservices architecture for an e-commerce checkout flow.`

3. **Sit Back and Watch**:
   The Main Agent will automatically read `SKILL.md` and guide you through the 5 stages:
   - **Stage 1**: It will generate `scope.md`.
   - **Stage 2**: It will use `run_command` to execute the bundled `orchestrator.py --stage 2`, spinning up 6 concurrent background CLI sessions to write initial designs.
   - **Stage 3**: It will execute `orchestrator.py --stage 3`, spinning up 3 concurrent background CLI sessions to consolidate the designs.
   - **Stage 4**: It will read the results and output `final_design.md`, complete with alternative options analysis and risks listed in descending order.
   - **Stage 5**: It will perform a final review and consistency check on the output design, verifying that no content contradicts itself, and applying corrections if needed.

## Concurrency and Rate Limits
The `orchestrator.py` script uses a semaphore (default set to `3`) to prevent system resource exhaustion from spawning too many heavy LLM processes at once. You can adjust `MAX_CONCURRENCY` in the python script depending on your machine's capabilities and your API rate limits.
