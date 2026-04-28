from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

REPORTS = [
    (
        DOCS / "assignment-4-report.pdf",
        [
            DOCS / "incident-report.md",
            DOCS / "postmortem.md",
        ],
        "Assignment 4: Incident Response Simulation and Postmortem",
    ),
    (
        DOCS / "assignment-5-report.pdf",
        [
            DOCS / "assignment-5-terraform.md",
            DOCS / "deployment-guide.md",
        ],
        "Assignment 5: Terraform Implementation and Deployment Guide",
    ),
    (
        DOCS / "final-submission-report.pdf",
        [
            DOCS / "final-submission-report.md",
            ROOT / "README.md",
            DOCS / "incident-report.md",
            DOCS / "postmortem.md",
            DOCS / "assignment-5-terraform.md",
            DOCS / "deployment-guide.md",
            DOCS / "final-submission-checklist.md",
        ],
        "Final Submission Report",
    ),
]


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=22,
            leading=28,
            textColor=colors.HexColor("#132227"),
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading1Custom",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#132227"),
            spaceAfter=10,
            spaceBefore=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading2Custom",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0E2C34"),
            spaceAfter=8,
            spaceBefore=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletCustom",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=14,
            leftIndent=12,
            bulletIndent=0,
            spaceAfter=4,
        )
    )
    return styles


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def add_markdown(story: list, text: str, styles) -> None:
    lines = text.splitlines()
    in_code = False
    code_lines: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(
                    Preformatted(
                        "\n".join(code_lines),
                        styles["Code"],
                        dedent=0,
                    )
                )
                story.append(Spacer(1, 0.2 * cm))
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            story.append(Spacer(1, 0.14 * cm))
            continue

        if line.startswith("# "):
            story.append(Paragraph(escape(line[2:].strip()), styles["Heading1Custom"]))
            continue

        if line.startswith("## "):
            story.append(Paragraph(escape(line[3:].strip()), styles["Heading2Custom"]))
            continue

        if line.startswith("### "):
            story.append(Paragraph(f"<b>{escape(line[4:].strip())}</b>", styles["BodyCustom"]))
            continue

        if line.startswith("- "):
            story.append(Paragraph(escape(line[2:].strip()), styles["BulletCustom"], bulletText="•"))
            continue

        if line[:2].isdigit() and line[1:3] == ". ":
            story.append(Paragraph(escape(line[3:].strip()), styles["BulletCustom"], bulletText=f"{line[0]}."))
            continue

        if "|" in line and not set(line.replace("|", "").strip()) <= {"-", " "}:
            cells = [escape(cell.strip()) for cell in line.strip("|").split("|")]
            story.append(
                Table(
                    [cells],
                    colWidths=[16 * cm / max(len(cells), 1)] * len(cells),
                    style=TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9CDD1")),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F4EE")),
                            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ]
                    ),
                )
            )
            continue

        story.append(Paragraph(escape(line), styles["BodyCustom"]))


def build_report(output_path: Path, markdown_files: list[Path], title: str, styles) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=title,
    )
    story: list = [
        Spacer(1, 2 * cm),
        Paragraph(escape(title), styles["CoverTitle"]),
        Paragraph("Generated from the project documentation package.", styles["BodyCustom"]),
        Spacer(1, 0.8 * cm),
    ]

    for markdown_path in markdown_files:
        story.append(Paragraph(f"<b>Source:</b> {escape(os.path.relpath(markdown_path, ROOT))}", styles["BodyCustom"]))
        story.append(Spacer(1, 0.15 * cm))
        add_markdown(story, markdown_path.read_text(encoding="utf-8"), styles)
        story.append(Spacer(1, 0.6 * cm))

    document.build(story)


def main() -> None:
    styles = build_styles()
    for output_path, markdown_files, title in REPORTS:
        build_report(output_path, markdown_files, title, styles)
        print(f"Created {output_path}")


if __name__ == "__main__":
    main()
