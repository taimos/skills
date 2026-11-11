---
name: projen-upgrade
description: >-
  Upgrade all dependencies of a pnpm repository or pnpm workspace monorepo —
  projen-managed or plain — to their latest COMPATIBLE (semver-safe) versions
  while fixing as many known vulnerabilities as possible, projen-first,
  verifying that projen still synthesizes and the build stays green at each
  stage. Handles projen's upgrade task or its steps, plain pnpm packages, Expo
  apps, pinned CDK / constructs versions, existing pnpm overrides, the pnpm
  version and the pnpm minimum-release-age gate, then delivers the result as one
  commit on a branch with a pull request. Use when asked to "upgrade
  dependencies", "update all dependencies", "bump deps to latest", "upgrade
  projen", "fix vulnerabilities", "fix pnpm audit", "refresh the lockfile", or
  "get everything on the latest compatible versions", even if projen or pnpm is
  not named explicitly. Not for a single hand-picked package bump (do that
  directly).
---

# pnpm / Projen Dependency Upgrade

Bring a pnpm repo — single package or workspace monorepo, projen-managed or not
— to the latest **compatible** dependency versions with the fewest open
vulnerabilities, verify it, and open one PR.

The non-negotiable order is **projen first**: bump projen, confirm it still
synthesizes and builds, and only then upgrade the rest. A newer projen can
change generated files or task/workflow shape, so it must be settled before any
other dependency moves.

The skill can run unattended (CI, Claude.ai sandbox, Kiro, headless Claude
Code). In an unattended run it never asks the user a question — every decision
is covered by the rules below, and anything a rule cannot resolve goes into the
PR report. In an interactive session it leaves the working tree for the user
instead of committing (see Delivery).

## How projen upgrades work (read before acting)

Do not think in terms of `npm update` or hand-editing `package.json`. In a
projen repo:

- **Declared versions live in `.projenrc.*` / `.projen/*.ts`**, and `package.json` / `pnpm-lock.yaml` are **generated**. Never hand-edit generated files to make a lasting change — change the source and re-synthesize with `pnpm exec projen` (or `npx projen`). The one exception is the fallback in Phase 2, which edits `package.json` transiently exactly like projen's own upgrade task does, followed by regeneration.
- Every `NodeProject` ships an **`upgrade` task** (component `UpgradeDependencies`). Running it: runs `npm-check-updates` → installs → runs `npx projen` (re-synth) as one unit.
- The upgrade task's default `target` is **`minor`** and `satisfyPeerDependencies` is **`true`**. So it moves deps to the latest version that is **semver-compatible and peer-compatible** — it will **not** cross a major. That is exactly "latest compatible". A new **major** requires editing the version range in the source and is out of scope unless a rule below allows it (see Majors).
- Defaults differ by project role: `depsUpgrade`/`workflow` are `true` for the **root** project and `false` for **subprojects**. Taimos projects usually set `depsUpgrade: false`, so the `upgrade` task is often missing. Detect what actually exists rather than assume.

## Rules

These rules are the contract. Do not deviate from them.

1. **Compatible means within caret semantics.** A change of the first non-zero
   version component is a major: `1.x` to `2.x`, and also `0.28.x` to `0.29.x`
   and `0.1.x` to `0.2.x`. Upgrade every dependency to the latest version that
   is not a major by this definition. Existing range operators are respected:
   `~57.0.27` stays in `57.0.x`, exact pins stay pinned (see rule 4 for the
   toolchain constants).
   **Exception: `projen` always goes to the latest published version**, across
   0.x minors and real majors alike. The release-age gate (rule 6) and the
   breakage rule (rule 9) still apply.
2. **Majors only in three cases:**
   - `projen` (rule 1 exception),
   - a high or critical vulnerability can only be fixed by a major, or
   - the user explicitly named the package (or "all majors") in the request.
   Every major applied is flagged in the PR with its reason (for projen:
   "projen always latest").
3. **Vulnerability policy:**
   - **High and critical:** always fix (rule 2 allows a major if needed).
   - **Low and moderate:** fix only if a compatible update fixes it and the
     full gate stays green. Otherwise report it.
   - **Transitive vulnerability whose parent has no compatible update that
     pulls the fix:** report only. Never add new `overrides`,
     `pnpm.overrides` or `resolutions` entries.
