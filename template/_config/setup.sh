#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  ./_config/setup.sh
  ./_config/setup.sh --refresh
  ./_config/setup.sh --student <forgejo-login>

Without --student, mct.student is read from Git configuration (on Bunny this
is generated from rollout.csv). --student writes a repo-local override and is
mainly intended for Windows/non-Bunny machines.
USAGE
}

student_override=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --refresh)
            shift
            ;;
        --student)
            [[ $# -ge 2 ]] || { usage >&2; exit 2; }
            student_override=$2
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

root=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "ERROR: run this script inside the @REPO_NAME@ Git repository." >&2
    exit 1
}
cd "$root"

if [[ -n "$student_override" ]]; then
    if [[ ! "$student_override" =~ ^[A-Za-z0-9._-]+$ ]]; then
        echo "ERROR: invalid Forgejo login '$student_override'." >&2
        exit 1
    fi
    git config --local mct.student "$student_override"
fi

student=$(git config --get mct.student 2>/dev/null || true)
if [[ -z "$student" || "$student" == "UNCONFIGURED" ]]; then
    echo "ERROR: mct.student is not configured." >&2
    echo "       Bunny: regenerate the host config from rollout.csv." >&2
    echo "       Other systems: ./_config/setup.sh --student <forgejo-login>" >&2
    exit 1
fi
if [[ ! "$student" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "ERROR: invalid mct.student '$student'." >&2
    exit 1
fi

# include.path is resolved relative to .git/config. Do not destroy unrelated
# include paths the user may already have.
if ! git config --local --get-all include.path 2>/dev/null | grep -Fxq '../_config/gitconfig'; then
    git config --local --add include.path '../_config/gitconfig'
fi

# Set directly as well, so the hook is active immediately in this clone.
git config --local core.hooksPath _config/hooks

mkdir -p .vscode
cp _config/launch.json .vscode/launch.json

# Continue may create its own default config on first extension start. The MCT
# repository is authoritative for the classroom configuration, so install our
# version as a normal writable user file (not a Nix-store symlink).
install -Dm0644 _config/continue/config.yaml "$HOME/.continue/config.yaml"

if [[ "$student" == "donner" ]]; then
    cp _config/settings.teacher.json .vscode/settings.json
else
    mkdir -p "$student"
    sed "s/__MCT_STUDENT__/$student/g" _config/settings.student.json.in > .vscode/settings.json
fi

cat <<EOF2
@REPO_NAME@ configured:
  mct.student : $student
  hooks       : _config/hooks
  VS Code     : .vscode/settings.json
  Continue    : ~/.continue/config.yaml
EOF2

if [[ "$student" != "donner" ]]; then
    echo "  writable     : $student/** and .git/config (VS Code protection)"
fi
