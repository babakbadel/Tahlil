#!/usr/bin/env python3
"""Publish staged generated outputs with bounded, non-forced push retries.

Only bot output commits may use this helper. During rebase, a newer generated
snapshot wins an overlap; upstream code and unrelated files remain intact.
"""
import os
import subprocess
import sys


def git(*args, check=True):
    return subprocess.run(["git", *args], check=check, text=True, capture_output=True)


def main():
    if os.getenv("GITHUB_REF") != "refs/heads/main":
        print("Output publishing skipped outside main")
        return 0
    allowed = ("reports/", "data/", "artifacts/", "graphify-out/", "memory/")
    changed = git("ls-files", "--modified", "--others", "--exclude-standard", "-z").stdout.split("\0")
    generated = sorted({p for p in changed if p.startswith(allowed) or p == "babimind_openrouter_prompt.txt"})
    if generated:
        git("add", "--", *generated)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        print("No generated output changes")
        return 0
    paths = git("diff", "--cached", "--name-only").stdout.splitlines()
    if any(not p.startswith(allowed) and p != "babimind_openrouter_prompt.txt" for p in paths):
        raise RuntimeError("Refusing to publish non-output files")
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("commit", "-m", sys.argv[1] if len(sys.argv) > 1 else "chore: refresh BabiMind outputs")
    for attempt in range(3):
        git("fetch", "origin", "main")
        result = git("rebase", "-X", "theirs", "origin/main", check=False)
        if result.returncode:
            git("rebase", "--abort", check=False)
            raise RuntimeError("Output rebase failed; outputs are available in workflow artifacts")
        if git("push", "origin", "HEAD:main", check=False).returncode == 0:
            print("Generated outputs published")
            return 0
        print(f"Push raced with another writer; retry {attempt + 1}/3")
    raise RuntimeError("Output publishing failed after three attempts")


if __name__ == "__main__":
    raise SystemExit(main())
