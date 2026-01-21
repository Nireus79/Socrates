"""
Report generation service for analytics exports.

Provides PDF and CSV report generation for project analytics, using:
- reportlab for PDF generation with charts and formatting
- pandas for CSV generation with structured data
"""

import csv
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import optional dependencies for report generation
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT  # noqa: F401
    from reportlab.lib.pagesizes import A4, letter  # noqa: F401
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,  # noqa: F401
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available - PDF reports will use fallback format")

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available - CSV reports will use standard csv module")


class ReportGenerator:
    """Generate PDF and CSV analytics reports."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to store generated reports (defaults to system temp)
        """
        if output_dir is None:
            # Use .socrates directory for reports, with temp as fallback
            socrates_dir = Path.home() / ".socrates" / "reports"
            output_dir = str(socrates_dir)

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Report output directory: {self.output_dir}")

    def generate_project_report(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        analytics_data: Dict[str, Any],
        format_type: str = "pdf",
    ) -> Tuple[bool, str, str]:
        """
        Generate analytics report for a project.

        Args:
            project_id: Project identifier
            project_data: Project information dict
            analytics_data: Analytics metrics dict
            format_type: 'pdf' or 'csv'

        Returns:
            Tuple of (success: bool, filepath: str, error_message: str)
        """
        try:
            if format_type == "pdf":
                return self._generate_pdf_report(project_id, project_data, analytics_data)
            elif format_type == "csv":
                return self._generate_csv_report(project_id, project_data, analytics_data)
            else:
                return False, "", f"Unsupported format: {format_type}"
        except Exception as e:
            logger.error(f"Error generating {format_type} report for {project_id}: {e}")
            return False, "", str(e)

    def _generate_pdf_report(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        analytics_data: Dict[str, Any],
    ) -> Tuple[bool, str, str]:
        """
        Generate PDF report using reportlab.

        Args:
            project_id: Project identifier
            project_data: Project information
            analytics_data: Analytics metrics

        Returns:
            Tuple of (success, filepath, error_message)
        """
        if not REPORTLAB_AVAILABLE:
            return self._generate_pdf_fallback(project_id, project_data, analytics_data)

        try:
            # Create PDF file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{project_id}_{timestamp}.pdf"
            filepath = self.output_dir / filename

            # Create PDF document
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Container for PDF elements
            elements = []

            # Create styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1f4788"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#333333"),
                spaceAfter=12,
                spaceBefore=12,
            )

            # Add title
            elements.append(Paragraph("Project Analytics Report", title_style))
            elements.append(Spacer(1, 0.3 * inch))

            # Add project information section
            elements.append(Paragraph("Project Information", heading_style))
            project_info_data = [
                ["Project ID", project_id],
                ["Project Name", project_data.get("name", "N/A")],
                ["Owner", project_data.get("owner", "N/A")],
                ["Current Phase", project_data.get("phase", "N/A")],
                ["Status", project_data.get("status", "N/A")],
                ["Created", project_data.get("created_at", "N/A")],
            ]
            project_table = Table(project_info_data, colWidths=[2 * inch, 4 * inch])
            project_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eef5")),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ]
                )
            )
            elements.append(project_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Add analytics section
            elements.append(Paragraph("Analytics Summary", heading_style))
            analytics_data_formatted = [
                ["Metric", "Value"],
                [
                    "Total Questions",
                    str(analytics_data.get("total_questions", 0)),
                ],
                [
                    "Total Answers",
                    str(analytics_data.get("total_answers", 0)),
                ],
                [
                    "Code Generation Count",
                    str(analytics_data.get("code_generation_count", 0)),
                ],
                [
                    "Code Lines Generated",
                    str(analytics_data.get("code_lines_generated", 0)),
                ],
                [
                    "Confidence Score",
                    f"{analytics_data.get('confidence_score', 0)}%",
                ],
                [
                    "Learning Velocity",
                    f"{analytics_data.get('learning_velocity', 0)}%",
                ],
                [
                    "Average Response Time",
                    f"{analytics_data.get('average_response_time', 0)}s",
                ],
            ]
            analytics_table = Table(analytics_data_formatted, colWidths=[3 * inch, 3 * inch])
            analytics_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4788")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f0f0f0")],
                        ),
                    ]
                )
            )
            elements.append(analytics_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Add categories if available
            if "categories" in analytics_data:
                elements.append(Paragraph("Topic Categories", heading_style))
                categories = analytics_data["categories"]
                categories_data = [["Category", "Count"]]
                for category, count in categories.items():
                    categories_data.append([category.title(), str(count)])

                categories_table = Table(categories_data, colWidths=[3 * inch, 3 * inch])
                categories_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4788")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                            (
                                "ROWBACKGROUNDS",
                                (0, 1),
                                (-1, -1),
                                [colors.white, colors.HexColor("#f0f0f0")],
                            ),
                        ]
                    )
                )
                elements.append(categories_table)
                elements.append(Spacer(1, 0.3 * inch))

            # Add footer
            footer_text = (
                f"<i>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
            )
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph(footer_text, styles["Normal"]))

            # Build PDF
            doc.build(elements)

            logger.info(f"PDF report generated: {filepath}")
            return True, str(filepath), ""

        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return False, "", str(e)

    def _generate_pdf_fallback(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        analytics_data: Dict[str, Any],
    ) -> Tuple[bool, str, str]:
        """
        Generate PDF report without reportlab (basic format).

        Args:
            project_id: Project identifier
            project_data: Project information
            analytics_data: Analytics metrics

        Returns:
            Tuple of (success, filepath, error_message)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{project_id}_{timestamp}.txt"
            filepath = self.output_dir / filename

            with open(filepath, "w") as f:
                f.write("=" * 60 + "\n")
                f.write("PROJECT ANALYTICS REPORT\n")
                f.write("=" * 60 + "\n\n")

                f.write("PROJECT INFORMATION\n")
                f.write("-" * 60 + "\n")
                f.write(f"Project ID:     {project_id}\n")
                f.write(f"Project Name:   {project_data.get('name', 'N/A')}\n")
                f.write(f"Owner:          {project_data.get('owner', 'N/A')}\n")
                f.write(f"Current Phase:  {project_data.get('phase', 'N/A')}\n")
                f.write(f"Status:         {project_data.get('status', 'N/A')}\n")
                f.write(f"Created:        {project_data.get('created_at', 'N/A')}\n\n")

                f.write("ANALYTICS SUMMARY\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total Questions:        {analytics_data.get('total_questions', 0)}\n")
                f.write(f"Total Answers:          {analytics_data.get('total_answers', 0)}\n")
                f.write(
                    f"Code Generation Count:  {analytics_data.get('code_generation_count', 0)}\n"
                )
                f.write(
                    f"Code Lines Generated:   {analytics_data.get('code_lines_generated', 0)}\n"
                )
                f.write(f"Confidence Score:       {analytics_data.get('confidence_score', 0)}%\n")
                f.write(f"Learning Velocity:      {analytics_data.get('learning_velocity', 0)}%\n")
                f.write(
                    f"Average Response Time:  {analytics_data.get('average_response_time', 0)}s\n\n"
                )

                if "categories" in analytics_data:
                    f.write("TOPIC CATEGORIES\n")
                    f.write("-" * 60 + "\n")
                    for category, count in analytics_data["categories"].items():
                        f.write(f"{category.title():20} {count}\n")
                    f.write("\n")

                f.write("=" * 60 + "\n")
                f.write(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            logger.info(f"Fallback text report generated: {filepath}")
            return True, str(filepath), ""

        except Exception as e:
            logger.error(f"Error generating fallback report: {e}")
            return False, "", str(e)

    def _generate_csv_report(
        self,
        project_id: str,
        project_data: Dict[str, Any],
        analytics_data: Dict[str, Any],
    ) -> Tuple[bool, str, str]:
        """
        Generate CSV report.

        Args:
            project_id: Project identifier
            project_data: Project information
            analytics_data: Analytics metrics

        Returns:
            Tuple of (success, filepath, error_message)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{project_id}_{timestamp}.csv"
            filepath = self.output_dir / filename

            if PANDAS_AVAILABLE:
                return self._generate_csv_pandas(filepath, project_id, project_data, analytics_data)
            else:
                return self._generate_csv_standard(
                    filepath, project_id, project_data, analytics_data
                )

        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
            return False, "", str(e)

    def _generate_csv_pandas(
        self,
        filepath: Path,
        project_id: str,
        project_data: Dict[str, Any],
        analytics_data: Dict[str, Any],
    ) -> Tuple[bool, str, str]:
        """
        Generate CSV report using pandas.

        Args:
            filepath: Output file path
            project_id: Project identifier
            project_data: Project information
            analytics_data: Analytics metrics

        Returns:
            Tuple of (success, filepath, error_message)
        """
        try:
            # Create project info dataframe
            project_df = pd.DataFrame(
                {
                    "Field": ["Project ID", "Project Name", "Owner", "Phase", "Status", "Created"],
                    "Value": [
                        project_id,
                        project_data.get("name", "N/A"),
                        project_data.get("owner", "N/A"),
                        project_data.get("phase", "N/A"),
                        project_data.get("status", "N/A"),
                        project_data.get("created_at", "N/A"),
                    ],
                }
            )

            # Create analytics dataframe
            analytics_list = [
                {"Metric": "Total Questions", "Value": analytics_data.get("total_questions", 0)},
                {"Metric": "Total Answers", "Value": analytics_data.get("total_answers", 0)},
                {
                    "Metric": "Code Generation Count",
                    "Value": analytics_data.get("code_generation_count", 0),
                },
                {
                    "Metric": "Code Lines Generated",
                    "Value": analytics_data.get("code_lines_generated", 0),
                },
                {
                    "Metric": "Confidence Score (%)",
                    "Value": analytics_data.get("confidence_score", 0),
                },
                {
                    "Metric": "Learning Velocity (%)",
                    "Value": analytics_data.get("learning_velocity", 0),
                },
                {
                    "Metric": "Average Response Time (s)",
                    "Value": analytics_data.get("average_response_time", 0),
                },
            ]

            if "categories" in analytics_data:
                for category, count in analytics_data["categories"].items():
                    analytics_list.append(
                        {
                            "Metric": f"{category.title()} Count",
                            "Value": count,
                        }
                    )

            analytics_df = pd.DataFrame(analytics_list)

            # Write to CSV with two sections
            with open(filepath, "w", newline="") as f:
                f.write("PROJECT INFORMATION\n")
                project_df.to_csv(f, index=False)
                f.write("\n\nANALYTICS DATA\n")
                analytics_df.to_csv(f, index=False)
                f.write(f"\n\nGenerated: {datetime.now().isoformat()}\n")

            logger.info(f"CSV report (pandas) generated: {filepath}")
            return True, str(filepath), ""

        except Exception as e:
            logger.error(f"Error generating pandas CSV: {e}")
            return False, "", str(e)

    def _generate_csv_standard(
        self,
        filepath: Path,
        project_id: str,
        project_data: Dict[str, Any],
        analytics_data: Dict[str, Any],
    ) -> Tuple[bool, str, str]:
        """
        Generate CSV report using standard csv module.

        Args:
            filepath: Output file path
            project_id: Project identifier
            project_data: Project information
            analytics_data: Analytics metrics

        Returns:
            Tuple of (success, filepath, error_message)
        """
        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)

                # Project information section
                writer.writerow(["PROJECT INFORMATION"])
                writer.writerow(["Field", "Value"])
                writer.writerow(["Project ID", project_id])
                writer.writerow(["Project Name", project_data.get("name", "N/A")])
                writer.writerow(["Owner", project_data.get("owner", "N/A")])
                writer.writerow(["Phase", project_data.get("phase", "N/A")])
                writer.writerow(["Status", project_data.get("status", "N/A")])
                writer.writerow(["Created", project_data.get("created_at", "N/A")])

                # Empty row for separation
                writer.writerow([])

                # Analytics section
                writer.writerow(["ANALYTICS DATA"])
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Total Questions", analytics_data.get("total_questions", 0)])
                writer.writerow(["Total Answers", analytics_data.get("total_answers", 0)])
                writer.writerow(
                    ["Code Generation Count", analytics_data.get("code_generation_count", 0)]
                )
                writer.writerow(
                    ["Code Lines Generated", analytics_data.get("code_lines_generated", 0)]
                )
                writer.writerow(["Confidence Score (%)", analytics_data.get("confidence_score", 0)])
                writer.writerow(
                    ["Learning Velocity (%)", analytics_data.get("learning_velocity", 0)]
                )
                writer.writerow(
                    ["Average Response Time (s)", analytics_data.get("average_response_time", 0)]
                )

                # Categories if available
                if "categories" in analytics_data:
                    writer.writerow([])
                    writer.writerow(["TOPIC CATEGORIES"])
                    writer.writerow(["Category", "Count"])
                    for category, count in analytics_data["categories"].items():
                        writer.writerow([category.title(), count])

                # Footer
                writer.writerow([])
                writer.writerow([f"Generated: {datetime.now().isoformat()}"])

            logger.info(f"CSV report (standard) generated: {filepath}")
            return True, str(filepath), ""

        except Exception as e:
            logger.error(f"Error generating standard CSV: {e}")
            return False, "", str(e)

    def cleanup_old_reports(self, max_age_hours: int = 24) -> int:
        """
        Clean up old report files.

        Args:
            max_age_hours: Remove files older than this many hours

        Returns:
            Number of files deleted
        """
        try:
            import time

            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            deleted_count = 0

            for filepath in self.output_dir.glob("*"):
                if filepath.is_file():
                    file_age = current_time - filepath.stat().st_mtime
                    if file_age > max_age_seconds:
                        filepath.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old report: {filepath}")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old reports: {e}")
            return 0


# Global report generator instance
_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Get or create global report generator instance."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
