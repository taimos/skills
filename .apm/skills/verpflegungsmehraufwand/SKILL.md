---
name: verpflegungsmehraufwand
description: >-
  Create a PDF "Reisekostenabrechnung: Verpflegungsmehraufwand" (German
  per-diem / meal allowance statement) for a business trip. Pulls the trip
  from the calendar, hotel confirmations and invoices from the mailbox (HRS,
  booking.com, hotel invoices), applies the German domestic per-diem rules
  (§ 9 Abs. 4a EStG) including meal deductions, and renders a PDF. Use
  whenever the user asks for "Verpflegungsmehraufwand", "Spesen",
  "Reisekosten", "Verpflegungspauschale", "Tagegeld", "per diem",
  "Spesenabrechnung" or a travel expense statement for a trip, conference,
  workshop or client visit, even if they only name the event ("mach mir die
  Spesen für die Konferenz in Hamburg").
---

# Verpflegungsmehraufwand

Produce a per-diem statement as a PDF. The workflow is: load the traveller
profile, find the trip, find the hotels, settle the few facts that change the
math, fill a JSON file, render it with the bundled script, check the PDF.
Never upload or send the result anywhere (cloud drive, accounting tool, mail)
unless the user asks for it.

This skill applies the German tax rules as commonly used for employees and
managing directors. It is not tax advice. Point the user to their tax advisor
for edge cases (foreign trips with several countries, first place of work
questions, trips longer than three months at the same place).

## 0. Traveller profile and organization context

If a skill named `org-context` is installed, read its
`references/verpflegungsmehraufwand.md` before starting. Values there (name,
role, home address, vehicle, who pays hotels, branding, output folder) take
precedence over the defaults in this file.

Without such a file, ask once for the facts the PDF needs and that cannot be
derived from calendar or mail:

- Traveller name, role and home address (start and end point of the trip)
- Vehicle: company car, private car (Kilometerpauschale) or public transport
- Who pays hotels: the company directly (listed "nachrichtlich") or the
  traveller (part of the payout)
- Optional branding: company footer line, logo PNG, colours, TTF fonts

## 1. Find the trip

Use the calendar tool available in this environment (e.g. Google Calendar
`list_events`, Outlook) over the window the user names (a month, an event, a
date range). Search for the event or client name first, then sweep the whole
window without a filter to catch travel blocks.

What to extract per day:

- Departure from home and return time. Entries such as "Fahrt X → Y" often
  carry times, route and km.
- Business purpose per stop (conference, client workshop, partner meeting).
- Meals on the schedule (dinners, catered events). They matter for the
  deduction discussion, not automatically for the math.
- All-day "Stay at ..." entries or imported booking entries point to hotels.

Ignore focus blocks, habits and recurring remote calls.

## 2. Find the hotels

Search the mailbox, e.g.
`(HRS OR Hotelreservierung OR Buchungsbestätigung OR booking.com OR <hotelname>) after:<start-60d>`.
Prefer, in this order: the hotel invoice or HRS "Leistungsnachweis" (actual
amounts), then the booking confirmation. Read the full thread. Capture: hotel
name and address, nights, gross amount incl. city tax, whether breakfast is
included (and its price), who pays (billing address, company card), booking
numbers. Check for cancellations and changes (shortened stays, unused nights)
and mention them as a note under the hotel table.

## 3. Settle the facts that change the result

Apply the traveller profile from step 0. If the trip data contradicts it
(train tickets although the profile says company car, a company-paid dinner,
a private hotel payment) or something is unclear, ask the user. Keep
questions out of the document itself. State the defaults you applied in the
chat reply so the user can correct them.

## 4. Apply the rules

Domestic rates 2026 (verify with a quick web search if the year changes):

| Day | Amount |
|---|---|
| Arrival / departure day of a trip with overnight stay | 14,00 € |
| Full calendar day away (24 h) | 28,00 € |
| One-day trip, more than 8 h away | 14,00 € |
| One-day trip, up to 8 h | 0,00 € |

Meal deductions are always computed from the full-day rate: breakfast 20 %
(5,60 €), lunch or dinner 40 % (11,20 €) each. A day can not go below 0 €.

Deduct only meals provided by the employer or at the employer's instigation,
typically breakfast inside a hotel rate booked and paid by the company. Meals
from event organisers, partners or clients without the employer's
instigation do not reduce the per diem (§ 9 Abs. 4a Satz 8 EStG). Write one
short "Begründung" line per relevant case.

Foreign trips need the BMF country rates for the year; look them up and put
them into the JSON `rates` block (`full`, `partial`) and adjust `legal_basis`.

The script computes all amounts from the `days` list, so never type totals by
hand.

## 5. Build the JSON and render

Copy `references/example-trip.json` as a template. Fields:

- `title`, `created` (today, ISO), `traveller` (`name`, `role`, `address`),
  `period.start/end`, `purposes` (list), `vehicle`
- `itinerary`: `date`, `time`, `place`, `activity` per day
- `days`: `date`, `type` (`arrival`, `full`, `departure`, `single`, `short`),
  optional `breakfast` / `lunch` / `dinner` booleans for provided meals
- `deduction_notes`: list of short strings (inline `<b>` allowed)
- `hotels_heading`, `hotels` (name, period, nights, amount, breakfast,
  receipt as strings), `hotel_notes`
- `travel_costs_note`
- optional: `rates`, `legal_basis`, `extra_payouts` (`label`, `amount`) with
  `payout_total`
- optional `branding`:
  - `footer`: footer line, e.g. company name and address
  - `logo`: `{"path": "logo.png", "width_mm": 36}`
  - `colors`: hex values for `primary`, `secondary`, `accent`, `muted`,
    `text`, `light`
  - `fonts`: TTF paths for `heading_bold`, `heading_semibold`, `body`,
    `body_semibold`, `body_bold` (all five, otherwise the built-in Helvetica
    is used)

  Relative paths resolve from the JSON file. The skill bundles no fonts or
  logos; use only files the user is licensed to embed.

```bash
pip install reportlab   # once, if missing
python3 <skill-dir>/scripts/generate_pdf.py trip.json verpflegungsmehraufwand-YYYY-MM-<ort>.pdf
pdftoppm -png -r 70 <pdf> /tmp/prev   # look at every page before presenting
```

The PDF has no signature line by design. The script replaces "→" with "nach";
avoid other exotic symbols, since custom fonts often lack them.

## 6. Deliver

Save the PDF where the user wants it (the output folder from the
organization context, the current directory otherwise) and show it with
whatever file-sharing mechanism the environment provides. In the chat, give a
short summary: trip window, hotels found, the day-by-day amounts, total, the
defaults applied and anything still missing (e.g. final hotel invoice not in
the mailbox).

Writing style for all German text in the PDF: factual, no exaggerating words.
