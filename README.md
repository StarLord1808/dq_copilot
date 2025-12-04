# Data Quality Copilot CLI 🤖✨

A command-line AI assistant that profiles tables, detects data quality issues, and auto-suggests dbt-style tests.

Think of it as a linting engine for your data — part spellchecker, part judgmental analyst, and slightly more useful than the average unsolicited LinkedIn advice.

## Why This Exists 😫

Good analytics and ML depend on clean data. Unfortunately, writing data quality checks by hand ranks somewhere between watching paint dry and debugging CSV encodings as a hobby.

This tool automates the dreary bits by:

- **Profiling** your tables (no more manual eyeballing CSVs)
- **Detecting** anomalies using heuristics + an LLM assist
- **Suggesting** actionable fixes instead of vague doom messages
- **Generating** dbt-style tests automatically (yes, even the YAML)
- **Outputting** everything neatly for copy-paste or CI runs

## Architecture 🏗️

This is more than a script — it's a tiny guild of specialized agents quietly judging your datasets.

```
┌─────────────┐
│   CLI       │  The Executive
└──────┬──────┘
       │
       ├──► TableLoaderAgent
       ├──► ProfilerAgent
       ├──► AnomalyDetectorAgent
       ├──► TestGeneratorAgent
       ├──► YamlGenerator
       └──► ReportRendererAgent
```

### Agent Roles

- **TableLoaderAgent**: Eats CSV, Parquet, etc. Handles encodings without emotional breakdowns.
- **ProfilerAgent**: Calculates stats, distributions, nulls, distinct counts — the accounting department.
- **AnomalyDetectorAgent**: Sherlock Holmes for data messiness:
  - Null swamps
  - Duplicate IDs
  - Boring constant columns
  - Negative numbers pretending they belong
- **TestGeneratorAgent**: Uses GPT to generate human-grade recommendations and dbt tests.
- **ReportRendererAgent**: Pretty terminal output because aesthetics matter.

## Setup 🛠️

### Prerequisites

- Python 3.8+
- OpenAI API Key (recommended unless you love rule engines)
- Coffee ☕ (optional but statistically correlated with productivity)

### Installation

```bash
cd /home/jiraiya/codebase/ai-agent/dq-copilot
python3 -m venv venv
source venv/bin/activate
pip install -e .
export OPENAI_API_KEY="your-key-here"
```

## Usage 🚀

### Profile Mode — Stats Only

```bash
dq-copilot profile --table-path examples/orders.csv --table-name orders
```

**Produces:** `orders_profile.json`

### Full Run — Profiling + AI Insights + Tests

```bash
dq-copilot run --table-path examples/orders.csv --table-name orders
```

**Outputs:**
- `orders_profile.json`
- `tests/orders_tests.yml`

### Flags

```
--table-path PATH    File location
--table-name NAME    Logical table name
--output-dir DIR     Output destination
--api-key KEY        LLM key
```

## Example Demo 🍿

A deliberately messy sample (`examples/orders.csv`) is available. Running the tool gives a structured output summarizing issues, priorities, suggested actions, and dbt tests — like a performance review, except useful.

**Example highlights:**
- Unique ID failures flagged as **CRITICAL**
- Null explosions flagged as **HIGH**
- Negative values politely interrogated

Reports include remediation steps and generated dbt tests (`not_null`, `unique`, ranges, etc.).

## Configuration ⚙️

### LLM Integration

Defaults to OpenAI GPT-4. Without a key, the tool falls back to rule-based analysis — functional, but a bit rotary-phone-in-smartphone-world.

### Thresholds

Customizable heuristics:

```python
AnomalyDetectorAgent(
    high_null_threshold=0.3,
    constant_threshold=1,
    id_uniqueness_threshold=1.0
)
```

## Dependencies 📦

- `click` — CLI framework
- `pandas` — Data wrangler's Swiss army knife
- `pyarrow` — Parquet support
- `openai` — AI brainpower
- `pyyaml` — dbt output whisperer
- `rich` — Pretty output, because CLI doesn't have to be sad

## Development 💻

```bash
pip install -e ".[dev]"
pytest
black dq_copilot/
ruff check dq_copilot/
```

## License 📜

MIT — experiment, extend, or creatively destroy. Just don't blame us for philosophical crises induced by bad data.

---

*Built with caffeine, curiosity, and an unreasonable love for well-behaved datasets.*