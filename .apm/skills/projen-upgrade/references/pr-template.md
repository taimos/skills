# PR description template

Title: `chore(deps): upgrade dependencies (<YYYY-MM-DD>)`. No `[major]` or
other prefix; repos lint PR titles against conventional commit types.

Fill every section. Write "none" for empty sections instead of removing them,
so reviewers see that the case was checked.

```markdown
## Summary

<one or two sentences: how many packages upgraded, how many vulnerabilities
fixed, how many remain, whether any major was applied>

## Majors applied

| Package | Workspace package | From | To | Reason |
|---|---|---|---|---|
| <pkg> | <workspace pkg> | <x.y.z> | <x.y.z> | security: <GHSA-id> (high) / requested by user / projen always latest |

## Toolchain

| Item | From | To |
|---|---|---|
| pnpm | | |
| CDK_VERSION (aws-cdk-lib and derived alpha modules) | | |
| CONSTRUCTS_VERSION | | |
| projen | | |
| @taimos/projen | | |

## projen regeneration changes

<generated files changed by the new projen version, one line each, or "none">

## Upgraded dependencies

<table per workspace package, or a collapsed <details> block if long>

| Workspace package | Dependency | From | To |
|---|---|---|---|

## Vulnerabilities

Before: <critical> critical, <high> high, <moderate> moderate, <low> low
After:  <critical> critical, <high> high, <moderate> moderate, <low> low

### Fixed

| Advisory | Severity | Package | Fixed by |
|---|---|---|---|

### Still open

| Advisory | Severity | Package | Path | Reason |
|---|---|---|---|---|
| | | | <parent > child> | no compatible parent update / fix breaks gate / low-moderate needs major |

## Overrides removed

| Override | Floor | Resolved versions without it |
|---|---|---|

## Held back

Newer versions exist but were not applied (major under caret semantics,
tilde range, exact pin, or blocked by the release-age gate).

| Package | Workspace package | Current | Newest | Reason |
|---|---|---|---|---|

## Release-age gate bypasses

| Package@version | Advisory | Severity |
|---|---|---|

## Rolled back

| Package | Attempted version | Error (excerpt) | Fix attempts |
|---|---|---|---|

## Code changes

<source changes made to keep the build green, with the migration note that
required them; CDK snapshot changes with explanation>

## Verification

| Check | Result |
|---|---|
| pnpm install --frozen-lockfile | |
| projen regenerate is stable | |
| pnpm -r run build | |
| pnpm -r run test | |
| lint | |
| expo install --check (<apps>) | |
| cdk synth (<apps>) | |
| pnpm audit | |

<pre-existing failures from the baseline, if any>
```
