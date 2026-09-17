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

Student branches are created before first use and initially point to the same
commit as `master`. For example:

```bash
git push origin master:refs/heads/huber
```

After cloning/checking out `huber`, `bash _config/setup.sh` creates the local empty
`huber/` directory. Git does not track empty directories, so there is no
special "first student commit". The first real file under `huber/` is checked
by exactly the same pre-commit rule as every later commit.

Branch creation and Forgejo `master` protection are intended to become part of
the later class-bootstrap automation; they are not hard-coded into this clean
base repository.

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
│   └── config.yaml
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
