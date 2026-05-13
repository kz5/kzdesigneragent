import asyncio
import argparse
import os
import sys

# ==========================================
# CONFIGURATION
# ==========================================
# Update this command to match how you invoke the Antigravity CLI on your machine.
# Example: "antigravity run --prompt" or "npx antigravity --prompt"
ANTIGRAVITY_CLI_COMMAND = "antigravity run --prompt"

# Max concurrent heavy sub-agents to run to avoid crashing the machine
MAX_CONCURRENCY = 3

# ==========================================
# CONSTANT RULES INJECTED INTO SUB-AGENTS
# ==========================================
DESIGN_RULES = """
CRITICAL DESIGN OUTPUT RULES:
- Completeness: This must be a fully complete, standalone design document.
- No Back-Referencing: Do not say 'As stated in previous design X'. Synthesize all context.
- Alternative Options Analysis: Explicitly discuss alternative options considered, debate pros/cons, and reason why the chosen path is best.
- Risks & Mitigations: List risks of your proposed architecture in descending order of severity with mitigations.
"""

async def run_subagent(task_name, prompt, sem):
    """Spawns an Antigravity CLI process with the given prompt."""
    async with sem:
        print(f"[{task_name}] Starting sub-agent...")
        # Escape double quotes for the shell command
        safe_prompt = prompt.replace('"', '\\"')
        cmd = f'{ANTIGRAVITY_CLI_COMMAND} "{safe_prompt}"'
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print(f"[{task_name}] Completed successfully.")
            return True
        else:
            print(f"[{task_name}] FAILED with exit code {process.returncode}")
            print(f"[{task_name}] Error output: {stderr.decode().strip()}")
            return False

async def stage2_exploration():
    """Spawns 6 sub-agents to explore 3 approaches based on scope.md."""
    if not os.path.exists("scope.md"):
        print("Error: scope.md not found. Stage 1 must be completed first.")
        sys.exit(1)
        
    with open("scope.md", "r") as f:
        scope_content = f.read()

    os.makedirs("stage2", exist_ok=True)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = []

    approaches = ["Skill/Prompt Orchestration", "Microservices API", "Event-Driven State Graph"]
    
    for i, approach in enumerate(approaches):
        for variant in [1, 2]:
            task_name = f"Approach_{i+1}_Variant_{variant}"
            prompt = (
                f"Read the following scope:\n\n{scope_content}\n\n"
                f"Your task is to write an initial design using the '{approach}' approach. "
                f"Write your output to the file 'stage2/{task_name}.md'.\n"
                f"{DESIGN_RULES}"
            )
            tasks.append(run_subagent(task_name, prompt, sem))

    print(f"Launching {len(tasks)} Stage 2 sub-agents...")
    results = await asyncio.gather(*tasks)
    
    if all(results):
        print("Stage 2 completed successfully. All 6 initial designs generated.")
    else:
        print("Stage 2 encountered errors. Check logs.")
        sys.exit(1)

async def stage3_consolidation():
    """Spawns 3 sub-agents to consolidate the 6 stage 2 designs."""
    if not os.path.exists("stage2") or len(os.listdir("stage2")) < 6:
        print("Error: stage2 folder missing or incomplete. Run stage 2 first.")
        sys.exit(1)

    # Read all stage 2 contents
    stage2_contents = ""
    for filename in os.listdir("stage2"):
        if filename.endswith(".md"):
            with open(os.path.join("stage2", filename), "r") as f:
                stage2_contents += f"\n\n--- Content of {filename} ---\n\n" + f.read()

    os.makedirs("stage3", exist_ok=True)
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = []

    for i in range(1, 4):
        task_name = f"Consolidated_Design_{i}"
        prompt = (
            f"Review the 6 initial design proposals provided below:\n{stage2_contents}\n\n"
            f"Your task is to debate the pros and cons of the 6 proposals and synthesize a new, consolidated design. "
            f"Write your output to the file 'stage3/{task_name}.md'.\n"
            f"{DESIGN_RULES}"
        )
        tasks.append(run_subagent(task_name, prompt, sem))

    print(f"Launching {len(tasks)} Stage 3 sub-agents...")
    results = await asyncio.gather(*tasks)
    
    if all(results):
        print("Stage 3 completed successfully. All 3 consolidated designs generated.")
    else:
        print("Stage 3 encountered errors. Check logs.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Designer Agent Orchestrator")
    parser.add_argument("--stage", type=int, required=True, choices=[2, 3], help="Pipeline stage to run (2 or 3)")
    args = parser.parse_args()

    if args.stage == 2:
        asyncio.run(stage2_exploration())
    elif args.stage == 3:
        asyncio.run(stage3_consolidation())
