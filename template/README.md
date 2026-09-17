# @REPO_NAME@ — Microcontrollertechnik

Course/class: `@CLASS@`

This is the clean course repository for the MCT classroom workflow.

The repository starts intentionally without lesson content. `donner/` contains
only `.gitkeep` so that the teacher namespace exists in Git from the first
commit. Student folders do **not** exist in `master`; they are created locally
when a student clone is bootstrapped.

## Invariant

For a student with Forgejo login `huber`:

- `mct.student = huber`
- branch = `huber`
- writable/committable course folder = `huber/`
- upstream = `origin/huber`

The human Git identity is independent of this technical key, for example:

- `user.name = Anton Huber`
- `user.email = ...`
- `mct.student = huber`

For the teacher:

- `mct.student = donner`
- normal teaching work happens on `master`
- the pre-commit path restriction is intentionally bypassed so repairs and
  repository maintenance remain possible.

## One-time setup per clone

On Bunny, `mct.student` is generated from the `forgejo` column in the Bunny
rollout configuration. Run:

```bash
bash _config/setup.sh
```

On Windows or another machine without that Nix configuration:

```bash
bash _config/setup.sh --student huber
```

The setup script:

1. adds `_config/gitconfig` to the repository-local Git configuration,
2. activates `_config/hooks/pre-commit`,
3. creates the local `.vscode/` configuration,
4. installs `_config/continue/config.yaml` to `~/.continue/config.yaml`,
5. creates the student's local (initially untracked) work folder.

The Continue file in `_config/continue/` is the versioned source of truth for
the MCT environment. `setup.sh` copies it to the user's home as a normal
writable file. It intentionally replaces a Continue-generated default config.

`.vscode/` is intentionally ignored because the writable path is different for
each student.

## VS Code protection

For students, VS Code marks the complete repository read-only except:

```text
<student>/
<student>/**
.git/config
```

`.git/` remains visible in the Explorer on purpose.

This is an ergonomics/safety layer against accidental edits, not a security
boundary. Git itself can still update `donner/`, root files and configuration
files during `git upmaster`.

The prominent VS Code Sync/Publish action buttons are disabled. Commit remains
available. A normal Push can still be run from the Git UI after committing.

## Pre-commit protection

The versioned pre-commit hook rejects a student commit when:

- the current branch is not exactly `mct.student`, or
- any staged path is outside `<mct.student>/`.

The path scan disables rename detection, so moving a protected file into the
student folder is seen as a forbidden deletion plus an allowed addition.

`git add -A` is therefore fine: the hook validates the staged result at commit
time.

## Beginning of a lesson: `git upmaster`

Students run:

```bash
git upmaster
```

`upmaster` deliberately requires a clean worktree and does **not** autostash.
It then:

1. verifies `mct.student`, branch and upstream,
2. fetches `origin --prune`,
3. validates that student-only commits change only `<student>/**`,
4. rebases local work onto `origin/<student>` (two-machine case),
5. rebases the result onto `origin/master`,
6. validates the resulting student history again,
7. publishes with `git push --force-with-lease`,
8. refreshes the local VS Code protection.

If a conflict occurs, the generic recovery commands supplied by NixOS-Bunny
(`git current`, `git incoming`, `git abort-op`, `git reset-to-remote`, etc.) are
used by the teacher.

For a badly polluted student branch, the project also provides:

```bash
git repair-student [forgejo-login]
```

It aborts an in-progress operation, preserves the current student directory,
creates a local `rescue/...` branch, rebuilds the student branch on the current
`origin/master`, restores only the student's directory and republishes with
`--force-with-lease`. The interactive confirmation can be skipped deliberately
with `--yes` when speed matters in class.

## End of a lesson

The normal workflow is deliberately simple:

```bash
git add -A
git commit -m "Commit message"
git push
```

The VS Code Stage/Commit/Push UI can be used instead.

## Student branch bootstrap

The VM image is provisioned from the public GitHub mirror. The clone names that
remote `github`; Forgejo is then added as `origin`. No Forgejo credentials are
needed while the image is built.

The student's local branch is created directly from the common `master`
starting point:

```bash
git switch -c huber master
```

`bash _config/setup.sh` then creates the local empty `huber/` directory. Git
does not track empty directories, so there is no special "first student
commit". The first real file under `huber/` is checked by exactly the same
pre-commit rule as every later commit.

The remote branch `origin/huber` deliberately does **not** exist yet. The
student publishes it under their own Forgejo identity on first use with:

```bash
git pub
```

That first publish creates `origin/huber` and sets it as the upstream. Until
then, `git upmaster` is intentionally unavailable because it requires the
student's remote branch.

## Repository layout

```text
@REPO_NAME@/
├── _config/
│   ├── bin/
│   │   ├── check-student-history
│   │   ├── repair-student
│   │   └── upmaster
│   ├── hooks/
│   │   └── pre-commit
│   ├── gitconfig
│   ├── setup.sh
│   ├── settings.student.json.in
│   ├── settings.teacher.json
│   ├── launch.json
│   └── continue/config.yaml
├── donner/
│   └── .gitkeep
├── .gitignore
├── Makefile
├── arduino-cli.yaml
├── flake.nix
└── flake.lock
```

The previous Forgejo path-check Action is intentionally not present. Accidental
edits are stopped before the push by VS Code and the pre-commit hook. Server-side
protection of `master` will be configured by the later Forgejo bootstrap.
