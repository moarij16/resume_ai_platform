# ATS Resume Scanner

Production-grade modular ATS (Applicant Tracking System) resume scanner with two modes:

- **Mode 1:** Resume vs Job Description matching (ATS compatibility score)
- **Mode 2:** Standalone resume quality analysis (ATS optimization report)

## Requirements

- Python 3.9+
- See `requirements.txt` for dependencies

## Setup

From the **repository root** (parent of `ats_scanner`):

```bash
pip install -r ats_scanner/requirements.txt
python -m spacy download en_core_web_md
```

Or from inside `ats_scanner`:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

## Usage

Run from the **repository root** so the `ats_scanner` package is found:

### Mode 1: ATS Matching (Resume vs Job Description)

```bash
python -m ats_scanner.main --resume path/to/resume.pdf --jd "Python developer with AWS and Docker experience"
```

With a job description file:

```bash
python -m ats_scanner.main --resume resume.pdf --jd job_description.txt
```

### Mode 2: Quality Analysis (Resume Only)

```bash
python -m ats_scanner.main --resume path/to/resume.pdf
```

### Options

| Option | Description |
|--------|-------------|
| `--resume PATH` | Path to resume (PDF or DOCX) |
| `--jd TEXT or PATH` | Job description as text or path to file |
| `--format {text\|json\|html}` | Output format (default: text) |
| `--output PATH` | Write results to file |
| `--verbose` | Enable verbose logging |
| `--resume-dir PATH` | Batch: process all PDF/DOCX in directory |
| `--output-dir PATH` | Batch: directory for result files |

### Examples

```bash
# JSON output to file
python -m ats_scanner.main --resume resume.pdf --jd jd.txt --format json --output results.json

# HTML report
python -m ats_scanner.main --resume resume.pdf --format html --output report.html

# Batch process
python -m ats_scanner.main --resume-dir ./resumes/ --jd job_post.txt --output-dir ./results/ --format json
```

## Project Structure

```
ats_scanner/
├── main.py                 # CLI entry point
├── config.py               # Configuration and constants
├── parsers/                # PDF/DOCX extraction
├── processors/             # NLP, skills, contacts
├── analyzers/              # Sections, format, content, experience
├── engines/                # Similarity and ATS scoring
├── models/                 # Mode 2 quality analysis
├── utils/                  # Logging and output formatting
└── data/                   # Skills taxonomy, action verbs, keywords
```

## Data Files

- **data/skills_taxonomy.json** — 100+ skills with synonyms and categories (programming languages, frameworks, databases, cloud/DevOps, tools, soft skills).
- **data/action_verbs.json** — Strong action verbs by category (leadership, achievement, technical, analysis, communication, improvement, management).
- **data/ats_keywords.json** — Industry-related keywords for software, data, product/project management.

## Context-aware skill extraction

Resume analysis uses **section-weighted** skill extraction:

- **Section weights:** Experience 3×, Skills 2×, Education 1× (other sections 1×).
- **Context:** Each skill is tied to where it appears (e.g. job title, company, project).
- **Proficiency:** Phrases like "expert in", "proficient with", "familiar with" are detected.
- **Estimated years:** Years of experience per skill are inferred from date ranges in the Experience section.

JSON output includes a **`skills_detail`** / **`skills`** object per skill, for example:

```json
"Python": {
  "mentions": 5,
  "contexts": ["Senior Developer at Acme", "ML Project"],
  "estimated_years": 4,
  "proficiency_signals": ["advanced", "expert"],
  "weighted_score": 8.5
}
```

Use `extract_skills_context_aware(resume_text)` in code for this format; `extract_skills()` remains for simple/JD-only extraction.

## Scoring

### Mode 1 (Resume vs JD)

- **ATS Score** = 40% Skill Match + 25% Keyword (TF-IDF) + 25% Semantic Similarity + 10% Experience Relevance.

### Mode 2 (Resume Quality)

- **Quality Score** = 20% Section Completeness + 20% Keyword Strength + 20% Bullet Quality + 15% Format Compatibility + 15% Content Quantification + 10% Resume Length.

## New features (no external APIs)

- **Multi-word phrase detection:** "Machine Learning", "React Native", tech stacks (MERN → MongoDB, Express, React, Node), certifications (e.g. AWS Certified Solutions Architect) via `data/multiword_skills.json`.
- **Multi-tier skill matching:** Exact (1.0), synonym (~0.95), related via embeddings (~0.7–0.9).
- **Experience relevance:** Title match vs JD, recency decay, career progression (junior → senior).
- **Section-weighted scoring:** Experience 1.0, Projects 0.9, Skills 0.6, Education 0.5 (`config.yaml` or `config.py`).
- **Keyword density:** Optimal 2–3%, over-stuffing flag, safe locations to add keywords (`keyword_density` in JSON).
- **Actionable recommendations:** Severity (CRITICAL/HIGH/MEDIUM/LOW), specific actions and estimated impact (e.g. +12% ATS).
- **Achievement pattern detection:** Percentage, dollar, time, scale and impact verbs in bullets.
- **Synonym/acronym expansion:** `data/synonyms_acronyms.json` (ML→Machine Learning, K8s→Kubernetes, etc.).
- **Industry benchmarks:** `data/benchmarks/` (software_engineer, data_scientist, product_manager).
- **ATS profiles:** `data/ats_profiles.json` (Workday, Greenhouse, Lever, generic).
- **Config:** Optional `config.yaml` overlay for models and scoring weights (PyYAML).
- **ModelManager:** Singleton loading for spaCy and SentenceTransformer; graceful regex fallback if spaCy fails.
- **Batch ranking:** `--rank` and `--top N` with `--resume-dir` and `--jd`; writes `ranking.txt`.

## License

Use as part of the resume_ai_platform project.
