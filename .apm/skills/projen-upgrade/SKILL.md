---
name: projen-upgrade
description: >-
  Upgrade the dependencies of a pnpm repository or workspace to their latest
  compatible (semver-safe) versions and fix known vulnerabilities, verifying the
  build at each stage. Works for projen-managed and plain pnpm projects. Upgrades
  projen first, then everything else, respects the pnpm minimum-release-age gate
  and existing overrides, and delivers one commit and pull request. Use when asked
  to "upgrade dependencies", "update all dependencies", "bump deps to latest",
  "upgrade projen", "fix vulnerabilities", "fix pnpm audit" or "refresh the
  lockfile". Not for a single hand-picked package bump.
---

# pnpm / projen dependency upgrade

Bring a pnpm repository to the latest compatible dependency versions with the
fewest open vulnerabilities, verify it, and deliver one pull request.

The repository can be a single package or a workspace. It can be managed by
projen or not. Do not assume anything else about it: its language, framework,
layout and script names are found in Phase 0, not taken from this document.

If the repository uses projen, upgrade projen first. Confirm it still
synthesizes and the project still builds before any other dependency moves. A
newer projen can change generated files, tasks and workflows, so settle it
before attributing any later failure to a library.

The skill can run unattended (CI, sandbox, headless agent). In an unattended run
it never asks the user a question. The rules below cover every decision, and
anything they cannot resolve goes into the PR report. In an interactive session
it leaves the working tree for the user instead of committing (see Delivery).

## How projen upgrades work

Skip this section for repositories without projen.

- Declared versions live in the projen source (`.projenrc.*` and any files it
  imports). `package.json`, the lockfile, task definitions and workflows are
  generated. Do not hand-edit generated files for a lasting change. Change the
  source and regenerate with `pnpm exec projen`.
- A projen project can have an `upgrade` task (component `UpgradeDependencies`).
  It runs `npm-check-updates`, installs, and regenerates as one unit. Its
  default target is `minor` and it respects peer dependencies, so it stays
  inside the current major.
- The `upgrade` task is optional. Projects often disable it
  (`depsUpgrade: false`). Check `.projen/tasks.json` for a task named `upgrade`
  instead of assuming it exists.

## Rules

1. **Compatible means within caret semantics.** A change of the first non-zero
   version component is a major: `1.x` to `2.x`, and also `0.28.x` to `0.29.x`
   and `0.1.x` to `0.2.x`. Upgrade each dependency to the latest version that
   is not a major by this definition. Respect existing range operators: `~1.2.3`
   stays in `1.2.x`, exact pins stay pinned.
   **Exception: `projen` goes to the latest published version**, across 0.x
   minors and majors. Rules 6 and 9 still apply.
2. **Majors only in three cases:**
   - `projen` (rule 1 exception),
   - a high or critical vulnerability can only be fixed by a major, or
   - the user named the package (or "all majors") in the request.
   Flag every major in the PR with its reason.
3. **Vulnerability policy:**
   - High and critical: always fix. Rule 2 allows a major if needed.
   - Low and moderate: fix only if a compatible update fixes it and the
     verification gate stays green. Otherwise report it.
   - Transitive vulnerability whose parent has no compatible update that pulls
     in the fix: report only. Never add new `overrides`, `pnpm.overrides` or
     `resolutions` entries.
4. **Version constants in config.** If the repository pins versions as literals
   in its own config (for example a shared version constant that several
   packages are derived from), treat them like dependencies: bump to the latest
   compatible version if the gate stays green. Packages derived from a constant
   must exist at the matching version and pass the release-age gate.
5. **pnpm version:** bump to the latest compatible pnpm (rule 1). Do not touch
   the Node.js version or CI action versions.
6. **Minimum-release-age gate:** respect it. Bypass it only for a specific
   version that fixes a high or critical vulnerability, and list each bypass in
   the PR.
7. **Existing overrides:** test whether each existing override is still needed.
   Remove it if it is stale and the gate stays green. Otherwise keep it.
8. **Generated files stay generated.** In projen-managed packages, never edit
   generated files by hand for a lasting change. Change the projen source and
   regenerate. The only exception is the Phase 2 fallback, which edits
   `package.json` transiently the way projen's own upgrade task does, followed
   by regeneration.
9. **Breakage:** if an update breaks the gate, try to fix the source code, at
   most 2 attempts per package. Never loosen tests, lint rules, type checks or
   compiler settings to get green. If still red, roll that package back to its
   previous version and report it.
10. **Delivery:** one branch, one commit, one PR in unattended runs. In an
    interactive session, leave the working tree for the user to review. Without
    push or `gh` access, deliver a patch file plus the PR description.

