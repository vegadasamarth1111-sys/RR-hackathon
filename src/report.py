"""Report entry points used by run_all.py."""
from __future__ import annotations

from .report_pdf import build_pdf
from .report_pptx import build_pptx
from .report_html import build_dashboard

__all__ = ["build_pdf", "build_pptx", "build_dashboard"]
