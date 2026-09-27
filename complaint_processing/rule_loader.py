# complaint_processing/rule_loader.py
# Module for dynamically loading and querying the Complaint Resolution Rule Matrix from CSV/SQLite.
# Enforces Hard Rules 1 & 3: Rules and thresholds live in configuration, never in Python code or GenAI prompts.

import os
import csv
from typing import List, Dict, Any, Optional
from database.db import execute_query, execute_statement

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV_PATH = os.path.join(BASE_DIR, "complaint_rules", "resolution_rules.csv")

class RuleMatrixLoader:
    """
    Loads and caches the business rule matrix from CSV file.
    Dynamically inspects CSV headers to accommodate new rule attributes without code changes.
    """
    def __init__(self, csv_path: str = DEFAULT_CSV_PATH):
        self.csv_path = csv_path
        self.rules: List[Dict[str, Any]] = []
        self.load_rules()

    def load_rules(self) -> List[Dict[str, Any]]:
        """
        Dynamically inspects CSV headers, parses values into appropriate data types, and caches rules.
        """
        if not os.path.exists(self.csv_path):
            # Fallback to database rules table if CSV file is absent
            rows = execute_query("SELECT * FROM rules")
            self.rules = [dict(r) for r in rows]
            return self.rules

        parsed_rules = []
        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []

            for row in reader:
                rule_dict = {}
                for h in headers:
                    val = row.get(h, "").strip()
                    # Convert numeric fields dynamically
                    if h in ["max_refund", "max_compensation"]:
                        try:
                            rule_dict[h] = float(val) if val else 0.0
                        except ValueError:
                            rule_dict[h] = 0.0
                    elif h in ["mandatory_escalation", "follow_up_required"]:
                        try:
                            rule_dict[h] = int(val) if val else 0
                        except ValueError:
                            rule_dict[h] = 0
                    else:
                        rule_dict[h] = val
                parsed_rules.append(rule_dict)

        self.rules = parsed_rules
        return self.rules

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Returns all cached rules."""
        return self.rules

    def find_rule(self, category: str, subcategory: str = "") -> Optional[Dict[str, Any]]:
        """
        Finds the matching rule for a given category and subcategory.
        First attempts exact match on (category, subcategory).
        If no exact match exists, attempts fuzzy match on subcategory within the same category.
        Returns None if no confident match is found (never guesses arbitrary category rules).
        """
        import difflib
        import re

        category_clean = category.strip().lower()
        subcategory_clean = subcategory.strip().lower()

        category_rules = []
        for rule in self.rules:
            r_cat = (rule.get("category") or rule.get("Category") or "").strip().lower()
            if r_cat == category_clean:
                category_rules.append(rule)

        if not category_rules:
            return None

        # 1. Exact match on subcategory
        for rule in category_rules:
            r_sub = (rule.get("subcategory") or rule.get("Subcategory") or "").strip().lower()
            if r_sub == subcategory_clean:
                rule_copy = dict(rule)
                rule_copy["is_fallback_match"] = False
                return rule_copy

        # 2. Fuzzy match on subcategory within same category
        if subcategory_clean:
            sub_map = {}
            for rule in category_rules:
                r_sub = (rule.get("subcategory") or rule.get("Subcategory") or "").strip().lower()
                if r_sub and r_sub not in sub_map:
                    sub_map[r_sub] = rule

            choices = list(sub_map.keys())
            matches = difflib.get_close_matches(subcategory_clean, choices, n=1, cutoff=0.5)

            # Word overlap check as fallback fuzzy match
            if not matches:
                sub_words = set(re.findall(r'\w+', subcategory_clean))
                best_score = 0
                best_sub = None
                for choice in choices:
                    choice_words = set(re.findall(r'\w+', choice))
                    overlap = len(sub_words & choice_words)
                    if overlap > 0 and overlap > best_score:
                        best_score = overlap
                        best_sub = choice
                if best_sub and best_score >= 1:
                    matches = [best_sub]

            if matches:
                matched_rule = dict(sub_map[matches[0]])
                matched_rule["is_fallback_match"] = True
                return matched_rule

        return None

# Global instance for rule access across the app
RULE_LOADER = RuleMatrixLoader()
