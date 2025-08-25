#!/usr/bin/env python3
import subprocess, datetime, os, re, pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
PROGRESS = REPO / "PROGRESS.md"

def git(args):
    return subprocess.check_output(["git"]+args, text=True).strip()

def today_section(comments):
    today = datetime.date.today().isoformat()
    lines = []
    lines.append(f"## {today}")
    for c in comments:
        c = c.strip()
        if not c: continue
        # skip merge noise
        if re.match(r"^Merge (pull request|branch)", c, re.I): 
            continue
        # compact long messages -> first line only
        first = c.splitlines()[0]
        lines.append(f"- {first}")
    return "\n".join(lines) + "\n"

def read_recent_commit_messages(limit=50):
    log = git(["log", f"-{limit}", "--pretty=%s"])
    return [l for l in log.split("\n") if l.strip()]

def insert_today_section(section_text):
    if not PROGRESS.exists():
        PROGRESS.write_text("# Foritech Secure System — Progress Log\n\n", encoding="utf-8")
    content = PROGRESS.read_text(encoding="utf-8")
    # insert after title
    if "\n## " in content:
        head, rest = content.split("\n## ", 1)
        new = head.rstrip()+"\n\n"+section_text+"\n## "+rest
    else:
        new = content.rstrip()+"\n\n"+section_text
    PROGRESS.write_text(new, encoding="utf-8")

def main():
    msgs = read_recent_commit_messages()
    # lightweight heuristic: use top 10 since last run (actions commit will be bot-signed; we skip those)
    msgs = [m for m in msgs if "[bot]" not in m][:10]
    if not msgs:
        return
    section = today_section(msgs)
    insert_today_section(section)

if __name__ == "__main__":
    main()
