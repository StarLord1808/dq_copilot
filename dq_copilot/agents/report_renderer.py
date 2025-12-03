"""Report renderer agent for terminal output."""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


class ReportRendererAgent:
    """Agent responsible for rendering reports to the terminal."""
    
    def __init__(self):
        """Initialize the report renderer."""
        self.console = Console()
    
    def render(
        self,
        profile: Dict[str, Any],
        issues: List[Dict[str, Any]],
        test_suggestions: Dict[str, Any],
        file_paths: Dict[str, str]
    ) -> None:
        """
        Render a comprehensive report to the terminal.
        
        Args:
            profile: Table profile data
            issues: List of detected issues
            test_suggestions: Test suggestions from LLM
            file_paths: Dictionary of output file paths
        """
        # Table Summary
        self._render_table_summary(profile)
        
        # Detected Issues
        self._render_issues(issues)
        
        # Suggested Tests
        self._render_tests(test_suggestions)
        
        # Output Files
        self._render_file_paths(file_paths)
    
    def _render_table_summary(self, profile: Dict[str, Any]) -> None:
        """Render table summary section."""
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold cyan")
        summary.add_column()
        
        summary.add_row("Table Name:", profile["table_name"])
        summary.add_row("Row Count:", f"{profile['row_count']:,}")
        summary.add_row("Column Count:", str(profile["column_count"]))
        
        panel = Panel(
            summary,
            title="[bold]📊 Table Summary[/bold]",
            border_style="blue"
        )
        self.console.print(panel)
        self.console.print()
    
    def _render_issues(self, issues: List[Dict[str, Any]]) -> None:
        """Render detected issues section."""
        if not issues:
            self.console.print("[green]✓ No data quality issues detected[/green]\n")
            return
        
        # Group by severity
        severity_order = {"error": 0, "warning": 1, "info": 2}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x["severity"], 3))
        
        table = Table(title="[bold]⚠️  Detected Issues[/bold]", show_header=True)
        table.add_column("Severity", style="bold")
        table.add_column("Column", style="cyan")
        table.add_column("Issue Type")
        table.add_column("Details")
        
        severity_styles = {
            "error": "red",
            "warning": "yellow",
            "info": "blue"
        }
        
        for issue in sorted_issues:
            severity_style = severity_styles.get(issue["severity"], "white")
            table.add_row(
                f"[{severity_style}]{issue['severity'].upper()}[/{severity_style}]",
                issue["column"],
                issue["issue_type"],
                issue["details"]
            )
        
        self.console.print(table)
        self.console.print()
    
    def _render_tests(self, test_suggestions: Dict[str, Any]) -> None:
        """Render suggested tests section."""
        tests = test_suggestions.get("tests", [])
        
        if not tests:
            self.console.print("[yellow]⚠ No tests suggested[/yellow]\n")
            return
        
        # Count tests by type
        test_counts = {}
        for test in tests:
            test_type = test["test_type"]
            test_counts[test_type] = test_counts.get(test_type, 0) + 1
        
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold")
        summary.add_column(style="green")
        
        summary.add_row("Total Tests:", str(len(tests)))
        summary.add_row("Description:", test_suggestions.get("description", "N/A"))
        summary.add_row("", "")
        summary.add_row("Tests by Type:", "")
        
        for test_type, count in sorted(test_counts.items()):
            summary.add_row(f"  • {test_type}:", str(count))
        
        panel = Panel(
            summary,
            title="[bold]✅ Suggested Tests[/bold]",
            border_style="green"
        )
        self.console.print(panel)
        self.console.print()
    
    def _render_file_paths(self, file_paths: Dict[str, str]) -> None:
        """Render output file paths section."""
        paths = Table.grid(padding=(0, 2))
        paths.add_column(style="bold magenta")
        paths.add_column(style="dim")
        
        if "profile" in file_paths:
            paths.add_row("Profile JSON:", file_paths["profile"])
        if "tests" in file_paths:
            paths.add_row("Tests YAML:", file_paths["tests"])
        
        panel = Panel(
            paths,
            title="[bold]📁 Output Files[/bold]",
            border_style="magenta"
        )
        self.console.print(panel)
