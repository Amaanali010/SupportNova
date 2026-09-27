# tests/test_phase8.py
# Comprehensive Pytest test suite for SupportNova Phase 8.
# Validates batch dataset evaluation runner, comparison report generation, and system documentation.

import os
import pytest
from reports.batch_runner import run_batch_dataset_evaluation
from database.seed import run_seed_if_needed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_batch_runner_execution():
    """Test batch dataset evaluation runner over sample dataset rows."""
    run_seed_if_needed()

    summary = run_batch_dataset_evaluation(limit=3)
    assert summary["total_processed"] == 3
    assert "verification_rate_pct" in summary
    assert "category_agreement_pct" in summary

    # Check that comparison_report.md was generated
    report_path = os.path.join(BASE_DIR, "reports", "comparison_report.md")
    assert os.path.exists(report_path)

def test_readme_and_reports_existence():
    """Test existence of README.md documentation and comparison report files."""
    readme_path = os.path.join(BASE_DIR, "README.md")
    assert os.path.exists(readme_path)

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Streamlit Community Cloud Deployment Guide" in content
    assert "Dual-Pipeline Workflow" in content
    assert "GROQ_API_KEY" in content
