"""CLI interface for Data Quality Copilot."""

import json
import os
from pathlib import Path

import click
from rich.console import Console

from dq_copilot.agents import (
    TableLoaderAgent,
    ProfilerAgent,
    AnomalyDetectorAgent,
    TestGeneratorAgent,
    YamlGenerator,
    ReportRendererAgent,
)

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Data Quality Copilot - Profile tables and generate dbt tests."""
    pass


@main.command()
@click.option(
    "--table-path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the table file (CSV or Parquet)",
)
@click.option(
    "--table-name",
    required=True,
    help="Name of the table",
)
@click.option(
    "--output-dir",
    default=".",
    type=click.Path(),
    help="Directory to write output files (default: current directory)",
)
def profile(table_path: str, table_name: str, output_dir: str):
    """Profile a table and generate statistics."""
    try:
        console.print(f"[bold blue]Loading table from {table_path}...[/bold blue]")
        
        # Load table
        loader = TableLoaderAgent()
        df, metadata = loader.load(table_path, table_name)
        
        console.print(f"[green]✓[/green] Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Profile table
        console.print("[bold blue]Profiling table...[/bold blue]")
        profiler = ProfilerAgent()
        profile_data = profiler.profile(df, table_name)
        
        # Write profile to file
        output_path = Path(output_dir) / f"{table_name}_profile.json"
        with open(output_path, "w") as f:
            json.dump(profile_data, f, indent=2, default=str)
        
        console.print(f"[green]✓[/green] Profile written to {output_path}")
        
        # Print summary
        console.print("\n[bold]Profile Summary:[/bold]")
        console.print(f"  Table: {table_name}")
        console.print(f"  Rows: {profile_data['row_count']}")
        console.print(f"  Columns: {len(profile_data['columns'])}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@main.command()
@click.option(
    "--table-path",
    required=True,
    type=click.Path(exists=True),
    help="Path to the table file (CSV or Parquet)",
)
@click.option(
    "--table-name",
    required=True,
    help="Name of the table",
)
@click.option(
    "--output-dir",
    default=".",
    type=click.Path(),
    help="Directory to write output files (default: current directory)",
)
@click.option(
    "--api-key",
    envvar="OPENAI_API_KEY",
    help="OpenAI API key (or set OPENAI_API_KEY env var)",
)
def run(table_path: str, table_name: str, output_dir: str, api_key: str):
    """Run full data quality analysis with test generation."""
    try:
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        tests_dir = output_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Load table
        console.print(f"[bold blue]Loading table from {table_path}...[/bold blue]")
        loader = TableLoaderAgent()
        df, metadata = loader.load(table_path, table_name)
        console.print(f"[green]✓[/green] Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Profile table
        console.print("[bold blue]Profiling table...[/bold blue]")
        profiler = ProfilerAgent()
        profile_data = profiler.profile(df, table_name)
        profile_path = output_path / f"{table_name}_profile.json"
        with open(profile_path, "w") as f:
            json.dump(profile_data, f, indent=2, default=str)
        console.print(f"[green]✓[/green] Profile written to {profile_path}")
        
        # Detect anomalies
        console.print("[bold blue]Detecting anomalies...[/bold blue]")
        detector = AnomalyDetectorAgent()
        issues = detector.detect(profile_data)
        console.print(f"[green]✓[/green] Found {len(issues)} potential issues")
        
        # Generate tests
        console.print("[bold blue]Generating test suggestions...[/bold blue]")
        test_generator = TestGeneratorAgent(api_key=api_key)
        test_suggestions = test_generator.generate(profile_data, issues)
        console.print(f"[green]✓[/green] Generated {len(test_suggestions.get('tests', []))} test suggestions")
        
        # Generate YAML
        console.print("[bold blue]Generating dbt tests YAML...[/bold blue]")
        yaml_gen = YamlGenerator()
        yaml_path = tests_dir / f"{table_name}_tests.yml"
        yaml_gen.generate(table_name, test_suggestions.get("tests", []), str(yaml_path))
        console.print(f"[green]✓[/green] Tests written to {yaml_path}")
        
        # Render report
        console.print("\n" + "=" * 80 + "\n")
        renderer = ReportRendererAgent()
        renderer.render(
            profile_data,
            issues,
            test_suggestions,
            {
                "profile": str(profile_path),
                "tests": str(yaml_path),
            },
        )
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


if __name__ == "__main__":
    main()
