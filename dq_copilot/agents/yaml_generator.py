"""YAML generator for dbt-style test files."""

from typing import List, Dict, Any
import yaml


class YamlGenerator:
    """Agent responsible for generating dbt test YAML files."""
    
    def generate(
        self,
        table_name: str,
        tests: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        """
        Generate a dbt-style tests YAML file.
        
        Args:
            table_name: Name of the table
            tests: List of test dictionaries from TestGeneratorAgent
            output_path: Path to write the YAML file
        """
        # Group tests by column
        tests_by_column = {}
        for test in tests:
            col = test["column"]
            if col not in tests_by_column:
                tests_by_column[col] = []
            tests_by_column[col].append(test)
        
        # Build dbt YAML structure
        columns = []
        for col_name, col_tests in tests_by_column.items():
            column_def = {
                "name": col_name,
                "tests": []
            }
            
            for test in col_tests:
                test_def = self._format_test(test)
                column_def["tests"].append(test_def)
            
            columns.append(column_def)
        
        dbt_yaml = {
            "version": 2,
            "models": [
                {
                    "name": table_name,
                    "columns": columns
                }
            ]
        }
        
        # Write to file
        with open(output_path, "w") as f:
            yaml.dump(
                dbt_yaml,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
    
    def _format_test(self, test: Dict[str, Any]) -> Any:
        """
        Format a test for dbt YAML.
        
        Args:
            test: Test dictionary
            
        Returns:
            Formatted test (string or dict)
        """
        test_type = test["test_type"]
        config = test.get("config", {})
        
        # Simple tests without config
        if not config:
            return test_type
        
        # Tests with config
        return {test_type: config}
