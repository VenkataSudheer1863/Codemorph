"""Report Generator Service.

Generates PDF reports for legacy analysis and migration plans.
Uses ReportLab for PDF generation.
"""

import io
import logging
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

BRAND_COLOR = colors.HexColor("#2dd4bf")
DARK_BG = colors.HexColor("#0a0c10")
HEADER_BG = colors.HexColor("#14171f")
TEXT_COLOR = colors.HexColor("#e2e8f0")


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontSize=28,
        leading=34,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor("#2dd4bf"),
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=40,
        textColor=colors.HexColor("#94a3b8"),
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=18,
        leading=22,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor("#2dd4bf"),
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="SubSection",
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.HexColor("#7c3aed"),
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontSize=10,
        leading=14,
        spaceAfter=6,
        textColor=colors.HexColor("#cbd5e1"),
    ))
    return styles


def generate_legacy_report(project: dict) -> bytes:
    """Generate Legacy Analysis PDF report.

    Includes: Architecture overview, module dependency map,
    tech stack, DB schema summary, API summary.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    styles = _get_styles()
    elements = []

    # Cover page
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("CodeMorph", styles["CoverTitle"]))
    elements.append(Paragraph("Legacy Codebase Analysis Report", styles["CoverSubtitle"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Project: {project.get('name', 'Unknown')}", styles["CoverSubtitle"]))
    elements.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        styles["CoverSubtitle"],
    ))
    elements.append(PageBreak())

    # Executive Summary
    elements.append(Paragraph("1. Executive Summary", styles["SectionTitle"]))
    elements.append(Paragraph(
        f"This report provides a comprehensive analysis of the legacy codebase "
        f"located at <b>{project.get('path', 'N/A')}</b>. The analysis covers "
        f"architecture, technology stack, APIs, and database schema.",
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 0.2 * inch))

    # Key Metrics
    elements.append(Paragraph("Key Metrics", styles["SubSection"]))
    metrics_data = [
        ["Metric", "Value"],
        ["Total Files", str(project.get("total_files", 0))],
        ["Lines of Code", f"{project.get('total_loc', 0):,}"],
        ["Languages", str(project.get("languages_count", 0))],
        ["Frameworks Detected", str(project.get("frameworks_count", 0))],
    ]
    metrics_table = Table(metrics_data, colWidths=[3 * inch, 3 * inch])
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f172a"), colors.HexColor("#1e293b")]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Language Distribution
    elements.append(Paragraph("2. Language Distribution", styles["SectionTitle"]))
    lang_dist = project.get("language_distribution", {})
    if lang_dist:
        lang_data = [["Language", "Percentage"]]
        for lang, pct in lang_dist.items():
            lang_data.append([lang, f"{pct}%"])
        lang_table = Table(lang_data, colWidths=[3 * inch, 3 * inch])
        lang_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f172a"), colors.HexColor("#1e293b")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(lang_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Architecture Layers
    elements.append(Paragraph("3. Architecture Overview", styles["SectionTitle"]))
    arch_layers = project.get("architecture_layers", {})
    if arch_layers:
        for layer_name, layer_data in arch_layers.items():
            if isinstance(layer_data, dict):
                file_count = layer_data.get("file_count", 0)
                frameworks = layer_data.get("frameworks", [])
                components = layer_data.get("components", [])
                elements.append(Paragraph(
                    f"<b>{layer_name.capitalize()}</b> — {file_count} files",
                    styles["SubSection"],
                ))
                if frameworks:
                    elements.append(Paragraph(
                        f"Frameworks: {', '.join(frameworks[:5])}",
                        styles["BodyText2"],
                    ))
                if components:
                    elements.append(Paragraph(
                        f"Components: {', '.join(components[:10])}{'...' if len(components) > 10 else ''}",
                        styles["BodyText2"],
                    ))
    elements.append(Spacer(1, 0.3 * inch))

    # Detected Stack
    elements.append(Paragraph("4. Technology Stack", styles["SectionTitle"]))
    detected_stack = project.get("detected_stack", [])
    if detected_stack:
        stack_data = [["Category", "Technology", "Confidence"]]
        for item in detected_stack:
            stack_data.append([
                item.get("label", ""),
                item.get("detected", ""),
                f"{item.get('confidence', 0)}%",
            ])
        stack_table = Table(stack_data, colWidths=[2 * inch, 2.5 * inch, 1.5 * inch])
        stack_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f172a"), colors.HexColor("#1e293b")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(stack_table)
    elements.append(Spacer(1, 0.3 * inch))

    # API Summary
    elements.append(Paragraph("5. API Endpoints", styles["SectionTitle"]))
    apis = project.get("detected_apis", [])
    if apis:
        api_data = [["Method", "Path", "Handler", "Type"]]
        for api in apis[:50]:  # Limit to 50 for readability
            api_data.append([
                api.get("method", ""),
                api.get("path", ""),
                api.get("handler", ""),
                api.get("type", "REST"),
            ])
        api_table = Table(api_data, colWidths=[1 * inch, 2 * inch, 2 * inch, 1 * inch])
        api_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f172a"), colors.HexColor("#1e293b")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(api_table)
    else:
        elements.append(Paragraph("No API endpoints detected.", styles["BodyText2"]))
    elements.append(Spacer(1, 0.3 * inch))

    # Database Summary
    elements.append(Paragraph("6. Database Schema", styles["SectionTitle"]))
    tables_data = project.get("detected_tables", [])
    if tables_data:
        db_data = [["Name", "Type", "Columns", "Relationships"]]
        for tbl in tables_data[:50]:
            db_data.append([
                tbl.get("name", ""),
                tbl.get("type", "Table"),
                str(tbl.get("columns", 0)),
                str(tbl.get("relationships", 0)),
            ])
        db_table = Table(db_data, colWidths=[2 * inch, 1.5 * inch, 1.25 * inch, 1.25 * inch])
        db_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f172a"), colors.HexColor("#1e293b")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(db_table)
    else:
        elements.append(Paragraph("No database objects detected.", styles["BodyText2"]))

    doc.build(elements)
    return buffer.getvalue()


def generate_migration_report(project: dict) -> bytes:
    """Generate Migration Report PDF.

    Includes: New architecture, new tech stack, migration mapping,
    component mapping, generated project structure.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    styles = _get_styles()
    elements = []

    # Cover page
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph("CodeMorph", styles["CoverTitle"]))
    elements.append(Paragraph("Migration Report", styles["CoverSubtitle"]))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Project: {project.get('name', 'Unknown')}", styles["CoverSubtitle"]))
    elements.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        styles["CoverSubtitle"],
    ))
    elements.append(PageBreak())

    # Selected Target Stack
    elements.append(Paragraph("1. Target Technology Stack", styles["SectionTitle"]))
    selected_stack = project.get("selected_stack", {})
    if selected_stack:
        stack_data = [["Category", "Selected Technology"]]
        for category, tech in selected_stack.items():
            label = category.replace("_", " ").title()
            stack_data.append([label, tech])
        s_table = Table(stack_data, colWidths=[3 * inch, 3 * inch])
        s_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f172a"), colors.HexColor("#1e293b")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(s_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Migration Mappings
    elements.append(Paragraph("2. Migration Mappings", styles["SectionTitle"]))
    mappings = project.get("transformation_mappings", [])
    if mappings:
        map_data = [["From", "To", "Files", "Status"]]
        for m in mappings:
            map_data.append([
                m.get("source", ""),
                m.get("target", ""),
                str(m.get("file_count", 0)),
                m.get("status", "pending"),
            ])
        m_table = Table(map_data, colWidths=[2 * inch, 2 * inch, 1 * inch, 1 * inch])
        m_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_COLOR),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#334155")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0f172a"), colors.HexColor("#1e293b")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(m_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Modernized Project Structure
    elements.append(Paragraph("3. Modernized Project Structure", styles["SectionTitle"]))
    elements.append(Paragraph(
        "The modernized codebase follows this structure:",
        styles["BodyText2"],
    ))
    structure_text = """
    modernized-project/
    ├── frontend/          — UI components, pages, assets
    ├── backend/           — Services, controllers, repositories
    ├── database/          — Migration scripts, schema definitions
    ├── configs/           — Application configs, environment files
    └── docs/              — API docs, migration notes
    """
    elements.append(Paragraph(
        structure_text.replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;"),
        styles["BodyText2"],
    ))
    elements.append(Spacer(1, 0.3 * inch))

    # Recommendations
    elements.append(Paragraph("4. Recommendations", styles["SectionTitle"]))
    recommendations = project.get("recommendations", [])
    if recommendations:
        for rec in recommendations:
            elements.append(Paragraph(
                f"<b>{rec.get('label', '')}</b>: "
                f"{rec.get('detected', '')} → {', '.join(rec.get('suggestions', []))}",
                styles["BodyText2"],
            ))
    elements.append(Spacer(1, 0.3 * inch))

    # Next Steps
    elements.append(Paragraph("5. Next Steps", styles["SectionTitle"]))
    next_steps = [
        "1. Review the generated codebase and verify business logic preservation",
        "2. Run unit tests and integration tests on the modernized code",
        "3. Set up CI/CD pipeline for the new project structure",
        "4. Plan database migration from legacy to target database",
        "5. Conduct performance testing and optimization",
        "6. Update deployment configurations for the target platform",
    ]
    for step in next_steps:
        elements.append(Paragraph(step, styles["BodyText2"]))

    doc.build(elements)
    return buffer.getvalue()
