"""Anomaly detector agent for identifying data quality issues."""

import json
import os
from typing import Dict, Any, List, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AnomalyDetectorAgent:
    """Agent responsible for detecting data quality anomalies."""
    
    SYSTEM_PROMPT = """You are a data quality expert helping identify anomalies in database tables.

Given a table profile, analyze the statistics and identify potential data quality issues.

**Look for these types of anomalies:**
- high_null_rate: Columns with an unexpectedly high percentage of null values (e.g., > 30%)
- non_unique_id: ID-like columns that are not 100% unique
- constant_column: Columns that have only 1 distinct value
- negative_values: Numeric columns (amount, price, count) that contain negative values
- suspicious_distribution: Columns with unusual statistical properties (e.g., min > max, mean far from median)

**Response format (strict JSON):**
{
  "issues": [
    {
      "column": "column_name",
      "issue_type": "high_null_rate",
      "severity": "warning",
      "priority": "HIGH",
      "details": "Column has 45% null values, which is high for a 'status' column",
      "justification": "Status columns usually track the state of a record and should be populated for active tracking.",
      "impact_description": "Incomplete status tracking may lead to dropped orders or reporting gaps.",
      "action_recommendation": "Investigate upstream ingestion for missing status updates.",
      "example": "Null count: 450/1000 rows",
      "value": 0.45
    }
  ]
}

**Guidelines:**
1. Be conservative with errors, use warnings for suspicious but possible data.
2. Pay attention to column names to infer expected behavior (e.g., 'email' should be unique usually).
3. ID columns should almost always be unique.
4. Return an empty list if no significant anomalies are found.
5. Provide a clear 'justification' for why this is an issue and an 'example' (e.g., specific value or stat).
6. Assign a 'priority' (CRITICAL, HIGH, MEDIUM, LOW) based on potential business impact.
7. Provide a specific 'action_recommendation' and 'impact_description'.
"""
    
    def __init__(
        self,
        high_null_threshold: float = 0.3,
        constant_threshold: int = 1,
        id_uniqueness_threshold: float = 1.0,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the anomaly detector with configurable thresholds.
        
        Args:
            high_null_threshold: Percentage threshold for high null rate (default: 0.3 = 30%)
            constant_threshold: Number of distinct values to consider constant (default: 1)
            id_uniqueness_threshold: Required uniqueness percentage for ID columns (default: 1.0 = 100%)
            api_key: OpenAI API key (if None, will try to use env var or fallback mode)
        """
        self.high_null_threshold = high_null_threshold
        self.constant_threshold = constant_threshold
        self.id_uniqueness_threshold = id_uniqueness_threshold
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            print("Using OpenAI API for anomaly detection")
            self.client = OpenAI(api_key=self.api_key)
    
    def detect(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in a table profile.
        
        Args:
            profile: Table profile dictionary from ProfilerAgent
            
        Returns:
            List of detected issues
        """
        # Try LLM detection first
        if self.client:
            try:
                return self._detect_with_llm(profile)
            except Exception as e:
                print(f"Warning: LLM detection failed ({str(e)}), falling back to rule-based")
        
        # Fallback to rule-based detection
        return self._detect_fallback(profile)
    
    def _detect_with_llm(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect anomalies using LLM.
        
        Args:
            profile: Table profile
            
        Returns:
            List of detected issues
        """
        # Build user prompt
        user_prompt = self._build_user_prompt(profile)
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Lower temperature for more consistent analysis
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        return result.get("issues", [])
    
    def _build_user_prompt(self, profile: Dict[str, Any]) -> str:
        """Build the user prompt for LLM."""
        prompt_parts = [
            f"Table: {profile.get('table_name', 'Unknown')}",
            f"Rows: {profile.get('row_count', 0)}",
            f"Columns: {profile.get('column_count', 0)}",
            "\n**Column Profiles:**"
        ]
        
        for col in profile.get('columns', []):
            col_info = [
                f"- {col['name']} ({col['dtype']})",
                f"  - Null: {col['null_pct']:.1%}",
                f"  - Distinct: {col['distinct_count']} ({col['distinct_pct']:.1%})"
            ]
            if 'min' in col and 'max' in col:
                col_info.append(f"  - Range: [{col['min']}, {col['max']}]")
            if 'mean' in col:
                col_info.append(f"  - Mean: {col['mean']}")
            prompt_parts.extend(col_info)
        
        return "\n".join(prompt_parts)
    
    def _detect_fallback(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect anomalies using rule-based logic (fallback).
        
        Args:
            profile: Table profile dictionary from ProfilerAgent
            
        Returns:
            List of detected issues
        """
        issues = []
        
        for col in profile.get("columns", []):
            # Check for high null rate
            if col["null_pct"] > self.high_null_threshold:
                issues.append({
                    "column": col["name"],
                    "issue_type": "high_null_rate",
                    "severity": "warning",
                    "priority": "HIGH",
                    "details": f"Column has {col['null_pct']:.1%} null values (threshold: {self.high_null_threshold:.1%})",
                    "justification": "High null rates can indicate missing data or broken ingestion pipelines.",
                    "impact_description": "Missing data can lead to incomplete analysis and inaccurate reporting.",
                    "action_recommendation": "Check upstream data sources for missing values or adjust null thresholds.",
                    "example": f"Null count: {int(col['null_pct'] * profile.get('row_count', 0))} rows",
                    "value": col["null_pct"],
                })
            
            # Check for non-unique ID columns
            if self._is_id_column(col["name"]):
                if col["distinct_pct"] < self.id_uniqueness_threshold:
                    issues.append({
                        "column": col["name"],
                        "issue_type": "non_unique_id",
                        "severity": "error",
                        "priority": "CRITICAL",
                        "details": f"ID column is only {col['distinct_pct']:.1%} unique (expected 100%)",
                        "justification": "ID columns are expected to be unique identifiers for each row. Duplicates cause data integrity issues.",
                        "impact_description": "Duplicate IDs can cause double-counting in aggregations and join explosions.",
                        "action_recommendation": "Remove duplicates or investigate why the ID is not unique.",
                        "example": f"Unique count: {col['distinct_count']} vs Row count: {profile.get('row_count', 0)}",
                        "value": col["distinct_pct"],
                    })
            
            # Check for constant columns
            if col["distinct_count"] <= self.constant_threshold:
                issues.append({
                    "column": col["name"],
                    "issue_type": "constant_column",
                    "severity": "info",
                    "priority": "LOW",
                    "details": f"Column has only {col['distinct_count']} distinct value(s)",
                    "justification": "Constant columns provide no information gain and might be redundant.",
                    "impact_description": "Redundant columns waste storage and computation.",
                    "action_recommendation": "Consider removing this column if it's not needed for filtering.",
                    "example": f"Distinct count: {col['distinct_count']}",
                    "value": col["distinct_count"],
                })
            
            # Check for numeric sanity (negative values in amount/count columns)
            if self._is_amount_or_count_column(col["name"]):
                if "min" in col and col["min"] < 0:
                    issues.append({
                        "column": col["name"],
                        "issue_type": "negative_values",
                        "severity": "warning",
                        "priority": "HIGH",
                        "details": f"Column contains negative values (min: {col['min']}) but appears to be an amount/count field",
                        "justification": "Amount and count fields are typically positive. Negative values might indicate data errors or returns.",
                        "impact_description": "Negative values can skew totals and averages.",
                        "action_recommendation": "Verify if negative values are expected (e.g., returns) or data errors.",
                        "example": f"Min value: {col['min']}",
                        "value": col["min"],
                    })
        
        return issues
    
    def _is_id_column(self, col_name: str) -> bool:
        """
        Check if a column name suggests it's an ID field.
        
        Args:
            col_name: Column name to check
            
        Returns:
            True if column appears to be an ID field
        """
        col_lower = col_name.lower()
        id_indicators = ["_id", "id_", "identifier", "key"]
        return any(indicator in col_lower for indicator in id_indicators) or col_lower == "id"
    
    def _is_amount_or_count_column(self, col_name: str) -> bool:
        """
        Check if a column name suggests it's an amount or count field.
        
        Args:
            col_name: Column name to check
            
        Returns:
            True if column appears to be an amount/count field
        """
        col_lower = col_name.lower()
        amount_indicators = [
            "amount", "price", "cost", "total", "sum",
            "count", "quantity", "qty", "number", "num"
        ]
        return any(indicator in col_lower for indicator in amount_indicators)
