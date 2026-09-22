#!/usr/bin/env python3
"""Create, update and publish the generated MCT course repositories.

The canonical source lives in ../template. Generated repositories live as
sibling repositories below ../../ (the shared repos/ directory) and have their
own .git directory.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template"
REPOS_ROOT = ROOT.parent
DEFAULT_BRANCH = "master"
MARKER_RE = re.compile(r"@[A-Z][A-Z0-9_]*@")


@dataclass(frozen=True)
class Course:
    key: str
    repo_name: str
    origin: str
    github: str


COURSES: dict[str, Course] = {
    "I3A": Course(
        key="I3A",
        repo_name="MCT_I3A",
        origin="ssh://meisterk@forgejo.meisterk.de/Microcontrollertechnik/MCT_I3A.git",
        github="git@github.com:BerndDonner/MCT_I3A.git",
    ),
    "E3A": Course(
        key="E3A",
        repo_name="MCT_E3A",
        origin="ssh://meisterk@forgejo.meisterk.de/Microcontrollertechnik/MCT_E3A.git",
        github="git@github.com:BerndDonner/MCT_E3A.git",
    ),
}


def run(*args: str, cwd: Path, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage generated MCT_I3A and MCT_E3A repositories."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("create", "generate a course tree, initialize Git and configure remotes"),
        ("update", "regenerate a clean existing course repo while preserving .git"),
        ("publish", "push master to Forgejo (origin) and GitHub"),
        ("status", "show branch, remotes and working-tree status"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("course", choices=[*COURSES, "all"])

    return parser.parse_args()


def targets(key: str) -> list[Course]:
    if key == "all":
        return [COURSES["I3A"], COURSES["E3A"]]
    return [COURSES[key]]


def destination(course: Course) -> Path:
    return REPOS_ROOT / course.repo_name


def substitute_tree(root: Path, course: Course) -> None:
    values = {
        "@CLASS@": course.key,
        "@REPO_NAME@": course.repo_name,
    }
    unresolved: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for marker, replacement in values.items():
            text = text.replace(marker, replacement)
        path.write_text(text, encoding="utf-8")

        for match in MARKER_RE.finditer(text):
            unresolved.append(f"{path.relative_to(root)}: {match.group(0)}")

    if unresolved:
        details = "\n".join(f"  {item}" for item in unresolved)
        raise RuntimeError(f"unresolved template marker(s):\n{details}")


def render(course: Course, parent: Path) -> Path:
    target = parent / course.repo_name
    shutil.copytree(TEMPLATE, target, copy_function=shutil.copy2)
    substitute_tree(target, course)
    return target


def set_remote(repo: Path, name: str, url: str) -> None:
    remotes = run("git", "remote", cwd=repo, capture=True).splitlines()
    if name in remotes:
        run("git", "remote", "set-url", name, url, cwd=repo)
    else:
        run("git", "remote", "add", name, url, cwd=repo)


def assert_repo(repo: Path) -> None:
    if not (repo / ".git").exists():
        raise RuntimeError(f"not an initialized generated repository: {repo}")


def assert_master(repo: Path) -> None:
    branch = run("git", "branch", "--show-current", cwd=repo, capture=True)
    if branch != DEFAULT_BRANCH:
        raise RuntimeError(
            f"{repo.name}: expected branch '{DEFAULT_BRANCH}', found '{branch or '<detached>'}'"
        )


def assert_clean(repo: Path) -> None:
    status = run("git", "status", "--porcelain", cwd=repo, capture=True)
    if status:
        raise RuntimeError(
            f"{repo.name}: working tree is not clean; commit/stash/remove changes first:\n{status}"
        )


def create(course: Course) -> None:
    repo = destination(course)
    if repo.exists():
        raise RuntimeError(
            f"destination already exists: {repo}\n"
            "Use 'update' for an existing generated repository."
        )

    REPOS_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mct-render-") as tmp:
        rendered = render(course, Path(tmp))
        shutil.move(str(rendered), repo)

    run("git", "init", "-b", DEFAULT_BRANCH, cwd=repo)
    set_remote(repo, "origin", course.origin)
    set_remote(repo, "github", course.github)
    run("git", "add", "-A", cwd=repo)
    run("git", "commit", "-m", f"Initial {course.repo_name} course repository", cwd=repo)

    print(f"Created {course.repo_name}: {repo}")
    print(f"  branch : {DEFAULT_BRANCH}")
    print(f"  origin : {course.origin}")
    print(f"  github : {course.github}")


def remove_worktree_except_git(repo: Path) -> None:
    for child in repo.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def copy_rendered_into_repo(rendered: Path, repo: Path) -> None:
    for child in rendered.iterdir():
        dest = repo / child.name
        if child.is_dir() and not child.is_symlink():
            shutil.copytree(child, dest, copy_function=shutil.copy2)
        else:
            shutil.copy2(child, dest, follow_symlinks=False)


def update(course: Course) -> None:
    repo = destination(course)
    assert_repo(repo)
    assert_master(repo)
    assert_clean(repo)

    # Render completely before touching the real working tree. If rendering
    # fails, the generated repository remains unchanged.
    with tempfile.TemporaryDirectory(prefix="mct-render-") as tmp:
        rendered = render(course, Path(tmp))
        remove_worktree_except_git(repo)
        copy_rendered_into_repo(rendered, repo)

    # Keep the configured topology deterministic even if a remote was edited.
    set_remote(repo, "origin", course.origin)
    set_remote(repo, "github", course.github)

    print(f"Updated working tree for {course.repo_name}; .git was preserved.")
    print("Review with:")
    print(f"  git -C {repo} status")
    print(f"  git -C {repo} diff")


def publish(course: Course) -> None:
    repo = destination(course)
    assert_repo(repo)
    assert_master(repo)
    assert_clean(repo)
    set_remote(repo, "origin", course.origin)
    set_remote(repo, "github", course.github)

    # Forgejo is authoritative: master tracks origin/master. GitHub is a
    # public bootstrap mirror and deliberately does not become the upstream.
    run("git", "push", "-u", "origin", DEFAULT_BRANCH, cwd=repo)
    run("git", "push", "github", DEFAULT_BRANCH, cwd=repo)
    print(f"Published {course.repo_name} master to origin and github.")


def status(course: Course) -> None:
    repo = destination(course)
    assert_repo(repo)
    print(f"== {course.repo_name} ==")
    branch = run("git", "branch", "--show-current", cwd=repo, capture=True)
    print(f"branch: {branch or '<detached>'}")
    print(run("git", "remote", "-v", cwd=repo, capture=True))
    state = run("git", "status", "--short", cwd=repo, capture=True)
    print(state if state else "working tree clean")


def main() -> int:
    args = parse_args()
    actions = {
        "create": create,
        "update": update,
        "publish": publish,
        "status": status,
    }
    action = actions[args.command]

    try:
        for course in targets(args.course):
            action(course)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
