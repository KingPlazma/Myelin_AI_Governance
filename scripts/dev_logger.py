"""
Developer Change Logger — Myelin AI Governance
===============================================
Run this script to auto-generate a timestamped CHANGELOG entry from your
current git working tree (staged + unstaged changes).

Usage:
    python scripts/dev_logger.py                   # auto-detect changes
    python scripts/dev_logger.py --message "desc"  # add a description
    python scripts/dev_logger.py --build            # generate build log entry

Output files:
    CHANGELOG.md     — human-readable running changelog (appended at top)
    logs/build.jsonl — machine-readable build event log (append-only)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
LOG_DIR = ROOT / "logs"
BUILD_LOG = LOG_DIR / "build.jsonl"


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _run_git(args: list[str]) -> str:
    """Run a git command from the repo root and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() or ""


def get_changed_files() -> dict:
    """Return dict of {status: [files]} for all changed files."""
    raw = _run_git(["status", "--porcelain"])
    files = {"modified": [], "added": [], "deleted": [], "renamed": [], "untracked": []}
    for line in raw.splitlines():
        if not line.strip():
            continue
        code = line[:2].strip()
        fname = line[3:].strip()
        if code in ("M", "MM"):
            files["modified"].append(fname)
        elif code in ("A", "AM"):
            files["added"].append(fname)
        elif code == "D":
            files["deleted"].append(fname)
        elif code.startswith("R"):
            files["renamed"].append(fname)
        elif code == "??":
            files["untracked"].append(fname)
    return files


def get_diff_summary() -> list[str]:
    """Return list of changed function/class names from the diff."""
    diff = _run_git(["diff", "--unified=0", "HEAD"])
    lines = []
    for line in diff.splitlines():
        if line.startswith("@@") and "def " in line or "class " in line:
            lines.append(line.strip())
    return lines[:20]  # cap at 20


def get_last_commit() -> dict:
    """Return metadata of the last commit."""
    return {
        "hash":    _run_git(["log", "-1", "--format=%H"]),
        "short":   _run_git(["log", "-1", "--format=%h"]),
        "author":  _run_git(["log", "-1", "--format=%an <%ae>"]),
        "message": _run_git(["log", "-1", "--format=%s"]),
        "date":    _run_git(["log", "-1", "--format=%ai"]),
    }


def get_branch() -> str:
    return _run_git(["rev-parse", "--abbrev-ref", "HEAD"])


# ---------------------------------------------------------------------------
# CHANGELOG writer
# ---------------------------------------------------------------------------

def _format_file_list(label: str, files: list[str]) -> str:
    if not files:
        return ""
    items = "\n".join(f"  - `{f}`" for f in files)
    return f"**{label}:**\n{items}\n"


def write_changelog_entry(message: str, changed: dict, commit: dict, build: bool = False) -> str:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%d %H:%M UTC")
    branch = get_branch()

    sections = [
        f"## [{ts}] — {branch} · {commit['short']}",
        "",
        f"**Message:** {message or commit['message'] or '(no message)'}",
        f"**Author:** {commit['author']}",
        "",
    ]
    if build:
        sections.append("🏗️ **BUILD EVENT**\n")

    sections.append(_format_file_list("Added",    changed["added"]))
    sections.append(_format_file_list("Modified", changed["modified"]))
    sections.append(_format_file_list("Deleted",  changed["deleted"]))
    sections.append(_format_file_list("Renamed",  changed["renamed"]))
    sections.append(_format_file_list("Untracked (not committed)", changed["untracked"]))

    diff_hints = get_diff_summary()
    if diff_hints:
        sections.append("**Changed functions/classes:**")
        sections.extend(f"  - `{h}`" for h in diff_hints)
        sections.append("")

    sections.append("---\n")
    return "\n".join(s for s in sections if s is not None)


def prepend_to_changelog(entry: str):
    """Insert a new entry at the top of CHANGELOG.md (below the title)."""
    existing = ""
    if CHANGELOG.exists():
        existing = CHANGELOG.read_text(encoding="utf-8")

    # If file doesn't have a title, add one
    if not existing.startswith("# Myelin"):
        header = "# Myelin AI Governance — Developer Changelog\n\n"
        existing = header + existing

    # Insert new entry after the first header line
    lines = existing.split("\n", 2)
    new_content = lines[0] + "\n\n" + entry + ("\n".join(lines[1:]) if len(lines) > 1 else "")
    CHANGELOG.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Build log writer
# ---------------------------------------------------------------------------

def write_build_log(message: str, changed: dict, commit: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "event":         "build",
        "branch":        get_branch(),
        "commit":        commit,
        "message":       message,
        "files_added":   changed["added"],
        "files_modified": changed["modified"],
        "files_deleted": changed["deleted"],
        "files_renamed": changed["renamed"],
    }
    with open(BUILD_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"✅ Build log entry written → {BUILD_LOG}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Myelin Developer Change Logger")
    parser.add_argument("--message", "-m", default="", help="Changelog entry description")
    parser.add_argument("--build",   "-b", action="store_true", help="Mark as a build event")
    args = parser.parse_args()

    print("🔍 Scanning git working tree...")
    changed = get_changed_files()
    commit  = get_last_commit()

    total = sum(len(v) for v in changed.values())
    if total == 0 and not args.build:
        print("ℹ️  No changes detected. Nothing to log.")
        return

    entry = write_changelog_entry(args.message, changed, commit, build=args.build)
    prepend_to_changelog(entry)
    print(f"✅ CHANGELOG.md updated → {CHANGELOG}")

    if args.build:
        write_build_log(args.message, changed, commit)


if __name__ == "__main__":
    main()