4. **Pinned toolchain constants** (`CDK_VERSION`, `CONSTRUCTS_VERSION` or
   similar literals in `.projen/*.ts` / `.projenrc.ts`): bump to the latest
   compatible version (rule 1) if the full gate stays green. Packages derived
   from them (for example `@aws-cdk/aws-amplify-alpha@${CDK_VERSION}-alpha.0`)
   must have a matching published version that also passes the release-age gate.
5. **pnpm version:** bump to the latest compatible pnpm (rule 1). Do not touch
   the Node version or GitHub Actions versions.
6. **Minimum-release-age gate:** respect it. Bypass it only for a specific
   version that fixes a high or critical vulnerability, and list each bypass in
   the PR.
7. **Existing overrides:** for each existing override entry, test whether it is
   still needed. Remove it if it is stale and the full gate stays green.
   Otherwise keep it.
8. **Projen owns its files.** In projen-managed packages, never edit generated
   files (`package.json`, `pnpm-workspace.yaml`, `.projen/tasks.json`,
   workflows, `amplify.yml`, `cdk.json`) by hand to make a lasting change.
   Change `.projenrc.ts` / `.projen/*.ts` and regenerate. The only exception is
   the Phase 2 fallback, which edits `package.json` transiently exactly like
   projen's own upgrade task does, followed by regeneration.
9. **Breakage:** if an update breaks the gate, try to fix the source code, at
   most 2 attempts per package. Never loosen tests, lint rules, type checks or
   compiler settings to get green. If still red, roll that package back to its
   previous version and report it.
10. **Delivery:** one branch, one single commit, one PR (unattended runs). In an
    interactive session, leave the working tree for the user to review. Without push or `gh` access, deliver a patch file plus the
    PR description instead.

## Phase 0 — Detect environment, repo shape and clean baseline

**Environment:**

| Signal | Environment | Branch handling |
|---|---|---|
| `GITHUB_ACTIONS=true` or `CI=true` | CI | Use the checkout as given, create the branch there |
| Otherwise, git repo with remote | Any checkout | `git switch -c chore/deps-upgrade-<YYYY-MM-DD>` |
| No push rights or no `gh` auth | Sandbox | Work locally, deliver a patch (Delivery) |

Check push and PR ability early: `git ls-remote --exit-code origin` and
`gh auth status`. Record the result; do not abort on failure.

**Clean working tree.** Confirm `git status` is clean. Upgrades must be isolated
and revertable. In an interactive session, if the tree is dirty, ask before
proceeding.

**Repo shape.** Build an inventory before changing anything:

- **Workspace:** `pnpm-workspace.yaml` present. List packages with `pnpm -r ls --depth -1 --json`.
- **Projen root:** `.projenrc.ts` (or `.js` / `.json`) and `.projen/tasks.json`. A Taimos monorepo root is a `MonorepoProject` from `@taimos/projen`.
- **Projen sub-project:** a package directory with its own `.projen/tasks.json` and `.projen/deps.json`.
- **Upgrade task:** for every projen project, note whether `.projen/tasks.json` contains a task named `upgrade`. A project has none whenever `depsUpgrade: false` — common on subprojects and on Taimos projects.
- **Plain package:** no `.projen/` directory (Next.js, Angular, Expo apps, small libraries).
- **Expo app:** plain package with `expo` in `dependencies`.
- **CDK app:** package contains `cdk.json`. Note its synth task (`synth:silent` if defined, else `synth`).
- **Package manager:** confirm pnpm from `packageManager` and the lockfile. Use `pnpm exec projen` consistently.
- **Toolchain constants:** literals such as `CDK_VERSION` and `CONSTRUCTS_VERSION` in `.projen/*.ts`, and anything interpolated from them.
- **pnpm version source:** in a `MonorepoProject`, the `pnpmWorkspaceVersion` option (default `10.33.0` in `@taimos/projen` 0.1.x) renders `packageManager`, `devEngines.packageManager` and the pnpm version of the build workflow. Elsewhere, the `packageManager` field.
- **Release-age gate:** `minimumReleaseAge` and `minimumReleaseAgeExclude` in `pnpm-workspace.yaml`. In a `MonorepoProject` these come from `workspaceOptions.minimumReleaseAge` / `workspaceOptions.minimumReleaseAgeExclude`.
- **Existing overrides:** `overrides` in `pnpm-workspace.yaml` or `pnpm.overrides` in the root `package.json`. In a `MonorepoProject` they come from `workspaceOptions.overrides`.
- **Scripts:** the root `lint` script (for example `pnpm -r run eslint`), and whether projen sub-projects already run tests inside `build`.

