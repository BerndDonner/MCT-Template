# MCT course-repository template

This repository is the **single canonical source** for the MCT classroom
repositories. `MCT_I3A` and `MCT_E3A` are generated from the same template; do
not maintain class-specific copies of `_config`, hooks, VS Code settings or the
Continue configuration by hand.

## Generate a course repository

From the template repository root:

```bash
python3 scripts/make-course-repo.py I3A
python3 scripts/make-course-repo.py E3A
```

The generated working trees are written to:

```text
dist/MCT_I3A/
dist/MCT_E3A/
```

Generation is deterministic and only substitutes explicit placeholders inside
`template/`:

```text
@CLASS@      -> I3A / E3A
@REPO_NAME@  -> MCT_I3A / MCT_E3A
```

The generator deliberately does **not** run `git init`, create Forgejo
repositories, add remotes or push. Those are separate bootstrap steps and can
later be automated safely.

Use `--force` to replace an already generated working tree:

```bash
python3 scripts/make-course-repo.py I3A --force
```

Use `--output-dir` if the generated repository should be written elsewhere:

```bash
python3 scripts/make-course-repo.py I3A --output-dir /tmp/mct-courses
```

## Repository layout

```text
MCT-Template/
├── README.md
├── scripts/
│   └── make-course-repo.py
└── template/
    ├── _config/
    │   ├── bin/
    │   ├── hooks/
    │   ├── continue/config.yaml
    │   ├── gitconfig
    │   ├── launch.json
    │   ├── settings.student.json.in
    │   ├── settings.teacher.json
    │   └── setup.sh
    ├── donner/
    ├── .gitignore
    ├── Makefile
    ├── arduino-cli.yaml
    ├── flake.nix
    └── flake.lock
```

`template/_config/setup.sh` installs the repository-local Git configuration,
hooks and VS Code protection. It also copies the versioned Continue template to
`~/.continue/config.yaml` as a normal writable file; the active Continue file
is therefore **not** a symlink into the Nix store.
