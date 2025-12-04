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
        self._render_table_summary(profile, issues)
        
        # Quick Win Summary
        self._render_quick_win_summary(issues)
        
        # Detected Issues
        self._render_issues(issues)
        
        # Suggested Tests
        self._render_tests(test_suggestions)
        
        # Output Files
        self._render_file_paths(file_paths)
    
    def _render_table_summary(self, profile: Dict[str, Any], issues: List[Dict[str, Any]]) -> None:
        """Render table summary section."""
        # Calculate a simple health score
        total_checks = profile["column_count"] * 4  # Rough estimate of checks per column
        issue_count = len(issues)
        health_score = max(0, min(10, 10 - (issue_count / max(1, profile["column_count"])) * 2))
        
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold cyan")
        summary.add_column()
        
        summary.add_row("Table Name:", profile["table_name"])
        summary.add_row("Row Count:", f"{profile['row_count']:,}")
        summary.add_row("Column Count:", str(profile["column_count"]))
        summary.add_row("Health Score:", f"{health_score:.1f}/10")
        
        panel = Panel(
            summary,
            title="[bold]📊 Table Summary[/bold]",
            border_style="blue"
        )
        self.console.print(panel)
        self.console.print()

    def _render_quick_win_summary(self, issues: List[Dict[str, Any]]) -> None:
        """Render a quick summary of issues by priority."""
        if not issues:
            return

        priority_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in issues:
            priority = issue.get("priority", "MEDIUM").upper()
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold")
        summary.add_column()
        
        summary.add_row("🎯 Quick Assessment:", f"{len(issues)} issues found")
        
        if priority_counts["CRITICAL"] > 0:
            summary.add_row("   • [red]CRITICAL:[/red]", f"{priority_counts['CRITICAL']} need immediate attention")
        if priority_counts["HIGH"] > 0:
            summary.add_row("   • [yellow]HIGH:[/yellow]", f"{priority_counts['HIGH']} important issues")
        if priority_counts["MEDIUM"] > 0:
            summary.add_row("   • [blue]MEDIUM:[/blue]", f"{priority_counts['MEDIUM']} warnings")
        if priority_counts["LOW"] > 0:
            summary.add_row("   • [dim]LOW:[/dim]", f"{priority_counts['LOW']} minor/info items")

        self.console.print(Panel(summary, border_style="dim"))
        self.console.print()
    
    def _render_issues(self, issues: List[Dict[str, Any]]) -> None:
        """Render detected issues section."""
        if not issues:
            self.console.print("[green]✓ No data quality issues detected[/green]\n")
            return
        
        # Group by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_issues = sorted(issues, key=lambda x: priority_order.get(x.get("priority", "MEDIUM").upper(), 4))
        
        table = Table(title="[bold]⚠️  Detected Issues (Prioritized)[/bold]", show_header=True, expand=True)
        table.add_column("Priority", style="bold", width=10)
        table.add_column("Column", style="cyan", width=15)
        table.add_column("Issue & Impact", ratio=2)
        table.add_column("Action", ratio=1)
        
        priority_styles = {
            "CRITICAL": "bold red",
            "HIGH": "yellow",
            "MEDIUM": "blue",
            "LOW": "dim white"
        }
        
        for issue in sorted_issues:
            priority = issue.get("priority", "MEDIUM").upper()
            style = priority_styles.get(priority, "white")
            
            # Combine details for richer display
            issue_desc = f"[bold]{issue['issue_type']}[/bold]\n{issue['details']}"
            if "justification" in issue:
                issue_desc += f"\n[dim]Why: {issue['justification']}[/dim]"
            if "impact_description" in issue:
                issue_desc += f"\n[italic red]Impact: {issue['impact_description']}[/italic red]"
            if "example" in issue:
                issue_desc += f"\n[dim]Ex: {issue['example']}[/dim]"
            
            action = issue.get("action_recommendation", "Investigate issue")
            
            table.add_row(
                f"[{style}]{priority}[/{style}]",
                issue["column"],
                issue_desc,
                action
            )
        
        self.console.print(table)
        self.console.print()
        
        # Next Steps
        self._render_next_steps(sorted_issues)

    def _render_next_steps(self, issues: List[Dict[str, Any]]) -> None:
        """Render recommended next steps."""
        steps = Table.grid(padding=(0, 2))
        steps.add_column(style="bold")
        steps.add_column()
        
        steps.add_row("🚀 Recommended Actions:", "")
        
        count = 1
        # Add specific actions for top issues
        for issue in issues[:3]:
            action = issue.get("action_recommendation", f"Fix {issue['issue_type']} in {issue['column']}")
            steps.add_row(f"   {count}.", f"{action} (Priority: {issue.get('priority', 'MEDIUM')})")
            count += 1
            
        steps.add_row(f"   {count}.", "Run the generated dbt tests to enforce quality rules")
        steps.add_row(f"   {count+1}.", "Schedule a follow-up scan after data remediation")
        
        self.console.print(Panel(steps, border_style="green"))
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
