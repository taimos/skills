# Taimos AI Skills

A collection of public [Agent Skills](https://agentskills.io) by [Taimos GmbH](https://taimos.de) — reusable prompt modules that extend AI coding agents with AWS and CDK expertise.

Works with Claude Code, Cursor, Codex, GitHub Copilot, OpenCode, Kiro, and any other agent that follows the [Agent Skills spec](https://agentskills.io).

## Available Skills

| Skill | Description |
|-------|-------------|
| [cdk-review](skills/cdk-review/SKILL.md) | Review AWS CDK projects against proven best practices and generate a structured `REVIEW.md` report with severity-classified findings. |
| [cognito-managed-login-branding](skills/cognito-managed-login-branding/SKILL.md) | Create, validate, and fix Amazon Cognito Managed Login branding assets (logos/favicons), catching the server-enforced rules `CfnManagedLoginBranding` fails on before `cdk deploy`. |

## Installation

### Using the Skills CLI (recommended)

The [`skills`](https://www.npmjs.com/package/skills) CLI auto-detects your installed agents and sets up skills for all of them:

```bash
# Install all skills
npx skills add taimos/skills

# List available skills
npx skills add taimos/skills --list

# Install a single skill
npx skills add taimos/skills --skill cdk-review
```

This works across Claude Code, Cursor, Codex, GitHub Copilot, OpenCode, and others — the CLI symlinks each skill into the agent's expected directory (`.claude/skills/`, `.cursor/skills/`, `.codex/skills/`, etc.).

### Manual installation

Copy the desired skill folder into your agent's skills directory:

```bash
# Claude Code
mkdir -p .claude/skills
cp -r skills/cdk-review .claude/skills/

# Cursor
mkdir -p .cursor/skills
cp -r skills/cdk-review .cursor/skills/

# Or the shared standard directory
mkdir -p .agents/skills
cp -r skills/cdk-review .agents/skills/
```

## Skill Structure

Each skill is a self-contained folder with a `SKILL.md` file:

```
skills/
  <skill-name>/
    SKILL.md          # Skill definition with frontmatter and instructions
    templates/        # Optional supporting files (must stay within the skill folder)
    references/       # Optional reference material
```

The `SKILL.md` file contains:

- **Frontmatter** (`---` block): `name` and `description` — the description acts as the routing rule that determines when the agent loads the skill, so be specific
- **Instructions**: Detailed prompts that guide the agent's behavior when the skill is active

Skills must be self-contained. Do not reference files outside the skill folder — symlink and copy-based install mechanisms break on `../` paths.

## License

MIT

## About Taimos

[Taimos GmbH](https://taimos.de) specializes in AWS cloud automation and infrastructure consulting, with a focus on CDK, serverless, and DevOps practices for small and medium enterprises.
