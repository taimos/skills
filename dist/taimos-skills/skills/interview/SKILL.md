---
name: interview
description: >-
  Conduct a detailed interview about a specific feature or topic to gather
  information and create a specification.
---

# Interview

$ARGUMENTS

## Core principle: never guess

This skill exists to remove ambiguity by asking, not by assuming. Every design
choice, scope boundary, and behavior must be traced back to an explicit decision
you made. The agent never silently fills a gap.

Two rules govern this:

- **Propose, don't decide.** The agent may propose a recommended default for any
  question, but must label it clearly as unconfirmed (e.g. "proposed default,
  needs your confirmation"). A proposed default is never treated as decided
  until you give an explicit yes or no.
- **Confirmed means confirmed.** An item counts as decided only after you
  explicitly confirm it. Until then it stays on the open list and must never
  appear in the plan.

## Phase 1: Context gathering

Before asking anything, explore the relevant parts of the codebase and docs so
questions are informed and specific, not generic:

- Related existing features, models, and patterns
- Relevant domain concepts from `docs/`
- Existing constraints (auth, data model, conventions) that the feature must fit

Use this context to sharpen questions and to surface conflicts. Do not use it to
answer questions on your own — a plausible codebase pattern is a reason to ask
"should we follow the existing X pattern here?", not a reason to assume yes.

## Phase 2: Interview

Ask questions in chat, in **small batches of 3-5 related questions per round**.
Use whatever question-asking mechanism the host environment provides; if none is
available, ask directly in chat. Where a sensible default exists, include it as a
labeled proposed default so answering is fast, but keep it unconfirmed until the
user responds.

**Approach:**

- Start from first principles — don't assume you understand the goal.
- Challenge assumptions and probe for hidden complexity.
- Ask about conflicts with existing features.
- Explicitly clarify scope: what's in, what's explicitly out for later.
- Explore edge cases, error states, and permissions.
- Drill into vague answers. If a reply is ambiguous, ask a follow-up rather than
  interpreting it.

**Cover these areas** (not necessarily in order):

- Core problem / why this feature
- Users and their goals
- Happy path and variations
- Edge cases and error handling
- Integration with existing features
- Data model implications
- UI/UX flow and states
- Constraints and non-negotiables

**Track decisions as you go.** Maintain two running lists and keep them current
across rounds:

- **Confirmed decisions** — items the user has explicitly confirmed.
- **Open items** — everything still unanswered, plus any proposed defaults
  awaiting a yes/no.

At the end of each round, show the user the open items that remain so progress is
visible.

**Completion gate.** The agent judges when it has enough *coverage* to write a
complete implementation plan. It may decide coverage is reached on its own, but
before finishing Phase 2 it must run a confirmation sweep: present the full list
of proposed defaults and any items still awaiting a yes/no, and only proceed once
**every** one of them is explicitly confirmed. The user still confirms every
individual decision; the agent only judges when the set of questions is complete.
If the user chooses to defer an item ("decide later"), record it as deferred — it
does not block completion but must not be treated as decided.

## Phase 3: Plan

Write a plan including:

- **Summary**: One paragraph.
- **Context**: Background (why, goals, links to related issues or documentation).
- **Scope**: What's included / explicitly excluded.
- **Product requirements**: UI/UX, user stories.
- **Technical plan**: Architecture, data model, implementation details.
- **Confirmed decisions**: A log of the decisions the user confirmed during the
  interview, so each choice in the plan is traceable.
- **TODOs**: Specific tasks to be done.
- **Open questions**: Only items the user explicitly chose to defer. Do not put
  unresolved-but-undeferred questions here — those must be resolved in Phase 2
  before the plan is written.

Only confirmed decisions and explicitly deferred items may appear in the plan.
Nothing that is merely a proposed default or an unanswered question belongs in
it.

The plan must be written in the same language as the user's input (e.g., if the
user asked in French, write the plan in French).