## Phase 0: Detect environment, repo shape and clean baseline

**Environment:**

| Signal | Environment | Branch handling |
|---|---|---|
| `GITHUB_ACTIONS=true` or `CI=true` | CI | Use the checkout as given, create the branch there |
| Git repo with a remote | Any checkout | `git switch -c chore/deps-upgrade-<YYYY-MM-DD>` |
| No push rights or no `gh` auth | Sandbox | Work locally, deliver a patch (see Delivery) |

Check push and PR ability early with `git ls-remote --exit-code origin` and
`gh auth status`. Record the result. Do not abort on failure.

If the repository documents its own branch or PR conventions (for example a
`CONTRIBUTING.md`), follow them for naming and targets.

**Clean working tree.** Confirm `git status` is clean. Upgrades must be isolated
and revertable. In an interactive session, ask before proceeding on a dirty
tree.

**Inventory.** Build it from the repository itself before changing anything.
Do not infer any of it from the project type.

- **Packages:** `pnpm-workspace.yaml` present means a workspace. List packages
  with `pnpm -r ls --depth -1 --json`. Otherwise it is a single package.
- **Package manager:** confirm pnpm from `packageManager` and the lockfile. Find
  where the pnpm version is declared (`packageManager`, CI workflow pins, or a
  projen option) and note every place.
- **projen:** `.projenrc.*` and `.projen/tasks.json` at the root or in package
  directories. For each projen project, note whether `.projen/tasks.json`
  contains a task named `upgrade`.
- **Plain packages:** packages without a `.projen/` directory.
- **Scripts:** read the `scripts` of the root and of each package (and the
  projen tasks) to learn what exists for build, test, lint, type checking and
  any other validation. Use these as the verification gate. Do not invent
  commands that the repository does not define.
- **Release-age gate:** `minimumReleaseAge` and `minimumReleaseAgeExclude` in
  `pnpm-workspace.yaml` or `.npmrc`. In projen repos these may be generated;
  find the projen option that renders them.
- **Existing overrides:** `overrides` in `pnpm-workspace.yaml` or
  `pnpm.overrides` in the root `package.json`, and the projen option that
  renders them if generated.
- **Version constants:** literals in the projen source or other config that
  pin versions used by several packages (rule 4).

Write the inventory down. It drives every later step.

**Baseline.** On the untouched tree, run and keep the output for the report:

```bash
corepack enable
pnpm install --frozen-lockfile
pnpm audit --json > /tmp/audit-before.json || true
pnpm -r outdated --format json > /tmp/outdated-before.json || true
```

Run the gate (see Verification) once. If the baseline is already red, record
which check fails. A later failure in that check counts against an upgrade only
if it gets worse. Mention the pre-existing failure in the PR.

Convert the release-age gate to days for ncu: `cooldown = ceil(minimumReleaseAge / 1440)`
(2880 minutes gives `--cooldown 2`). Pass it to every ncu call so ncu does not
pick versions that pnpm then rejects. If no gate is set, omit the flag.

Do not run dev servers or watchers. Use build and test tasks only.

## Phase 1: Upgrade projen first, in isolation

Skip this phase for repositories without projen.

For every projen project whose `.projen/deps.json` lists `projen` (usually only
the root), raise it to the latest version that passes the release-age gate:

```bash
(cd <dir> && pnpm dlx npm-check-updates@latest --upgrade --target latest \
   --cooldown <days> --filter projen)
pnpm install
pnpm exec projen
```

If `projenVersion` is pinned in the projen source, edit the pin and regenerate
instead. Regeneration must exit 0. Inspect `git diff` for changes to generated
files (workflows, tasks, tsconfig, `package.json`). Confirm they look like a
projen version bump and not lost configuration, and summarize them in the PR.
Then run the gate. If the new projen breaks it, rule 9 applies.

Run all later steps with the new projen.

## Phase 2: Upgrade the remaining dependencies

Order: version constants, pnpm version, projen-managed packages, plain
packages, then one install.

**pnpm version.** Find the latest compatible pnpm with
`pnpm view pnpm@^<current-major> version --json` and take the highest. Update
every place found in the inventory. For projen repos, change the projen option
or source that renders the version and regenerate. Elsewhere run
`corepack use pnpm@<version>`. Keep one source of truth: if a CI workflow pins a
pnpm version next to `packageManager`, make them equal or drop the workflow pin.
A mismatch fails the pnpm setup step in CI before any build runs.

