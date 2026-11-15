"""Build the current technical report PDF from tracked Markdown sources."""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "technical-report.pdf"


def clean(text):
    text = text.replace("²", "^2").replace("—", "-").replace("–", "-")
    text = text.replace("≥", ">=").replace("≤", "<=").replace("×", "x")
    text = text.replace("**", "").replace("`", "")
    return escape(text)


def markdown_flowables(path):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                              fontSize=20, leading=25, textColor=colors.HexColor("#12304c"), spaceAfter=14))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
                              fontSize=12, leading=16, textColor=colors.HexColor("#12616a"),
                              spaceBefore=12, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9.2,
                              leading=13.5, spaceAfter=7, alignment=TA_LEFT,
                              allowWidows=0, allowOrphans=0))
    styles.add(ParagraphStyle(name="TableSmall", parent=styles["BodyText"], fontSize=7.1,
                              leading=9.2, spaceAfter=0))
    lines = path.read_text(encoding="utf-8").splitlines()
    flow = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[:\- ]+", cell) for cell in cells):
                    rows.append([Paragraph(clean(cell), styles["TableSmall"]) for cell in cells])
                index += 1
            table = LongTable(rows, colWidths=[174 * mm / len(rows[0])] * len(rows[0]), repeatRows=1,
                              hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dceff0")),
                                       ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#b8c9d0")),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 4),
                                       ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                                       ("TOPPADDING", (0, 0), (-1, -1), 1),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
            flow.extend([table, Spacer(1, 5 * mm)])
            continue
        if line.startswith("# "):
            flow.append(Paragraph(clean(line[2:]), styles["ReportTitle"]))
        elif line.startswith("## "):
            flow.append(Paragraph(clean(line[3:]), styles["Section"]))
        else:
            paragraph = [line]
            while index + 1 < len(lines) and lines[index + 1].strip() and not lines[index + 1].startswith(("#", "|")):
                index += 1
                paragraph.append(lines[index].strip())
            flow.append(Paragraph(clean(" ".join(paragraph)), styles["BodySmall"]))
        index += 1
    return flow


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#647887"))
    canvas.drawString(18 * mm, 13 * mm, "SMART RACING CHAMPIONSHIP  /  DRAFT")
    canvas.drawRightString(A4[0] - 18 * mm, 13 * mm, str(document.page))
    canvas.restoreState()


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                                 topMargin=18 * mm, bottomMargin=20 * mm, title="Smart Racing Championship - Draft Report")
    flow = markdown_flowables(ROOT / "docs" / "report" / "technical-report.md")
    flow += markdown_flowables(ROOT / "experiments" / "results" / "analysis.md")
    document.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
