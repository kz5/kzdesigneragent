# Final Design: The Antigravity Designer Agent

## Version
- **Version**: 1.0
- **Date**: 2026-05-13

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture](#architecture)
   - [1. The Core Capability](#1-the-core-capability)
   - [2. The Orchestrator Agent](#2-the-orchestrator-agent)
   - [3. Execution Flow (The 4 Stages)](#3-execution-flow)
     - [Stage 1: Scoping](#stage-1-scoping)
     - [Stage 2: Exploration](#stage-2-exploration)
     - [Stage 3: Consolidation](#stage-3-consolidation)
     - [Stage 4: Finalization](#stage-4-finalization)
     - [Stage 5: Review and Consistency Check](#stage-5-review-and-consistency-check)
3. [Design Output Rules](#design-output-rules)
4. [Data Management](#data-management)
5. [Why this is the Best Approach](#why-this-is-the-best-approach)
6. [Risks of the Proposed Architecture](#risks-of-the-proposed-architecture)
7. [Quality Check Functions](#quality-check-functions)

## Executive Summary
After a comprehensive 4-stage map-reduce evaluation of 6 distinct architectural approaches and 3 subsequent consolidations, this document presents the definitive design for the Antigravity Designer Agent. 

The core challenge is executing a `1 -> 6 -> 3 -> 1` concurrent sub-agent pipeline natively within Antigravity. To ensure the design is **100% native to Antigravity's current user-space capabilities**, the chosen architecture is the **CLI-Driven Background Orchestrator**. 

This approach leverages the existing `run_command` tool to spawn background `antigravity` CLI processes, fully utilizing the terminal environment as the orchestration layer.

## Architecture

### 1. The Core Capability: `run_command` & CLI
The Main Agent relies on its existing ability to write scripts and execute them in the terminal. The agent generates a Python `asyncio` script (or bash script) that calls the `antigravity` command-line interface concurrently.

### 2. The Orchestrator Agent (Main Agent)
The Designer Agent itself is a standard Main Agent session. It acts as the Scoper (Stage 1), the Script Writer (Stages 2 & 3), and the Finalizer (Stage 4).

### 3. Execution Flow (The 4 Stages)

**Stage 1: Scoping (Sequential)**
1. User provides the prompt: "Design X".
2. Main Agent asks clarifying questions if needed.
3. Main Agent synthesizes the requirements and uses `write_to_file` to generate `scope.md`.

**Stage 2: Exploration (Fan-Out 6x)**
1. Main Agent writes an orchestration script, `run_stage2.py`, to the workspace. This script uses Python's `asyncio.subprocess` to spawn 6 concurrent `antigravity run` commands, passing specific instructions for each of the 3 approaches.
2. Main Agent executes the script via `run_command` (waiting for it to finish).
3. The background CLI instances read `scope.md` and write their designs to the `stage2/` directory.

**Stage 3: Consolidation (Fan-In 3x)**
1. Upon successful return of the Stage 2 script, the Main Agent writes `run_stage3.py`.
2. This script spawns 3 concurrent `antigravity run` commands instructing them to read `stage2/` and consolidate the designs.
3. Main Agent executes the script via `run_command`. The CLI instances write to `stage3/`.

**Stage 4: Finalization (Sequential)**
1. Main Agent uses `view_file` or `grep_search` to read the 3 consolidated designs from `stage3/`.
2. Main Agent evaluates the 3 options, decides on the final architecture, and uses `write_to_file` to output `final_design.md`.

**Stage 5: Review and Consistency Check (Sequential)**
1. Main Agent uses `view_file` to read the newly generated `final_design.md`.
2. Main Agent performs a strict review to ensure the design is internally consistent and that no content contradicts itself.
3. If contradictions or inconsistencies are found, the Main Agent uses `write_to_file` or `replace_file_content` to apply corrections to `final_design.md`.

## Design Output Rules
To ensure a high-quality user experience and maintain clarity, the following strict rules apply to the generation of all Consolidated Designs (Stage 3) and the Final Design (Stage 4):
- **Completeness**: Each design document must be a fully complete, standalone design.
- **No Back-Referencing**: Documents must *never* say "As stated in previous design X" or "Referencing the earlier proposal". They must synthesize all required context directly into the new document.
- **Clarity for the User**: The narrative must be framed as a cohesive proposal addressing the original scope, explaining the "why" and "how" clearly without requiring the user to read the discarded intermediate files.
- **Alternative Options Analysis**: The document must explicitly discuss the alternative design options considered, debate their pros and cons, and provide clear reasoning for why the final option was chosen over the others.
- **Risks & Mitigations**: The generated design document must explicitly list out the risks of the proposed architecture in descending order of severity, along with corresponding mitigations.

## Data Management
- **File-System as Shared Memory**: The sub-agents do not return complex JSON objects to the Main Agent. They communicate entirely by writing to specific folders (`stage2/`, `stage3/`). This guarantees persistence, allows human observation, and cleanly bypasses LLM context window limits.

## Why this is the Best Approach
1. **Truly Native**: It uses 100% existing Antigravity capabilities (`run_command` and the CLI), ensuring the agent can be deployed immediately without platform changes.
2. **Highly Observable**: The user can see the `run_stage2.py` script being written and executed in their workspace.

## Risks of the Proposed Architecture (Trade-offs)
In accordance with the design output rules, here are the risks associated with the **CLI-Driven Background Orchestrator**, ordered by descending severity:

1. **System Resource Exhaustion (High Severity)**: Spawning 6 concurrent full CLI instances of Antigravity is extremely memory and CPU intensive, and could crash the user's local machine or hit severe LLM API rate limits. 
   - *Mitigation*: The `run_stage2.py` script must implement a semaphore to limit actual concurrency (e.g., max 2 or 3 parallel processes at a time) and handle API backoff.
2. **Brittle Inter-Process Communication (Medium Severity)**: Relying on shell subprocess execution is inherently more brittle than native API calls. If the Antigravity CLI crashes unexpectedly or changes its exit codes, the orchestrator script might fail or hang.
   - *Mitigation*: The Python orchestration scripts must implement robust `try/except` blocks, strict timeout limits on the subprocesses, and force the CLI to output strictly to log files for error tracing.
3. **Loss of UI Observability (Medium Severity)**: Because the sub-agents are running in terminal background processes rather than native Antigravity UI sub-agent windows, the user cannot see their real-time thought processes or tool calls in the main chat UI.
   - *Mitigation*: The orchestration script should pipe all sub-agent stdout/stderr logs to a centralized `pipeline.log` file, allowing the user to `tail -f` the file to watch the progress.

## Quality Check Functions
To ensure the Designer Agent operates reliably, the pipeline must implement the following quality check functions:
- **Context Window Exhaustion Check**: Stage 3 and 4 sub-agents must read multiple large markdown files. *Quality Check*: The Main Agent must enforce that Stage 2 output sizes are concise before passing them to Stage 3.
- **Hallucination Fan-In Check**: Stage 3 agents might hallucinate features that were not present in the Stage 2 documents. *Quality Check*: The CLI prompts must include a strict grounding verification step to ensure outputs are explicitly tied to the provided files.