**Version constants.** For each constant, list candidate versions with
`pnpm view <pkg>@^<current-major> time --json` and pick the newest version that
is older than the release-age gate. Check that every derived package exists at
the matching version. Update the literal once so all packages inherit it.

**Projen-managed packages.** For each projen project, root first:

- **If an `upgrade` task exists:** run it (`pnpm exec projen upgrade`, run from
  the project directory). Its ncu target may be `minor`. Afterwards compare old
  and new versions and revert every change that is a major under rule 1,
  including 0.x minor bumps, unless rule 2 allows it. Keep the Phase 1 projen
  bump.
- **If no `upgrade` task exists (fallback):** run the steps projen's
  `UpgradeDependencies` would run, with `--target semver`. Do not enable
  `depsUpgrade` just to get the task. That is a separate configuration
  decision.
  1. From `.projen/deps.json`, collect dependencies without a `version` (or
     with `*`), excluding `projen`. Those are the ones projen lets change in
     `package.json`:
     ```bash
     (cd <dir> && pnpm dlx npm-check-updates@latest --upgrade --target semver \
        --cooldown <days> --peer --no-deprecated \
        --dep dev,peer,prod,optional --filter <comma-separated names>)
     ```
  2. Collect all dependency names from `.projen/deps.json` (excluding
     `workspace:*` ones) and update them within their ranges:
     `pnpm --filter <package-name> update <names...>`.
  3. Run `pnpm exec projen` at the root to regenerate. Projen keeps the new
     versions for unversioned dependencies and restores the declared specs for
     constrained ones. Dependencies whose range is pinned in the projen source
     are overwritten by regeneration. Raise those ranges in the source, then
     regenerate, and diff `package.json` to confirm the bumps stuck.

**Plain packages.** For each package without projen:

```bash
(cd <package-dir> && pnpm dlx npm-check-updates@latest --upgrade --target semver \
   --cooldown <days> --no-deprecated)
```

Then run one `pnpm install` at the workspace root. If install fails because no
version in a range is old enough (strict release-age mode), keep the previous
version for that package and continue.

If the inventory shows packages that carry their own version-alignment tooling
(a framework CLI that checks or fixes dependency versions, for example), run
that tool's check as part of the gate and apply its documented fix command as
one attempt under rule 9.

After all upgrades, regenerate once more in projen repos to confirm there is no
drift, then run the gate. Bisect failures as described in Phase 5.

### Strict per-package mode (optional)

The default is to upgrade compatible dependencies as one batch and let the gate
validate them together. Only when the batch fails do you bisect per package. If
the user asks for one-at-a-time verification, upgrade in small groups: edit the
source (or use ncu `--filter` for one package), regenerate, run the gate,
repeat. State which mode you used.

## Phase 3: Existing overrides

For each override entry (rule 7):

1. Remove the entry and run `pnpm install`. In projen repos, remove it through
   the projen option that renders it.
2. Check the result:
   - `pnpm why <pkg> -r --json`: every resolved version still satisfies the
     removed floor, and
   - `pnpm audit --json` shows no new advisory for that package.
3. If both hold, the entry is stale and stays removed. Otherwise restore it.

The final gate must pass with all removals. If it fails because of a removal,
restore that entry and re-run the gate.

## Phase 4: Vulnerabilities

```bash
pnpm audit --json > /tmp/audit-after-upgrade.json || true
```

For each remaining advisory:

1. Find who pulls it in: `pnpm why <vulnerable-pkg> -r`.
2. Classify the fix path:
   - **Direct dependency, fix within the compatible range:** Phase 2 should have
     fixed it. If not, the release-age gate held it back, or the range is a
     tilde or exact pin. For a pin, raise it to the fixing version if that is
     not a major.
   - **Direct dependency, fix only in a major:** apply only for high or
     critical (rule 2). In projen packages raise the spec in the projen source
     and regenerate. In plain packages use
     `pnpm dlx npm-check-updates@latest --upgrade --target latest --filter <pkg>`.
     Flag it.
   - **Transitive, a compatible parent update pulls in the fix:** update that
     parent with the Phase 2 methods. For high or critical, a parent major is
     allowed under rule 2 if it is the only path.
   - **Transitive, no parent update pulls in the fix:** report only (rule 3).
3. **Release-age bypass** (high and critical only): if the gate blocks the
   fixing version, add exactly `package@version` to `minimumReleaseAgeExclude`
   (pnpm 10.19 and later). If the list is generated by projen or replaces a
   default list, keep the existing entries. List each bypass in the PR.
4. Keep low and moderate fixes only if the gate stays green. If a fix breaks the
   gate and cannot be repaired in 2 attempts, revert it and report the advisory
   as open.

