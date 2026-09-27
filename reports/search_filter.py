# reports/search_filter.py
# Module for searching and multi-criteria filtering of complaints and analysis results in SQLite.

from typing import List, Dict, Any, Optional
from database.db import execute_query

def search_and_filter_complaints(
    query_text: Optional[str] = None,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    urgency_filter: Optional[str] = None,
    escalation_only: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Executes a dynamic SQL query to filter complaints based on text search, status, category, urgency, and dates.
    """
    sql = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if query_text and query_text.strip():
        search_pattern = f"%{query_text.strip()}%"
        sql += " AND (complaint_text LIKE ? OR complaint_id LIKE ? OR customer_id LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    if status_filter and status_filter != "All":
        sql += " AND status = ?"
        params.append(status_filter)

    if category_filter and category_filter != "All":
        sql += " AND category = ?"
        params.append(category_filter)

    if urgency_filter and urgency_filter != "All":
        sql += " AND urgency = ?"
        params.append(urgency_filter)

    if escalation_only:
        sql += " AND (status LIKE 'Escalated%' OR status = 'Manual_Review')"

    if start_date:
        sql += " AND created_at >= ?"
        params.append(f"{start_date} 00:00:00")

    if end_date:
        sql += " AND created_at <= ?"
        params.append(f"{end_date} 23:59:59")

    sql += " ORDER BY created_at DESC"

    rows = execute_query(sql, tuple(params))
    return [dict(r) for r in rows]