Write the inventory down. It drives every later step.

**Baseline.** Run on the untouched tree and keep the output for the report:

```bash
corepack enable
pnpm install --frozen-lockfile
pnpm audit --json > /tmp/audit-before.json || true
pnpm -r outdated --format json > /tmp/outdated-before.json || true
```

Run the gate (Verification) once. If the baseline is already red, record which
check fails. Later failures in that check count against an upgrade only if they
get worse; mention the pre-existing failure in the PR. Do not upgrade on top of
a broken tree without noting it.

Convert the release-age gate to days for ncu: `cooldown = ceil(minimumReleaseAge / 1440)`
(2880 minutes gives `--cooldown 2`). Use it in every ncu call below so ncu does
not pick versions pnpm then rejects.

> Do not run dev servers or watchers. Use build/test tasks only.

## Phase 1 — Upgrade projen first, in isolation

projen is proven green before anything else moves. For every projen project
whose `.projen/deps.json` lists `projen` (usually only the root), raise it to
the latest version that passes the release-age gate (rule 1 exception):

```bash
(cd <dir> && pnpm dlx npm-check-updates@20 --upgrade --target latest \
   --cooldown <days> --filter projen)
pnpm install
pnpm exec projen
```

If `projenVersion` is pinned in `.projenrc.*`, edit the pin instead and
re-synth. Re-synthesis (`pnpm exec projen`) must exit 0. Inspect `git diff` for
changes to generated files (workflows, tasks, tsconfig, `package.json`);
confirm they look like a projen version bump, not accidental config loss, and
summarise them in the PR. Then **build + test**. If the new projen breaks the
gate, rule 9 applies: fix up to 2 times, else roll back to the previous version.

Run this regeneration with the new projen before Phase 2, so the upgrade steps
and all later checks use the new generator.

## Phase 2 — Upgrade the remaining dependencies (compatible)

Order: toolchain constants, pnpm version, projen packages, plain packages, then
one install.

**pnpm version.** Find the latest compatible pnpm:
`pnpm view pnpm@^<current-major> version --json`, take the highest. In a
`MonorepoProject` set `pnpmWorkspaceVersion` explicitly in `.projen/monorepo.ts`
(it is often unset and falls back to the library default). Otherwise run
`corepack use pnpm@<version>`.

**Toolchain constants.** For each constant, list candidate versions with
`pnpm view <pkg>@^<current-major> time --json` and pick the newest version
older than the release-age gate. For `CDK_VERSION`, also require that every
derived package exists at the matching version (for example
`pnpm view @aws-cdk/aws-amplify-alpha@<version>-alpha.0 version`). Update the
literal once so all sub-projects inherit it.

**Projen-managed packages.** For each projen project (root first, then
sub-projects):

- **If an `upgrade` task exists:** run it (`pnpm exec projen upgrade`, or `(cd <dir> && pnpm exec projen upgrade)`; `pnpm -r run upgrade` when every workspace package defines it). Its ncu target is configured in projen and may be `minor`. After it runs, compare old and new versions and revert any change that is a major under rule 1 (including 0.x minor bumps), unless rule 2 allows it. Never revert the projen bump from Phase 1.
- **If no `upgrade` task exists (fallback):** run the same steps projen's `UpgradeDependencies` would run, with `--target semver`. Do not flip `depsUpgrade` to `true` just to get the task — that is a separate config decision.
  1. From `.projen/deps.json`, collect dependencies **without** a `version` (or `*`), excluding `projen` (handled in Phase 1). These are the ones projen lets change in `package.json`:
     ```bash
     (cd <dir> && pnpm dlx npm-check-updates@20 --upgrade --target semver \
        --cooldown <days> --peer --no-deprecated \
        --dep dev,peer,prod,optional --filter <comma-separated names>)
     ```
  2. Collect **all** dependency names from `.projen/deps.json` (excluding `workspace:*` ones) and update them within their ranges: `pnpm --filter <package-name> update <names...>`.
  3. Run `pnpm exec projen` at the root to regenerate. Projen keeps the new versions for unversioned dependencies and restores the declared specs for constrained ones; the lockfile keeps the newer in-range resolutions. Deps whose range is **pinned in `.projenrc.*`** are overwritten by synth — raise those ranges in the source itself, then re-synth, and diff `package.json` to confirm the bumps stuck.

