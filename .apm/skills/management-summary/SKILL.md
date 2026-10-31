---
name: management-summary
description: >-
  Write a one-page Management Summary for a board, committee or internal
  decision-making body. Use this skill whenever the user asks for a "Management
  Summary", "Managementzusammenfassung", "Kurzfassung", "Executive Summary",
  "Zusammenfassung für den Vorstand/Beirat/die Fraktion/das Gremium",
  "Beschlussvorlage", "one-pager for management", or wants a long document,
  options paper, report, study, meeting transcript or analysis condensed for
  decision-makers. Also use it when the user says "fasse das für das Gremium
  zusammen", "mach daraus eine Vorlage", or asks to shorten something so a
  non-technical decision-maker can act on it — even if the words "management
  summary" are never spoken.
---

# Management Summary

Condense a source document into a one-page summary that a committee can act on
without reading the original. The reader is typically an internal body —
Vorstand, Beirat, Gemeinderatsfraktion, Mitgliederversammlung, internal team —
not a customer. That means no sales gloss, no adjectives without numbers, and an
explicit statement of what the body is being asked to do.

Templates: `references/vorlage-de.md` (German), `references/template-en.md`
(English).

## Workflow

### 1. Locate the source and confirm the language

Identify what is being summarised: an attached file, a document earlier in the
conversation, a Notion page, a meeting transcript, a report. If nothing is
identifiable, ask for it — never write a summary from thin air.

Ask which output language is wanted (German or English) unless the user already
said. Ask this in the same turn as any other clarification, not as a separate
round-trip.

### 2. Pick the variant

Two variants exist, because the two purposes need different shapes:

- **Entscheidungsvariante / Decision** — the body has to decide something. Signals: two or more alternatives in the source, an open question of money, resources or direction, a pending approval, a recommendation, an options paper, an ADR still in *Proposed*, a quote, a budget request, phrasing like "wir müssen entscheiden".
- **Überblicksvariante / Overview** — the body only has to take note. Signals: status report, minutes, financial report, study, analysis, completed project, workshop result, with no open question.

Tie-breakers: if both apply, use Decision — a committee's scarce attention
should go to the vote, and the results fold into *Sachverhalt*. If the source
contains options but the decision has already been taken, use Overview and state
the decision as fact.

State the chosen variant in one line before writing, so it can be overridden
cheaply.

### 3. Extract, don't paraphrase everything

Pull out only what a decision-maker needs: the trigger, the numbers, the
options, the money, the risks, the deadline. Everything else stays in the source
document.

For every number, carry its unit and its time basis — "600.000 Events an einem
Wochenende" not "sehr viele Events". If a number, date, owner or cost is missing
from the source, write `[offen: …]` rather than inventing or smoothing over it.
A visible gap is useful to the reader; a plausible-sounding guess is not.

### 4. Write to the template

Follow the template for the chosen variant and language exactly, including
section order. Section order is the point: a committee reads top-down and stops
when it has what it needs.

### 5. Self-check before returning

- Does the first sentence carry the core message, so someone who reads only that sentence is not misled?
- Does it fit on one page? Decision: 250–400 words. Overview: 350–500 words.
- Is every claim traceable to the source?
- Decision variant: is there exactly one recommendation, and is the Beschlussvorschlag phrased so it can be voted on verbatim?
- Are the financial implications stated — including an explicit "keine" if there are none?
- Would a reader with no technical background understand every sentence?

Then note in one line, below the summary, which details were deliberately left
out, so the user knows what the attachment still has to carry.

## Output location

- **Claude.ai / desktop**: create as an artifact.
- **Claude Code / Kiro / computer use**: save as `management-summary-[thema-in-kebab-case].md` next to the source document, or to a path the user names.

## Anti-patterns

These are the failure modes that make a summary useless to a committee:

- **Warming up.** Do not open with background, history or "im Rahmen des Projekts". Open with the point.
- **Unmeasured adjectives.** "Erheblich", "massiv", "deutlich", "signifikant" are empty unless a number follows.
- **Untranslated jargon.** mTLS, Firehose, IdP, Kill-Switch mean nothing to a Verein board. Either add a short plain-language clause or drop the term — if it doesn't change the decision, it doesn't belong.
- **Strawman options.** Three options where two exist only to make the third look good wastes the body's trust. If the status quo is a real option, name it honestly as the Nullvariante and say what it costs.
- **Hedging.** "Beide Optionen haben Vorzüge" is not a recommendation. Name one option. Disagreement belongs in *Risiken*.
- **Overflow.** If it doesn't fit on a page, the surplus is detail, and detail belongs in the attachment.
- **Silent gaps.** Filling a template slot with an invented figure to make the document look complete is the worst outcome here, because the committee may vote on it.
