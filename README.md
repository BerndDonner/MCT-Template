# MCT course-repository template

This repository is the **single canonical source** for the MCT classroom
repositories. `MCT_I3A` and `MCT_E3A` are generated from exactly the same
`template/` tree. Class-specific copies of `_config`, hooks, or VS Code settings
are never maintained by hand.

The generated course repositories are independent siblings of this template
repository below the shared `repos/` directory:

```text
repos/
├── MCT-Template/.git/        # template/generator repository
├── MCT_I3A/.git/             # independent course repository
└── MCT_E3A/.git/             # independent course repository
```

This keeps the long-lived course repositories independent from the template.
The template is mainly used to bootstrap a school year; later the class
repositories may intentionally diverge and keep their own histories.

## Fixed Git topology

The default branch is always `master`.

### I3A

```text
origin  = ssh://meisterk@forgejo.meisterk.de/Microcontrollertechnik/MCT_I3A.git
github  = git@github.com:BerndDonner/MCT_I3A.git
```

### E3A

```text
origin  = ssh://meisterk@forgejo.meisterk.de/Microcontrollertechnik/MCT_E3A.git
github  = git@github.com:BerndDonner/MCT_E3A.git
```

Forgejo is the authoritative teaching remote and therefore has the conventional
name `origin`. GitHub is the public bootstrap mirror.

The Forgejo and GitHub repositories themselves are created manually in their
web interfaces. This template does not need API tokens or repository-creation
permissions.

## First creation of the course repositories

After the empty remote repositories exist:

```bash
python3 scripts/course.py create I3A
python3 scripts/course.py create E3A
```

or both in one go:

```bash
python3 scripts/course.py create all
```

`create` performs all local bootstrap work:

1. renders the canonical template,
2. substitutes only explicit template markers,
3. initializes an independent Git repository with branch `master`,
4. configures `origin` and `github`,
5. creates the initial commit.

It deliberately does **not** create remote repositories.

Publish the initial `master` branch with:

```bash
python3 scripts/course.py publish I3A
python3 scripts/course.py publish E3A
```

or:

```bash
python3 scripts/course.py publish all
```

Publishing uses:

```text
git push -u origin master
git push github master
```

Thus `master` tracks `origin/master`; GitHub never becomes the upstream.

## Updating course repositories after a template change

Edit only `template/`, commit the template change, then regenerate a course
working tree:

```bash
python3 scripts/course.py update I3A
python3 scripts/course.py update E3A
```

`update` has intentionally conservative semantics:

- the generated repository must already exist,
- it must be on `master`,
- its working tree must be completely clean,
- `.git/` is never deleted or replaced,
- the complete generated working tree is refreshed from `template/`, including
  deletion of files that no longer exist in the template,
- remotes are normalized back to the fixed URLs above.

After an update, inspect the concrete class-specific result normally:

```bash
cd ../MCT_I3A
git status
git diff
```

Then commit it in the generated repository and publish it:

```bash
git add -A
git commit -m "Update MCT course configuration"
cd ../..
python3 scripts/course.py publish I3A
```

The template repository and each generated repository therefore keep separate,
meaningful histories.

## Status helper

```bash
python3 scripts/course.py status I3A
python3 scripts/course.py status E3A
python3 scripts/course.py status all
```

## Template substitution

Generation substitutes only explicit markers inside `template/`:

```text
@CLASS@      -> I3A / E3A
@REPO_NAME@  -> MCT_I3A / MCT_E3A
```

There is deliberately no global `I3A <-> E3A` text replacement. Any unresolved
`@UPPERCASE_MARKER@` aborts generation before an existing repository is touched.

## Student VM bootstrap

GitHub is only the public source for initial VM provisioning. A student VM can
clone without credentials using the GitHub HTTPS URL, while naming that remote
`github`, then add Forgejo as `origin`:

```bash
git clone -o github https://github.com/BerndDonner/MCT_I3A.git MCT_I3A
cd MCT_I3A
git remote add origin https://forgejo.meisterk.de/Microcontrollertechnik/MCT_I3A.git
git switch -c <forgejo-login> master
bash _config/setup.sh
```

For E3A use `MCT_E3A` analogously.

No Forgejo credentials are required while the VM image is built. The student's
remote branch does not need to exist yet. On first use, the student publishes
it under their own Forgejo identity with `git pub`; that first publish also sets
`origin/<forgejo-login>` as the upstream. Only after that does `git upmaster`
have the remote student branch it intentionally requires.

For the teacher VM (`mct.student=donner`), provisioning keeps `master` checked
out and configures its upstream metadata for Forgejo rather than GitHub:

```bash
git config branch.master.remote origin
git config branch.master.merge refs/heads/master
```

This does not contact Forgejo during image creation; it only records which
remote `master` will use later.

## Repository layout

```text
MCT-Template/
├── README.md
├── scripts/
│   └── course.py
└── template/
    ├── _config/
    │   ├── bin/
    │   ├── hooks/
    │   ├── gitconfig
    │   ├── launch.json
    │   ├── settings.student.json.in
    │   ├── settings.teacher.json
    │   └── setup.sh
    ├── donner/
    ├── .gitignore
    ├── Makefile
    ├── flake.nix
    └── flake.lock
```

`template/_config/setup.sh` installs the repository-local Git configuration,
hooks and VS Code protection. Continue configuration is not part of the course
template and is managed during golden-image finalization in NixOS-Bunny.
