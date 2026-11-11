# Taimos AI Skills

A collection of public [Agent Skills](https://agentskills.io) by [Taimos GmbH](https://taimos.de): reusable prompt modules that extend AI agents with AWS, CDK and business expertise.

Works with Claude Code, Kiro, Codex, GitHub Copilot, Cursor, OpenCode and any other agent that follows the [Agent Skills spec](https://agentskills.io).

## Available Skills

| Skill | Description |
|-------|-------------|
| [cdk-review](.apm/skills/cdk-review/SKILL.md) | Review AWS CDK projects against proven best practices and generate a structured `REVIEW.md` report with severity-classified findings. |
| [cognito-managed-login-branding](.apm/skills/cognito-managed-login-branding/SKILL.md) | Create, validate and fix Amazon Cognito Managed Login branding assets (logos/favicons), catching the server-enforced rules `CfnManagedLoginBranding` fails on before `cdk deploy`. |
| [interview](.apm/skills/interview/SKILL.md) | Interview the user about a feature or topic without guessing, track confirmed decisions and write an implementation plan. |
| [management-summary](.apm/skills/management-summary/SKILL.md) | Condense a long document, report or transcript into a one-page Management Summary for a board or committee (German and English templates). |
| [projen-upgrade](.apm/skills/projen-upgrade/SKILL.md) | Upgrade the dependencies of a pnpm repo or workspace (projen-managed or plain) to the latest compatible versions, fix vulnerabilities, verify the build and deliver one commit and PR. Detects AWS CDK projects, projen-pipelines and cdk-serverless and handles them when present. |
| [verpflegungsmehraufwand](.apm/skills/verpflegungsmehraufwand/SKILL.md) | Build a German per-diem statement (Verpflegungsmehraufwand, § 9 Abs. 4a EStG) as PDF from calendar entries and hotel bookings. Not tax advice. |

## Installation

### Using APM (recommended)

The repo is an [APM](https://microsoft.github.io/apm) package. APM deploys the skills to every supported harness on your machine (Claude Code, Kiro, Codex, Copilot).

```bash
# All skills, for all projects (user scope)
apm install -g taimos/skills

# A single skill
apm install -g taimos/skills/.apm/skills/cdk-review
```

Or declare them per project in your `apm.yml` and pin a release:

```yaml
dependencies:
  apm:
    - taimos/skills#v1.0.0
    - taimos/skills/.apm/skills/cdk-review#v1.0.0
```

Then run `apm install` and commit `apm.yml` and `apm.lock.yaml`.

### Using the Skills CLI

The [`skills`](https://github.com/vercel-labs/skills) CLI auto-detects your installed agents and sets up skills for all of them:

```bash
# Install all skills
npx skills add taimos/skills

# List available skills
npx skills add taimos/skills --list

# Install a single skill
npx skills add taimos/skills --skill cdk-review
```

### Manual installation

Copy the desired skill folder into your agent's skills directory:

```bash
# Claude Code
mkdir -p .claude/skills
cp -r .apm/skills/cdk-review .claude/skills/

# Or the shared standard directory
mkdir -p .agents/skills
cp -r .apm/skills/cdk-review .agents/skills/
```

## Organization context

Some skills look for an optional skill named `org-context`. If it is installed, they read `org-context/references/<skill-name>.md` before starting and use the values there (company details, defaults, internal conventions, branding) in place of their generic defaults. This keeps the public skills generic while your own setup stays in a private package:

```
org-context/
  SKILL.md                              # description: reference data for other skills, do not invoke directly
  references/
    verpflegungsmehraufwand.md          # traveller, vehicle, who pays hotels, branding
```

Install your private `org-context` package next to these skills, e.g. as an additional APM dependency from a private repo.

## Repo Layout

```
apm.yml                      # APM package manifest
.apm/skills/<name>/
  SKILL.md                   # skill definition, folder name = skill name
  references/                # optional reference material
  scripts/                   # optional helper scripts
skills -> .apm/skills        # symlink for the Skills CLI
```

The `SKILL.md` file contains:

- **Frontmatter** (`---` block): `name` and `description`. The description acts as the routing rule that determines when the agent loads the skill, so be specific.
- **Instructions**: detailed prompts that guide the agent's behavior when the skill is active.

Skills must be self-contained. Do not reference files outside the skill folder; symlink and copy-based install mechanisms break on `../` paths. Use the `org-context` convention above for anything organization-specific.

## Contributing and releases

- Use conventional commits. `fix:` releases a patch, `feat:` a minor version and `BREAKING CHANGE:` a major version. Pull request titles are checked against the same convention.
- Do not edit the version in `apm.yml` by hand.
- `validate.yml` runs on every pull request. It packs the package, installs it into a scratch project, runs `apm audit`, renders the example per-diem PDF and syntax-checks the Cognito driver.
- `release.yml` runs semantic-release on every push to `main`. It bumps `apm.yml`, commits it back, tags `vX.Y.Z` and creates a GitHub release with notes.

## License

MIT, see [LICENSE](LICENSE). Fonts or logos you configure for generated documents are subject to their own licenses.

## About Taimos

[Taimos GmbH](https://taimos.de) specializes in AWS cloud automation, infrastructure and AI consulting, with a focus on CDK, serverless and DevOps practices for small and medium enterprises.
