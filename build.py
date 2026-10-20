#!/usr/bin/env python3
"""
build.py - one source, thirteen skills, three packages.

Every skill folder carries its own copy of the shared files (voice, context,
rules, tools), because a skill uploaded on its own to claude.ai only sees its
own folder. The copies are generated: edit shared/ and the SKILL.md files,
never skills/*/<shared file>, then run this.

  python3 build.py           copy shared/ into every skill, check, package
  python3 build.py --check   only check: copies in sync, frontmatter, JSON, Python
                             (exit 1 on any problem, nothing is written)

Packages, in dist/ (not committed):
  instagram-agent-he.plugin     upload in claude.ai (a zip of the plugin root)
  instagram-agent-he.zip        unzip, then /plugin marketplace add in Claude Code
  claude-ai-skills/ig-*.zip     one skill per zip, for Customize > Skills
"""

import argparse
import filecmp
import json
import os
import py_compile
import re
import shutil
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(ROOT, "shared")
SKILLS = os.path.join(ROOT, "skills")
DIST = os.path.join(ROOT, "dist")
NAME = "instagram-agent-he"
# What a user installs. shared/, tests/, build.py and dist/ stay behind.
PACKAGE = [".claude-plugin", "skills", "README.md", "LICENSE"]


def skill_dirs():
    return sorted(d for d in os.listdir(SKILLS)
                  if d.startswith("ig-") and os.path.isdir(os.path.join(SKILLS, d)))


def shared_files():
    return sorted(f for f in os.listdir(SHARED)
                  if os.path.isfile(os.path.join(SHARED, f)) and not f.startswith("."))


def sync():
    n = 0
    for d in skill_dirs():
        for f in shared_files():
            dst = os.path.join(SKILLS, d, f)
            if not os.path.exists(dst) or not filecmp.cmp(os.path.join(SHARED, f), dst, shallow=False):
                shutil.copy2(os.path.join(SHARED, f), dst)
                n += 1
    return n


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fields, key = {}, None
    for line in m.group(1).splitlines():
        top = re.match(r"([a-z_-]+):\s*(.*)$", line)
        if top:
            key = top.group(1)
            fields[key] = top.group(2).strip()
        elif key and line.startswith(" "):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def check():
    problems = []
    for d in skill_dirs():
        for f in shared_files():
            dst = os.path.join(SKILLS, d, f)
            if not os.path.exists(dst):
                problems.append(f"{d}/{f}: missing (run python3 build.py)")
            elif not filecmp.cmp(os.path.join(SHARED, f), dst, shallow=False):
                problems.append(f"{d}/{f}: differs from shared/{f}. Edit shared/, then build")
        fm = frontmatter(os.path.join(SKILLS, d, "SKILL.md"))
        if fm is None:
            problems.append(f"{d}/SKILL.md: no frontmatter")
            continue
        if fm.get("name") != d:
            problems.append(f"{d}/SKILL.md: name is {fm.get('name')!r}, folder is {d!r}")
        desc = fm.get("description", "").strip(">|- ")
        if not desc:
            problems.append(f"{d}/SKILL.md: empty description")
        elif len(desc) > 1024:
            problems.append(f"{d}/SKILL.md: description is {len(desc)} characters, over 1024")
    for base, _, files in os.walk(ROOT):
        if any(part in base for part in (os.sep + ".git", os.sep + "dist")):
            continue
        for f in files:
            p = os.path.join(base, f)
            rel = os.path.relpath(p, ROOT)
            if f.endswith(".json"):
                try:
                    json.load(open(p, encoding="utf-8"))
                except ValueError as e:
                    problems.append(f"{rel}: invalid JSON ({e})")
            elif f.endswith(".py"):
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        py_compile.compile(p, cfile=os.path.join(tmp, "x.pyc"), doraise=True)
                except py_compile.PyCompileError as e:
                    problems.append(f"{rel}: does not compile ({e.msg.strip()})")
    plugin = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8"))
    if plugin.get("name") != NAME:
        problems.append(f"plugin.json: name is {plugin.get('name')!r}, expected {NAME!r}")
    return problems


def _add_tree(zf, src, arc):
    if os.path.isfile(src):
        zf.write(src, arc)
        return
    for base, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc") or f == ".DS_Store":
                continue
            p = os.path.join(base, f)
            zf.write(p, os.path.join(arc, os.path.relpath(p, src)))


def package():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "claude-ai-skills"))
    made = []
    for path, prefix in ((os.path.join(DIST, NAME + ".plugin"), ""),
                         (os.path.join(DIST, NAME + ".zip"), NAME)):
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in PACKAGE:
                _add_tree(zf, os.path.join(ROOT, item), os.path.join(prefix, item))
        made.append(path)
    for d in skill_dirs():
        path = os.path.join(DIST, "claude-ai-skills", d + ".zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            _add_tree(zf, os.path.join(SKILLS, d), d)
        made.append(path)
    return made


def main():
    ap = argparse.ArgumentParser(description="Sync shared/ into every skill, check, package.")
    ap.add_argument("--check", action="store_true", help="check only, write nothing")
    args = ap.parse_args()

    if not args.check:
        n = sync()
        print(f"synced shared/ into {len(skill_dirs())} skills ({n} files updated)")
    problems = check()
    for p in problems:
        print("  PROBLEM", p)
    if problems:
        print(f"{len(problems)} problem(s). Nothing packaged.")
        sys.exit(1)
    print(f"check: {len(skill_dirs())} skills x {len(shared_files())} shared files in sync, "
          "frontmatter, JSON and Python OK")
    if args.check:
        return
    made = package()
    print(f"packaged {len(made)} files in dist/:")
    for p in made[:2]:
        print("  " + os.path.relpath(p, ROOT))
    print(f"  claude-ai-skills/ ({len(made) - 2} skills)")


if __name__ == "__main__":
    main()
