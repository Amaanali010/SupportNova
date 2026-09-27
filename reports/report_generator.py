# reports/report_generator.py
# Module for generating triage analytics, SLA breach risk metrics, category breakdowns, and CSV exports.

import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from database.db import execute_query

SLA_THRESHOLD_HOURS = {
    "Critical": 2,
    "Urgent": 2,
    "High": 6,
    "Medium": 24,
    "Low": 48
}

def calculate_sla_risk() -> List[Dict[str, Any]]:
    """
    Evaluates open/unresolved complaints against SLA threshold hours.
    Returns list of complaints at risk of SLA breach.
    """
    open_complaints = execute_query(
        "SELECT * FROM complaints WHERE status NOT LIKE 'Resolved%' ORDER BY created_at ASC"
    )

    at_risk = []
    now = datetime.now()

    for comp in open_complaints:
        comp_dict = dict(comp)
        urgency = comp_dict.get("urgency", "Medium") or "Medium"
        created_str = comp_dict.get("created_at", "") or ""
        max_hours = SLA_THRESHOLD_HOURS.get(urgency, 24)

        try:
            created_dt = datetime.strptime(created_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
            elapsed_hours = (now - created_dt).total_seconds() / 3600.0
            
            if elapsed_hours >= (max_hours * 0.75): # 75% of SLA threshold used
                at_risk.append({
                    "complaint_id": comp_dict["complaint_id"],
                    "customer_id": comp_dict["customer_id"],
                    "category": comp_dict.get("category", "Unclassified"),
                    "urgency": urgency,
                    "status": comp_dict["status"],
                    "elapsed_hours": round(elapsed_hours, 1),
                    "sla_limit_hours": max_hours,
                    "is_breached": elapsed_hours >= max_hours
                })
        except Exception:
            continue

    return at_risk

def generate_system_summary_metrics() -> Dict[str, Any]:
    """
    Computes overall system metrics: totals, category distribution, status distribution, and review queue volume.
    """
    total_cmp = execute_query("SELECT COUNT(*) as c FROM complaints")[0]['c']
    verified_cmp = execute_query("SELECT COUNT(*) as c FROM complaints WHERE status = 'Verified'")[0]['c']
    review_cmp = execute_query("SELECT COUNT(*) as c FROM complaints WHERE status = 'Manual_Review'")[0]['c']
    resolved_cmp = execute_query("SELECT COUNT(*) as c FROM complaints WHERE status LIKE 'Resolved%'")[0]['c']
    escalated_cmp = execute_query("SELECT COUNT(*) as c FROM complaints WHERE status LIKE 'Escalated%' OR status = 'Manual_Review'")[0]['c']

    cat_rows = execute_query("SELECT category, COUNT(*) as c FROM complaints GROUP BY category")
    cat_distribution = {r['category'] or 'Unclassified': r['c'] for r in cat_rows}

    dept_rows = execute_query("SELECT department, COUNT(*) as c FROM rules GROUP BY department")
    dept_distribution = {r['department'] or 'Unassigned': r['c'] for r in dept_rows}

    return {
        "total_complaints": total_cmp,
        "verified_count": verified_cmp,
        "manual_review_count": review_cmp,
        "resolved_count": resolved_cmp,
        "escalated_count": escalated_cmp,
        "category_distribution": cat_distribution,
        "department_distribution": dept_distribution
    }

def export_complaints_to_csv(complaints_list: List[Dict[str, Any]]) -> str:
    """
    Converts list of complaint dictionaries into a downloadable CSV string.
    """
    if not complaints_list:
        return ""

    fieldnames = ["complaint_id", "customer_id", "channel", "status", "category", "subcategory", "priority", "urgency", "is_repeat", "is_duplicate", "created_at"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(complaints_list)
    return output.getvalue()
