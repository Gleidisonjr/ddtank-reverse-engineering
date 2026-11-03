#!/usr/bin/env python3
"""
RE Router — watches GitHub issues labeled 're-analyze' and dispatches
isolated agent Workers (Claude Code OR Antigravity/agy) in round-robin.

Architecture: Router-Worker pattern (inspired by dsh-superagent-prototype)
Ref: notes/autonomous-re-agent-architecture.md

Usage:
    python scripts/re-router.py --repo owner/repo-name
    python scripts/re-router.py --repo owner/repo-name --once --dry-run
    python scripts/re-router.py --repo owner/repo-name --agent claude
    python scripts/re-router.py --repo owner/repo-name --agent agy

Env vars:
    GITHUB_TOKEN    — required for GitHub API access
    RE_GITHUB_REPO  — default repo (owner/name), overridden by --repo
"""

import os
import sys
import time
import argparse
import subprocess
import itertools
from pathlib import Path
from datetime import datetime

import httpx

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).parent.parent
TARGETS_DIR = PROJECT_DIR / "targets"
NOTES_DIR   = PROJECT_DIR / "notes"
LOGS_DIR    = Path(__file__).parent / "logs"

# ── Agent pool ───────────────────────────────────────────────────────────────
# Round-robin: Worker 1 → claude, Worker 2 → agy, Worker 3 → claude ...
# Each agent needs to be logged in independently.

AGY_PATH = (
    r"C:\Users\dopamine\AppData\Local\Microsoft\WinGet\Packages"
    r"\Google.AntigravityCLI_Microsoft.Winget.Source_8wekyb3d8bbwe\agy.exe"
)

AGENT_POOL = [
    {
        "name": "claude",
        "cmd": ["claude", "--print", "--dangerously-skip-permissions", "-p"],
        "timeout_flag": None,
        "env_extra": {},
    },
    {
        "name": "agy",
        "cmd": [AGY_PATH, "--print", "--dangerously-skip-permissions",
                "--print-timeout", "600s", "-p"],
        "timeout_flag": None,
        "env_extra": {
            "GHIDRA_INSTALL_DIR": r"C:\Users\dopamine\AppData\Local\ghidra\ghidra_12.1.4_PUBLIC",
            "JAVA_HOME": r"C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot",
        },
    },
]

# ── Labels ───────────────────────────────────────────────────────────────────

LABEL_PENDING     = "re-analyze"
LABEL_IN_PROGRESS = "re-in-progress"
LABEL_DONE        = "re-done"
LABEL_FAILED      = "re-failed"
LABEL_BLOCKED     = "re-blocked"
LABEL_FORCE       = "re-force"

POLL_INTERVAL = 60  # seconds between GitHub polls

# ── Worker prompt ─────────────────────────────────────────────────────────────

WORKER_PROMPT = """\
You are a reverse engineering analyst working in this project.

Target: {target_name}
Issue: #{issue_number}
Timestamp: {timestamp}

Steps:
1. Read targets/{target_name}/README.md for context on this target.
2. Use REA MCP tools to analyze it:
   - binary_overview or inspect_artifact for initial overview
   - list_strings, list_procedures for surface mapping
   - decompile or procedure_pseudo_code on interesting functions
   - inspect_pe_imports / inspect_android_package as appropriate
3. Apply /evidence-driven-debugging methodology for any unclear behavior.
4. Write analysis to notes/{target_name}-{timestamp}-analysis.md
   following the template in .claude/rules/notes.md.
5. Run: git add notes/{target_name}-{timestamp}-analysis.md
6. Run: git commit -m "re: add {target_name} analysis"

Do not skip steps. Write the note before committing.
"""

# ── GitHub API ────────────────────────────────────────────────────────────────

def _gh_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN is not set")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def list_labeled_issues(repo: str, label: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/issues"
    resp = httpx.get(url, headers=_gh_headers(),
                     params={"labels": label, "state": "open", "per_page": 50})
    resp.raise_for_status()
    return resp.json()


def add_label(repo: str, number: int, label: str):
    url = f"https://api.github.com/repos/{repo}/issues/{number}/labels"
    httpx.post(url, headers=_gh_headers(), json={"labels": [label]})