Apply explicit user-requested majors here too, with the same methods, and flag
them as "requested by user".

## Phase 5: Fix or roll back

When the gate fails after upgrades (rule 9):

1. Identify the responsible package from the error (stack trace, type error
   location, changelogs). If unclear, bisect by reverting half of the upgraded
   packages of the failing workspace package.
2. Attempt a source fix that follows the package's migration notes, at most 2
   attempts per package.
3. Forbidden fixes: skipping or deleting tests, adding `@ts-ignore` or
   `eslint-disable`, relaxing compiler or lint configuration, lowering coverage
   thresholds, accepting snapshot changes without understanding the diff.
   Snapshot changes are acceptable only when the upgrade explains the diff, and
   they are listed in the PR.
4. If still red, revert the package. In projen packages pin the previous
   version in the projen source for this run, or restore the previous lockfile
   entry. In plain packages restore the previous range. Re-run the gate. Record
   the package, the attempted fix and the error excerpt.

## Phase 6: Majors (only when a rule allows)

"Latest compatible" stops before majors. Rule 2 is the only gate. When a major
is allowed:

1. Upgrade one library, or one coherent group, at a time.
2. Edit the version range in the source (projen source or `package.json`),
   regenerate where needed, run the gate, and fix breakage from the changelog
   per Phase 5.
3. Never batch unrelated majors. A failing build becomes impossible to
   attribute.
4. Flag every major in the PR with its reason.

## Verification (the gate)

All checks must pass before committing. Build the check list from the
inventory: run the install, then every build, test, lint and type-check script
that the repository defines, at the workspace root or per package.

Always include:

```bash
pnpm install --frozen-lockfile
pnpm audit --json > /tmp/audit-after.json || true
```

For projen repositories, also verify that regeneration is stable:

```bash
pnpm exec projen && git status --porcelain > /tmp/s1 \
  && pnpm exec projen && git status --porcelain > /tmp/s2 && diff /tmp/s1 /tmp/s2
```

Notes:

- Some projen sub-projects already run tests inside `build`. Running the tests
  again costs time but stays in the gate.
- A check that needs credentials, network context or services that exist only
  in the pipeline can fail for that reason alone. Record it as "not verifiable
  here", not as an upgrade failure.
- Report what actually ran and its result. Never claim a check passed without
  running it.

## Delivery

**Unattended runs** produce one commit containing everything:

```bash
git add -A
git commit -m "chore(deps): upgrade dependencies and fix vulnerabilities"
```

Build the PR body from `references/pr-template.md`. Use the title
`chore(deps): upgrade dependencies (<YYYY-MM-DD>)`. Do not prefix it with
markers such as `[major]`. If the repository documents a different commit or
title convention, follow that instead.

- With push and `gh` access:
  ```bash
  git push -u origin HEAD
  gh pr create --title "chore(deps): upgrade dependencies (<YYYY-MM-DD>)" --body-file /tmp/pr-body.md
  ```
  Add the label `dependencies` if it exists. If any major was applied, add
  `major-upgrade` if it exists. The "Majors applied" section of the body is the
  authoritative flag.
- Without push or `gh`: run `git format-patch -1 -o <outdir>` and write the PR
  body to `<outdir>/PR.md`. Hand both to the user.

**Interactive sessions:** do not auto-commit. Leave the working tree for the
user to review and summarize the result: projen old and new version (if
applicable), how many packages moved, vulnerabilities fixed and remaining,
held-back packages with reasons, and majors applied with their reason. If the
user then asks to commit, use the same commit message.

## Common pitfalls

- **Editing generated files.** If you change `package.json`, a lockfile or a
  workflow by hand in a projen repository, stop. Change the source and
  regenerate. The Phase 2 fallback is the only exception.
- **Assuming an `upgrade` task exists.** Detect it from `.projen/tasks.json` and
  use the ncu fallback when it is missing.
- **Skipping the projen-first step.** Upgrading everything at once hides whether
  a break came from regeneration or from a library.
- **Chasing majors under the guise of "latest".** The compatible target is minor
  and patch by design. Rule 2 gates majors.
- **Adding overrides to patch a transitive vulnerability.** Rule 3 forbids it.
  Report it instead.
- **Upgrading on a red baseline.** Confirm green first or record the failure, so
  you can tell what the upgrade broke.
- **Two sources for the pnpm version.** A `packageManager` field and a CI
  workflow pin that disagree fail the pnpm setup step in CI, which a local build
  does not show. Wait for the CI checks on the PR and fix red ones.

## Reference material

- `references/pr-template.md`: structure of the PR description and report.
