"""Test generator agent using LLM for intelligent test suggestions."""

import json
import os
from typing import Dict, Any, List, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class TestGeneratorAgent:
    """Agent responsible for generating test suggestions using LLM."""
    
    SYSTEM_PROMPT = """You are a data quality expert helping generate dbt-style tests for database tables.

Given a table profile and detected data quality issues, suggest appropriate tests.

**Allowed test types:**
- not_null: Column should not contain null values
- unique: Column values should be unique
- accepted_values: Column should only contain specific values
- relationships: Column should reference values in another table
- expect_column_values_to_be_between: Numeric column should be within a range
- expect_column_values_to_match_regex: Column should match a pattern
- expect_column_mean_to_be_between: Column mean should be within a range

**Response format (strict JSON):**
{
  "description": "Brief summary of the test strategy",
  "tests": [
    {
      "column": "column_name",
      "test_type": "not_null",
      "config": {}
    }
  ]
}

**Guidelines:**
1. Prioritize tests for detected issues
2. Add not_null tests for columns with low null rates
3. Add unique tests for ID columns
4. Add range tests for numeric columns based on observed min/max
5. Keep config simple and practical
6. Suggest 3-10 tests per table
"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the test generator.
        
        Args:
            api_key: OpenAI API key (if None, will try to use env var or fallback mode)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            print("Using OpenAI API for test generation")
            self.client = OpenAI(api_key=self.api_key)
    
    def generate(
        self,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate test suggestions based on profile and issues.
        
        Args:
            profile: Table profile from ProfilerAgent
            issues: List of detected issues from AnomalyDetectorAgent
            
        Returns:
            Dictionary with 'description' and 'tests' list
        """
        # Try LLM generation first
        if self.client:
            try:
                return self._generate_with_llm(profile, issues)
            except Exception as e:
                print(f"Warning: LLM generation failed ({str(e)}), falling back to rule-based")
        
        # Fallback to rule-based generation
        return self._generate_fallback(profile, issues)
    
    def _generate_with_llm(
        self,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate tests using LLM.
        
        Args:
            profile: Table profile
            issues: Detected issues
            
        Returns:
            Test suggestions dictionary
        """
        # Build user prompt
        user_prompt = self._build_user_prompt(profile, issues)
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        # Validate and filter tests
        validated_tests = self._validate_tests(result.get("tests", []), profile)
        
        return {
            "description": result.get("description", "LLM-generated test suggestions"),
            "tests": validated_tests
        }
    
    def _build_user_prompt(
        self,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> str:
        """Build the user prompt for LLM."""
        prompt_parts = [
            f"Table: {profile['table_name']}",
            f"Rows: {profile['row_count']}",
            f"Columns: {profile['column_count']}",
            "\n**Column Profiles:**"
        ]
        
        for col in profile['columns']:
            col_info = [
                f"- {col['name']} ({col['dtype']})",
                f"  - Null: {col['null_pct']:.1%}",
                f"  - Distinct: {col['distinct_count']} ({col['distinct_pct']:.1%})"
            ]
            if 'min' in col and 'max' in col:
                col_info.append(f"  - Range: [{col['min']}, {col['max']}]")
            prompt_parts.extend(col_info)
        
        if issues:
            prompt_parts.append("\n**Detected Issues:**")
            for issue in issues:
                prompt_parts.append(
                    f"- {issue['column']}: {issue['issue_type']} ({issue['severity']}) - {issue['details']}"
                )
        
        return "\n".join(prompt_parts)
    
    def _validate_tests(
        self,
        tests: List[Dict[str, Any]],
        profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validate and filter test suggestions.
        
        Args:
            tests: Raw test suggestions from LLM
            profile: Table profile for validation
            
        Returns:
            Validated tests
        """
        valid_test_types = {
            "not_null", "unique", "accepted_values", "relationships",
            "expect_column_values_to_be_between", "expect_column_values_to_match_regex",
            "expect_column_mean_to_be_between"
        }
        
        column_names = {col["name"] for col in profile["columns"]}
        validated = []
        
        for test in tests:
            # Check required fields
            if "column" not in test or "test_type" not in test:
                continue
            
            # Check column exists
            if test["column"] not in column_names:
                continue
            
            # Check test type is allowed
            if test["test_type"] not in valid_test_types:
                continue
            
            # Ensure config exists
            if "config" not in test:
                test["config"] = {}
            
            validated.append(test)
        
        return validated
    
    def _generate_fallback(
        self,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate basic tests without LLM (fallback mode).
        
        Args:
            profile: Table profile
            issues: Detected issues
            
        Returns:
            Basic test suggestions
        """
        tests = []
        
        # Generate tests based on issues
        for issue in issues:
            if issue["issue_type"] == "non_unique_id":
                tests.append({
                    "column": issue["column"],
                    "test_type": "unique",
                    "config": {}
                })
            elif issue["issue_type"] == "high_null_rate":
                # Don't add not_null for high null columns
                pass
        
        # Add not_null tests for low-null columns
        for col in profile["columns"]:
            if col["null_pct"] < 0.05:  # Less than 5% nulls
                tests.append({
                    "column": col["name"],
                    "test_type": "not_null",
                    "config": {}
                })
        
        return {
            "description": "Rule-based test suggestions (LLM unavailable)",
            "tests": tests
        }