def remove_label(repo: str, number: int, label: str):
    url = f"https://api.github.com/repos/{repo}/issues/{number}/labels/{label}"
    httpx.delete(url, headers=_gh_headers())


def comment(repo: str, number: int, body: str):
    url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    httpx.post(url, headers=_gh_headers(), json={"body": body})


# ── Validation ────────────────────────────────────────────────────────────────

def parse_target(issue_title: str) -> str:
    raw = issue_title.split(":", 1)[-1].strip()
    return raw.lower().replace(" ", "-")


def target_exists(name: str) -> bool:
    return (TARGETS_DIR / name).is_dir()


def already_analyzed(name: str, force: bool) -> bool:
    if force:
        return False
    return bool(list(NOTES_DIR.glob(f"{name}-*-analysis.md")))


# ── Worker dispatch ───────────────────────────────────────────────────────────

def dispatch_worker(
    target: str,
    issue_number: int,
    agent: dict,
) -> subprocess.CompletedProcess:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    prompt = WORKER_PROMPT.format(
        target_name=target,
        issue_number=issue_number,
        timestamp=ts,
    )

    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / f"worker-{target}-{agent['name']}-{ts}.log"

    env = os.environ.copy()
    env.update(agent["env_extra"])

    cmd = agent["cmd"] + [prompt]

    print(f"[router] Dispatching {agent['name']} worker for '{target}' → {log_path.name}")
    with open(log_path, "w", encoding="utf-8") as log:
        result = subprocess.run(
            cmd,
            stdout=log,
            stderr=log,
            cwd=str(PROJECT_DIR),
            env=env,
        )

    return result


def dispatch_with_failover(
    target: str,
    issue_number: int,
    primary: dict,
    pool: list[dict],
) -> tuple[subprocess.CompletedProcess, dict]:
    """Try primary agent; on non-zero exit, retry with remaining pool agents."""
    agents_to_try = [primary] + [a for a in pool if a["name"] != primary["name"]]
    last_result, last_agent = None, primary
    for agent in agents_to_try:
        result = dispatch_worker(target, issue_number, agent)
        if result.returncode == 0:
            return result, agent
        print(f"[router] {agent['name']} failed (exit {result.returncode}), trying next agent…")
        last_result, last_agent = result, agent
    return last_result, last_agent


# ── Issue processing ──────────────────────────────────────────────────────────

def process_issue(issue: dict, repo: str, agent: dict, pool: list[dict], dry_run: bool):
    number = issue["number"]
    title  = issue["title"]
    labels = {lbl["name"] for lbl in issue.get("labels", [])}
    force  = LABEL_FORCE in labels

    target = parse_target(title)
    print(f"[router] Issue #{number}: '{title}' → target='{target}' agent={agent['name']} force={force}")

    if dry_run:
        print(f"[dry-run] Would dispatch {agent['name']} worker for '{target}'")
        return

    if not target_exists(target):
        comment(repo, number,
            f"**Blocked**: `targets/{target}/` not found.\n"
            f"Create the directory with a `README.md` and re-add `{LABEL_PENDING}`.")
        remove_label(repo, number, LABEL_PENDING)
        add_label(repo, number, LABEL_BLOCKED)
        return

    if already_analyzed(target, force):
        comment(repo, number,
            f"**Skipped**: `notes/{target}-*-analysis.md` already exists.\n"
            f"Add `{LABEL_FORCE}` label to force re-analysis.")
        remove_label(repo, number, LABEL_PENDING)
        add_label(repo, number, LABEL_DONE)
        return

    remove_label(repo, number, LABEL_PENDING)
    add_label(repo, number, LABEL_IN_PROGRESS)
    comment(repo, number,
        f"Worker started for `{target}` using **{agent['name']}**.")

    result, used_agent = dispatch_with_failover(target, number, agent, pool)

    remove_label(repo, number, LABEL_IN_PROGRESS)
    if result.returncode == 0:
        add_label(repo, number, LABEL_DONE)
        comment(repo, number,
            f"Analysis complete ({used_agent['name']}). See `notes/{target}-*-analysis.md`.")
    else:
        add_label(repo, number, LABEL_FAILED)
        comment(repo, number,
            f"All agents failed for `{target}` (last: {used_agent['name']}, exit {result.returncode}). "
            f"Check `scripts/logs/` for details.")