**Plain packages.** For each non-projen package:

```bash
(cd <package-dir> && pnpm dlx npm-check-updates@20 --upgrade --target semver \
   --cooldown <days> --no-deprecated)
```

Then one `pnpm install` at the workspace root. If install fails because no
version in a range is old enough (strict release-age mode), keep the previous
version for that package and continue.

After all upgrades, **re-synth once more** to be sure the tree is settled
(`pnpm exec projen`, clean exit, no drift), then build + test. Bisect failures
per the breakage rule (Phase 4).

### Strict per-package mode (optional)

The projen `upgrade` task bumps compatible deps as one batch and the build
validates them together — the pragmatic default. Only when the batch build
fails do you bisect per package. If the user explicitly wants one-at-a-time
verification (high-risk repo), upgrade in small groups: edit the source (or use
ncu `--filter` for one package), re-synth, build+test, repeat. State which mode
you are using.

## Phase 3 — Existing overrides

For each override entry (rule 7):

1. Remove the entry (through `workspaceOptions.overrides` in projen repos, also removing it from any comment that lists the entries) and run `pnpm install`.
2. Check the result:
   - `pnpm why <pkg> -r --json`: every resolved version still satisfies the removed floor, and
   - `pnpm audit --json` shows no new advisory for that package.
3. If both hold, the entry is stale: keep it removed. Otherwise restore it.

The final gate must pass with all removals. If it fails because of a removal,
restore that entry and re-run the gate.

## Phase 4 — Vulnerabilities

```bash
pnpm audit --json > /tmp/audit-after-upgrade.json || true
```

For each remaining advisory:

1. Find who pulls it in: `pnpm why <vulnerable-pkg> -r`.
2. Classify the fix path:
   - **Direct dependency, fix within compatible range:** should already be fixed by Phase 2. If not, the release-age gate held it back (see 3 below) or the range is a tilde or exact pin. For a tilde or exact pin, raise it to the fixing version if that is not a major.
   - **Direct dependency, fix only in a major:** apply only for high or critical (rule 2). In projen packages raise the spec in `.projen/*.ts` and regenerate; in plain packages `pnpm dlx npm-check-updates@20 --upgrade --target latest --filter <pkg>`. Flag it.
   - **Transitive, a compatible parent update pulls the fix:** update that parent with the methods of Phase 2. For high or critical, a parent major is allowed under rule 2 if it is the only path.
   - **Transitive, no parent update pulls the fix:** report only (rule 3).
3. **Release-age bypass** (high and critical only): if the fixing version is blocked by the gate, add exactly `package@version` to `minimumReleaseAgeExclude` (supported since pnpm 10.19). In a `MonorepoProject` the option replaces the library defaults, so the list must keep `projen-pipelines`, `cdk-serverless` and `@taimos/projen`. List each bypass in the PR.
4. Low and moderate fixes are kept only if the gate stays green. If a fix breaks the gate and cannot be fixed in 2 attempts, revert it and report the advisory as open.

Explicit majors requested by the user are applied here as well, with the same
methods, and flagged as "requested by user".

## Phase 5 — Fix or roll back

When the gate fails after upgrades (rule 9):

1. Identify the responsible package from the error (stack trace, type error location, changelogs of the upgraded packages). If unclear, bisect by reverting half of the upgraded packages of the failing workspace package.
2. Attempt a source-code fix that follows the package's migration notes, at most 2 attempts per package. For an Expo app whose `expo install --check` fails, `pnpm exec expo install --fix` in that package counts as one attempt.
3. Forbidden fixes: skipping or deleting tests, `@ts-ignore` / `eslint-disable` additions, relaxing `tsconfig` or lint config, lowering coverage thresholds, accepting snapshot changes without understanding the diff. CDK snapshot changes are acceptable only when the diff is explained by the upgrade and are listed in the PR.
4. If still red: revert the package. In projen packages pin the previous version in `.projen/*.ts` for this run or restore the previous lockfile entry; in plain packages restore its previous range. Re-run the gate. Record the package, the attempted fix and the error excerpt.

