# Data Quality Copilot CLI

A CLI AI agent that profiles tables, detects data quality issues, and generates dbt-style tests automatically.

## Problem Statement

Data quality is critical for reliable analytics and ML pipelines. However, manually writing data quality tests is time-consuming and error-prone. This tool automates the process by:

1. **Profiling** tables to understand their structure and statistics
2. **Detecting** common data quality issues using rule-based heuristics
3. **Generating** intelligent test suggestions using LLM
4. **Outputting** dbt-compatible YAML test files

## Architecture

```
┌─────────────┐
│   CLI       │  Click-based command interface
└──────┬──────┘
       │
       ├──► TableLoaderAgent      (Load CSV/Parquet → DataFrame)
       │
       ├──► ProfilerAgent         (Compute column statistics)
       │
       ├──► AnomalyDetectorAgent  (Rule-based issue detection)
       │
       ├──► TestGeneratorAgent    (LLM-powered test suggestions)
       │
       ├──► YamlGenerator         (dbt YAML output)
       │
       └──► ReportRendererAgent   (Terminal report)
```

### Agent Responsibilities

- **TableLoaderAgent**: Loads CSV and Parquet files with error handling
- **ProfilerAgent**: Computes per-column stats (dtype, nulls, distinct count, min/max, examples)
- **AnomalyDetectorAgent**: Detects 4 issue types:
  - High null rate (>30%)
  - Non-unique ID columns
  - Constant columns (≤1 distinct value)
  - Negative values in amount/count fields
- **TestGeneratorAgent**: Uses OpenAI GPT-4 to suggest dbt tests (with rule-based fallback)
- **YamlGenerator**: Transforms suggestions into dbt `version: 2` YAML
- **ReportRendererAgent**: Rich terminal output with tables and colors

## Installation

```bash
cd /home/jiraiya/codebase/ai-agent/dq-copilot
pip install -e .
```

## Usage

### Profile Command (No LLM Required)

Profile a table and generate statistics only:

```bash
dq-copilot profile --table-path examples/orders.csv --table-name orders
```

**Output:**
- `orders_profile.json` - Detailed column statistics

### Run Command (Full Pipeline with LLM)

Run the complete data quality analysis:

```bash
export OPENAI_API_KEY="your-api-key-here"
dq-copilot run --table-path examples/orders.csv --table-name orders
```

**Output:**
- `orders_profile.json` - Column statistics
- `tests/orders_tests.yml` - dbt test file

### Options

```
--table-path PATH    Path to CSV or Parquet file (required)
--table-name NAME    Table name for metadata (required)
--output-dir DIR     Output directory (default: current directory)
--api-key KEY        OpenAI API key (or set OPENAI_API_KEY env var)
```

## Example Demo

The included `examples/orders.csv` dataset contains intentional anomalies:

| Anomaly Type | Column | Issue |
|--------------|--------|-------|
| Non-unique ID | `order_id` | Duplicate value 1001 |
| High null rate | `customer_name` | 40% null values |
| Constant column | `status` | All values are "pending" |
| Negative values | `amount` | Contains -50.00 and -25.00 |

**Run the demo:**

```bash
cd /home/jiraiya/codebase/ai-agent/dq-copilot
dq-copilot run --table-path examples/orders.csv --table-name orders
```

**Expected output:**

```
Loading table from examples/orders.csv...
✓ Loaded 20 rows, 6 columns
Profiling table...
✓ Profile written to orders_profile.json
Detecting anomalies...
✓ Found 4 potential issues
Generating test suggestions...
✓ Generated 6 test suggestions
Generating dbt tests YAML...
✓ Tests written to tests/orders_tests.yml

================================================================================

┌─ 📊 Table Summary ─────────────────────────────────────────────────────────┐
│ Table Name:    orders                                                      │
│ Row Count:     20                                                          │
│ Column Count:  6                                                           │
└────────────────────────────────────────────────────────────────────────────┘

⚠️  Detected Issues
┌──────────┬───────────────┬──────────────────┬─────────────────────────────┐
│ Severity │ Column        │ Issue Type       │ Details                     │
├──────────┼───────────────┼──────────────────┼─────────────────────────────┤
│ ERROR    │ order_id      │ non_unique_id    │ ID column is only 95.0%...  │
│ WARNING  │ customer_name │ high_null_rate   │ Column has 40.0% null...    │
│ WARNING  │ amount        │ negative_values  │ Contains negative values... │
│ INFO     │ status        │ constant_column  │ Column has only 1 distinct..│
└──────────┴───────────────┴──────────────────┴─────────────────────────────┘

┌─ ✅ Suggested Tests ───────────────────────────────────────────────────────┐
│ Total Tests:  6                                                            │
│ Description:  LLM-generated test suggestions                               │
│                                                                            │
│ Tests by Type:                                                             │
│   • not_null:                                3                             │
│   • unique:                                  1                             │
│   • expect_column_values_to_be_between:      2                             │
└────────────────────────────────────────────────────────────────────────────┘

┌─ 📁 Output Files ──────────────────────────────────────────────────────────┐
│ Profile JSON:  orders_profile.json                                         │
│ Tests YAML:    tests/orders_tests.yml                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

## Configuration

### LLM Provider

The tool uses OpenAI GPT-4 by default. Set your API key:

```bash
export OPENAI_API_KEY="sk-..."
```

If no API key is provided, the tool falls back to rule-based test generation (limited but functional).

### Anomaly Detection Thresholds

Thresholds are configurable in the code:

```python
detector = AnomalyDetectorAgent(
    high_null_threshold=0.3,      # 30% null rate
    constant_threshold=1,          # ≤1 distinct value
    id_uniqueness_threshold=1.0    # 100% unique for IDs
)
```

## Dependencies

- `click` - CLI framework
- `pandas` - Data manipulation
- `pyarrow` - Parquet support
- `openai` - LLM integration
- `pyyaml` - YAML generation
- `rich` - Terminal formatting

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (if added)
pytest

# Format code
black dq_copilot/
ruff check dq_copilot/
```

## License

MIT
