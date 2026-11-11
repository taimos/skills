#!/usr/bin/env python3
"""Render a Verpflegungsmehraufwand (German per-diem) PDF from a JSON trip file.

Usage: python3 generate_pdf.py trip.json output.pdf

The script computes the per-diem amounts itself (rates and meal deductions
from the JSON "rates" block, defaulting to the German domestic rates 2026),
so the numbers in the PDF always match the day list.

Branding is optional. Without a "branding" block the PDF uses the built-in
Helvetica fonts, neutral colours and no logo. A "branding" block can set
"colors", "logo" (path to a PNG, "width_mm"), "fonts" (paths to TTF files
for "heading_bold", "heading_semibold", "body", "body_semibold",
"body_bold") and "footer". Relative paths resolve from the JSON file.
No fonts or logos are bundled with this skill.

Requires: reportlab (pip install reportlab)
"""
import json
import sys
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

DEFAULT_COLORS = {
    "accent": "#4A90A4",     # rules, bullets, total box border
    "primary": "#1F3A5F",    # headings, table headers
    "secondary": "#4A90A4",  # subtitle
    "muted": "#8A9399",      # header/footer text
    "text": "#333B40",       # body text
    "light": "#EEF3F5",      # zebra rows, total box
}

# Built-in PDF fonts, used when no TTF fonts are configured.
BUILTIN_FONTS = {
    "heading_bold": "Helvetica-Bold",
    "heading_semibold": "Helvetica-Bold",
    "body": "Helvetica",
    "body_semibold": "Helvetica-Bold",
    "body_bold": "Helvetica-Bold",
}

DEFAULT_RATES = {"full": 28.0, "partial": 14.0, "breakfast_pct": 0.20, "meal_pct": 0.40}
DAY_TYPES = {
    "arrival": ("Anreisetag", "partial"),
    "departure": ("Abreisetag", "partial"),
    "full": ("voller Kalendertag", "full"),
    "single": ("eintägig, mehr als 8 Std.", "partial"),
    "short": ("eintägig, bis 8 Std.", None),
}
WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


USE_TTF = False


def resolve(path, base):
    p = Path(path).expanduser()
    return p if p.is_absolute() else (base / p)


def register_fonts(branding, base):
    """Return the font names to use. TTF fonts are used only if all five are configured."""
    global USE_TTF
    cfg = branding.get("fonts") or {}
    if not all(cfg.get(k) for k in BUILTIN_FONTS):
        return dict(BUILTIN_FONTS)
    names = {}
    for key in BUILTIN_FONTS:
        name = f"Custom-{key}"
        pdfmetrics.registerFont(TTFont(name, str(resolve(cfg[key], base))))
        names[key] = name
    pdfmetrics.registerFontFamily(names["body"], normal=names["body"], bold=names["body_bold"],
                                  italic=names["body"], boldItalic=names["body_bold"])
    USE_TTF = True
    return names


def clean(t):
    """Replace glyphs that common fonts lack (e.g. arrows) with safe text."""
    t = str(t).replace(" → ", " nach ").replace("→", " nach ").replace("■", "•")
    return t if USE_TTF else t.replace("−", "-")


def eur(v):
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if v < 0 else "") + s + " €"


def de_date(iso, weekday=True):
    d = date.fromisoformat(iso)
    s = d.strftime("%d.%m.%Y")
    return f"{WEEKDAYS[d.weekday()]} {s}" if weekday else s


def compute(days, rates):
    rows, totals = [], {"base": 0.0, "breakfast": 0.0, "lunch": 0.0, "dinner": 0.0, "net": 0.0}
    bf = round(rates["full"] * rates["breakfast_pct"], 2)
    meal = round(rates["full"] * rates["meal_pct"], 2)
    for d in days:
        label, key = DAY_TYPES[d["type"]]
        base = rates[key] if key else 0.0
        ded = {"breakfast": -bf if d.get("breakfast") else 0.0,
               "lunch": -meal if d.get("lunch") else 0.0,
               "dinner": -meal if d.get("dinner") else 0.0}
        net = max(0.0, base + sum(ded.values()))
        rows.append({"date": d["date"], "label": label, "base": base, **ded, "net": net})
        totals["base"] += base
        for k in ded:
            totals[k] += ded[k]
        totals["net"] += net
    return rows, totals, bf, meal