def run_local_triage(target_dir: str, agent_name: str, dry_run: bool = False):
    """Executes static triage and triggers a local agent worker without GitHub dependencies."""
    p = Path(target_dir)
    if not p.is_absolute():
        p = PROJECT_DIR / p

    if not p.exists():
        print(f"[router:local] Target directory not found: {p}", file=sys.stderr)
        return

    target_name = p.name
    print(f"[router:local] Initiating local autonomous triage on '{target_name}' using agent '{agent_name}'")
    
    # 1. Discover PE/ELF/Binary artifacts
    binaries = list(p.glob("*.exe")) + list(p.glob("*.dll")) + list(p.glob("*.so")) + list(p.glob("*.apk"))
    print(f"[router:local] Discovered {len(binaries)} binary artifact(s) in {p}")
    for b in binaries:
        size_mb = round(b.stat().st_size / (1024 * 1024), 2)
        print(f"  • {b.name:<25} ({size_mb} MB)")

    # 2. Worker prompt invocation
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = WORKER_PROMPT.format(
        target_name=target_name,
        issue_number="LOCAL-001",
        timestamp=ts,
    )

    if dry_run:
        print("[router:local] [dry-run] Would execute worker with prompt:")
        print(prompt)
        return

    pool = resolve_pool(agent_name)
    agent = pool[0]
    print(f"[router:local] Dispatching to {agent['name']} worker...")
    run_agent_worker(agent, prompt)
    print(f"[router:local] Local triage completed for {target_name}.")


# ── Main loop ─────────────────────────────────────────────────────────────────

def resolve_pool(agent_filter: str | None) -> list[dict]:
    """Return agent pool filtered by name, or full round-robin pool."""
    if agent_filter:
        pool = [a for a in AGENT_POOL if a["name"] == agent_filter]
        if not pool:
            raise ValueError(f"Unknown agent '{agent_filter}'. Choose: {[a['name'] for a in AGENT_POOL]}")
        return pool
    return AGENT_POOL


def main():
    parser = argparse.ArgumentParser(
        description="RE Router — dispatch RE workers across Claude Code and Antigravity (agy)")
    parser.add_argument("--repo",    default=os.environ.get("RE_GITHUB_REPO"),
                        help="GitHub repo as owner/name")
    parser.add_argument("--local",   default=None,
                        help="Run autonomous triage on local target directory (e.g. targets/district-187)")
    parser.add_argument("--agent",   default=None,
                        help="Force a specific agent: claude | agy (default: round-robin)")
    parser.add_argument("--once",    action="store_true",
                        help="Process once then exit (no polling loop)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without calling GitHub or agents")
    args = parser.parse_args()

    if args.local:
        run_local_triage(args.local, args.agent or "claude", args.dry_run)
        return

    if not args.repo:
        print("Error: provide --repo owner/name, set RE_GITHUB_REPO, or use --local <target>", file=sys.stderr)
        sys.exit(1)

    pool = resolve_pool(args.agent)
    agent_cycle = itertools.cycle(pool)

    print(f"[router] Watching {args.repo!r} for issues labeled '{LABEL_PENDING}'")
    print(f"[router] Agent pool: {[a['name'] for a in pool]}  |  once={args.once}  |  dry_run={args.dry_run}")
    print(f"[router] Poll interval: {POLL_INTERVAL}s")

    while True:
        try:
            issues = list_labeled_issues(args.repo, LABEL_PENDING)
            print(f"[router] {len(issues)} issue(s) pending")
            for issue in issues:
                agent = next(agent_cycle)
                process_issue(issue, args.repo, agent, pool, args.dry_run)
        except Exception as exc:
            print(f"[router] Error: {exc}", file=sys.stderr)

        if args.once:
            break

        print(f"[router] Sleeping {POLL_INTERVAL}s…")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