## Phase 6 — Majors (only when a rule allows)

"Latest compatible" stops before majors; rule 2 is the only gate. When a major
is allowed (projen, a high/critical security fix, or a user request):

1. Do it **deliberately, one library (or one coherent group) at a time.**
2. Edit the version range in the source (`.projenrc.*` / `.projen/*.ts`, e.g. `'aws-cdk-lib@^2'` → `'aws-cdk-lib@^3'`), re-synth, build, test, fix breakage from the changelog per Phase 5.
3. Never batch unrelated majors — a failing build becomes impossible to attribute.
4. Flag every major in the PR with its reason.

## Verification (the gate)

All checks must pass before committing. Run from the workspace root:

```bash
pnpm install --frozen-lockfile
# projen repos: regeneration must be stable
pnpm exec projen && git status --porcelain > /tmp/s1 && pnpm exec projen && git status --porcelain > /tmp/s2 && diff /tmp/s1 /tmp/s2
pnpm -r run build
pnpm -r run test
pnpm run lint                         # root lint script; if none: pnpm -r run lint
# every Expo app:
pnpm --filter <expo-package> exec expo install --check
# every CDK app:
pnpm --filter <cdk-package> run synth:silent   # or "synth"
pnpm audit --json > /tmp/audit-after.json || true
```

Notes:

- `pnpm -r run test` repeats tests in projen sub-projects whose `build` already runs `test` (and their CDK synth tests). It stays in the gate; expect the extra time.
- `cdk synth` may need context or credentials that only exist in the pipeline. If synth fails only for missing credentials or account lookups, record it as "synth not verifiable here", not as an upgrade failure.
- Report what actually ran and its result. Never claim a check passed without running it.

## Delivery

**Unattended runs** produce one single commit containing everything:

```bash
git add -A
git commit -m "chore(deps): upgrade dependencies and fix vulnerabilities"
```

Build the PR body from `references/pr-template.md`. The PR title must pass
semantic PR title linting: `chore(deps): upgrade dependencies (<YYYY-MM-DD>)`.
Do not prefix the title with markers such as `[major]`.

- With push and `gh` access:
  ```bash
  git push -u origin HEAD
  gh pr create --title "chore(deps): upgrade dependencies (<YYYY-MM-DD>)" --body-file /tmp/pr-body.md
  ```
  Add the label `dependencies` if it exists. If any major was applied, add `major-upgrade` if it exists; the "Majors applied" section of the body is the authoritative flag.
- Without push or `gh`: run `git format-patch -1 -o <outdir>` and write the PR body to `<outdir>/PR.md`. Hand both to the user.

In CI the same applies; the workflow provides the token.

**Interactive sessions:** do not auto-commit. Leave the working tree for the
user to review, and summarise: projen old→new version, how many packages moved, vulnerabilities fixed and remaining, any
held-back packages with reasons, and any majors applied with their reason. If
the user then asks to commit, use the same conventional-commit message and no
co-authorship or tool attribution.

## Common pitfalls

- **Editing generated files.** If you find yourself changing `package.json`, a lockfile, or a `.github/workflows/*.yml` by hand for a lasting change, stop — change the source and re-synth instead. The Phase 2 fallback's transient edit (followed by regeneration) is the only exception.
- **Assuming an `upgrade` task exists.** Subprojects default to none, Taimos projects disable it, and some repos use dependabot/renovate. Detect from `.projen/tasks.json` and use the ncu fallback when it is absent.
- **Skipping the projen-first step.** Upgrading everything at once hides whether a break came from projen re-synthesis or from a library, and can churn generated files unpredictably.
- **Chasing majors under the guise of "latest".** The compatible target is minor/patch by design; majors are gated by rule 2.
- **Adding overrides to patch a transitive vuln.** Rule 3 forbids it — report it instead.
- **Upgrading on a red baseline.** Confirm green before you start, or record the pre-existing failure, so you can tell what your upgrade broke.

## Reference material

- `references/pr-template.md`: structure of the PR description and report.