def build(data, out, base=Path(".")):
    branding = data.get("branding", {})
    F = register_fonts(branding, base)
    C = {k: colors.HexColor(v) for k, v in {**DEFAULT_COLORS, **branding.get("colors", {})}.items()}
    GREEN, BLUE, PETROL, GRAY, TEXT, LIGHT = (C["accent"], C["primary"], C["secondary"],
                                              C["muted"], C["text"], C["light"])
    rates = {**DEFAULT_RATES, **data.get("rates", {})}
    rows, totals, bf, meal = compute(data["days"], rates)

    st = {
        "h1": ParagraphStyle("h1", fontName=F["heading_bold"], fontSize=20, leading=24, textColor=BLUE, spaceAfter=2 * mm),
        "sub": ParagraphStyle("sub", fontName=F["heading_semibold"], fontSize=11, leading=14, textColor=PETROL, spaceAfter=5 * mm),
        "h2": ParagraphStyle("h2", fontName=F["heading_bold"], fontSize=13, leading=16, textColor=BLUE, spaceBefore=6 * mm, spaceAfter=2.5 * mm),
        "body": ParagraphStyle("body", fontName=F["body"], fontSize=9, leading=13, textColor=TEXT),
        "small": ParagraphStyle("small", fontName=F["body"], fontSize=8, leading=11, textColor=TEXT),
        "cell": ParagraphStyle("cell", fontName=F["body"], fontSize=8, leading=10.5, textColor=TEXT),
        "cellr": ParagraphStyle("cellr", fontName=F["body"], fontSize=8, leading=10.5, textColor=TEXT, alignment=TA_RIGHT),
        "th": ParagraphStyle("th", fontName=F["body_bold"], fontSize=8, leading=10.5, textColor=colors.white),
        "thr": ParagraphStyle("thr", fontName=F["body_bold"], fontSize=8, leading=10.5, textColor=colors.white, alignment=TA_RIGHT),
        "total": ParagraphStyle("total", fontName=F["heading_bold"], fontSize=12, leading=15, textColor=BLUE),
        "totalr": ParagraphStyle("totalr", fontName=F["heading_bold"], fontSize=12, leading=15, textColor=BLUE, alignment=TA_RIGHT),
    }
    P = lambda t, s="cell": Paragraph(clean(t), st[s])

    def table(header, body, widths, right_cols=(), bold_last=False):
        hdr = [P(h, "thr" if i in right_cols else "th") for i, h in enumerate(header)]
        rws = [[P(c, "cellr" if i in right_cols else "cell") for i, c in enumerate(r)] for r in body]
        t = Table([hdr] + rws, colWidths=widths, repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#DDE3E4")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ]
        if bold_last:
            style += [("LINEABOVE", (0, -1), (-1, -1), 1.2, GREEN), ("BACKGROUND", (0, -1), (-1, -1), colors.white)]
        t.setStyle(TableStyle(style))
        return t

    W = A4[0] - 36 * mm
    story = []
    tr = data["traveller"]
    story.append(P("Reisekostenabrechnung: Verpflegungsmehraufwand", "h1"))
    story.append(P(f'{de_date(data["period"]["start"], False)} bis {de_date(data["period"]["end"], False)} · {data.get("title", "")}', "sub"))

    meta = [
        ("Reisender", f'{tr["name"]}, {tr.get("role", "")}'.strip(", ")),
        ("Anschrift", tr.get("address", "")),
        ("Reisezeitraum", f'{de_date(data["period"]["start"])} bis {de_date(data["period"]["end"])}'),
        ("Reisezweck", "<br/>".join(f"{i + 1}. {p}" for i, p in enumerate(data["purposes"]))),
        ("Verkehrsmittel", data.get("vehicle", "")),
        ("Rechtsgrundlage", data.get("legal_basis",
            f'§ 9 Abs. 4a EStG, Inlandspauschalen ({eur(rates["partial"])} An-/Abreisetag, {eur(rates["full"])} volle '
            f'Kalendertage; Kürzung für gestellte Mahlzeiten {int(rates["breakfast_pct"]*100)} % bzw. '
            f'{int(rates["meal_pct"]*100)} % von {eur(rates["full"])})')),
    ]
    mt = Table([[P(k, "cell"), P(v, "body")] for k, v in meta], colWidths=[32 * mm, W - 32 * mm])
    mt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), F["body_bold"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, GREEN),
        ("LEFTPADDING", (0, 0), (0, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    story.append(mt)

    if data.get("itinerary"):
        story.append(P("Reiseverlauf", "h2"))
        story.append(table(["Datum", "Beginn / Ende", "Ort", "Tätigkeit"],
                           [[de_date(i["date"]), i.get("time", ""), i.get("place", ""), i.get("activity", "")] for i in data["itinerary"]],
                           [24 * mm, 34 * mm, 48 * mm, W - 106 * mm]))

    story.append(P("Berechnung Verpflegungsmehraufwand", "h2"))
    body = [[de_date(r["date"]), r["label"], eur(r["base"]),
             eur(r["breakfast"]) if r["breakfast"] else "", eur(r["lunch"]) if r["lunch"] else "",
             eur(r["dinner"]) if r["dinner"] else "", eur(r["net"])] for r in rows]
    body.append(["<b>Summe</b>", "", f'<b>{eur(totals["base"])}</b>', f'<b>{eur(totals["breakfast"])}</b>',
                 f'<b>{eur(totals["lunch"])}</b>', f'<b>{eur(totals["dinner"])}</b>', f'<b>{eur(totals["net"])}</b>'])
    story.append(table(["Datum", "Art des Tages", "Pauschale", f"Frühstück<br/>{eur(-bf)}", f"Mittag<br/>{eur(-meal)}",
                        f"Abend<br/>{eur(-meal)}", "Ansatz"], body,
                       [26 * mm, 29 * mm, 19 * mm, 24 * mm, 24 * mm, 24 * mm, W - 146 * mm],
                       right_cols=(2, 3, 4, 5, 6), bold_last=True))
    story.append(Spacer(1, 4 * mm))
    box = Table([[P("Erstattungsbetrag Verpflegungsmehraufwand", "total"), P(eur(totals["net"]), "totalr")]],
                colWidths=[W - 40 * mm, 40 * mm])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LINEBEFORE", (0, 0), (0, 0), 3, GREEN),
                             ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(box)

    if data.get("deduction_notes"):
        notes = [[P(f'<font color="{PETROL.hexval().replace("0x", "#")}">•</font>&nbsp;&nbsp;{n}', "body"), Spacer(1, 1.5 * mm)] for n in data["deduction_notes"]]
        story.append(KeepTogether([P("Begründung der Kürzungen", "h2")] + notes[0]))
        for n in notes[1:]:
            story.extend(n)

    if data.get("hotels"):
        blk = [P(data.get("hotels_heading", "Übernachtungen (nachrichtlich)"), "h2")]
        blk.append(table(["Hotel", "Zeitraum", "Nächte", "Betrag brutto", "Frühstück", "Beleg"],
                         [[h["name"], h["period"], h["nights"], h["amount"], h.get("breakfast", ""), h.get("receipt", "")] for h in data["hotels"]],
                         [42 * mm, 24 * mm, 15 * mm, 32 * mm, 22 * mm, W - 135 * mm]))
        story.append(KeepTogether(blk))
        for n in data.get("hotel_notes", []):
            story.append(Spacer(1, 2 * mm))
            story.append(P(n, "body"))

    if data.get("travel_costs_note"):
        story.append(P("Fahrtkosten (nachrichtlich)", "h2"))
        story.append(P(data["travel_costs_note"], "body"))

    summary = [["Verpflegungsmehraufwand", eur(totals["net"])]] + [[s["label"], s["amount"]] for s in data.get("extra_payouts", [])]
    story.append(KeepTogether([
        P("Zusammenfassung", "h2"),
        table(["Position", "Betrag"], summary + [["<b>Auszahlungsbetrag an den Reisenden</b>",
              f'<b>{data.get("payout_total") or eur(totals["net"])}</b>']], [W - 40 * mm, 40 * mm], right_cols=(1,), bold_last=True),
    ]))

    footer_left = clean(branding.get("footer") or data.get("footer") or "")
    logo = branding.get("logo") or {}
    logo_path = resolve(logo["path"], base) if logo.get("path") else None

    def on_page(c, doc):
        c.saveState()
        pw, ph = A4
        c.setFillColor(GREEN)
        c.rect(0, ph - 4 * mm, pw, 4 * mm, stroke=0, fill=1)
        if logo_path:
            lw = logo.get("width_mm", 36) * mm
            iw, ih = ImageReader(str(logo_path)).getSize()
            c.drawImage(str(logo_path), 18 * mm, ph - 20 * mm, width=lw, height=lw * ih / iw, mask="auto")
        c.setFont(F["body"], 8)
        c.setFillColor(GRAY)
        c.drawRightString(pw - 18 * mm, ph - 15 * mm, f'Erstellt am {de_date(data.get("created", date.today().isoformat()), False)}')
        c.setStrokeColor(GREEN)
        c.setLineWidth(0.6)
        c.line(18 * mm, 16 * mm, pw - 18 * mm, 16 * mm)
        c.drawString(18 * mm, 11 * mm, footer_left)
        c.drawRightString(pw - 18 * mm, 11 * mm, f"Seite {doc.page}")
        c.restoreState()

    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=28 * mm, bottomMargin=22 * mm,
                            title=f'Verpflegungsmehraufwand {data.get("title", "")}', author=tr["name"])
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return totals["net"]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: generate_pdf.py trip.json output.pdf")
    src = Path(sys.argv[1]).resolve()
    total = build(json.loads(src.read_text(encoding="utf-8")), sys.argv[2], src.parent)
    print(f"OK: {sys.argv[2]} (Verpflegungsmehraufwand {eur(total)})")
