# FinPilot — Personal Finance Decision Support Agent

FinPilot is a full-stack Python + HTML/CSS/JavaScript prototype that turns transaction data into understandable financial signals.

## Core features

- CSV transaction upload
- Automatic transaction categorization
- Monthly income / expense / savings summary
- Spending-by-category visualization
- Recurring payment and subscription detection
- Explainable unusual-spending detection
- Budget tracking
- Financial goal tracking
- Month-over-month category comparison
- Natural-language decision-support assistant
- Responsive modern dashboard
- SQLite local database

## Important scope

This project is a **decision-support prototype**, not a financial-advice system. It does not provide investment, tax, lending, insurance or other regulated financial recommendations.

The assistant is intentionally explainable and local: it answers supported questions using the user's transaction data and deterministic analytics rather than pretending to be a general financial adviser.

## CSV format

Required columns:

```csv
date,description,amount
2026-09-18,Amazon Shopping,2499
```

Optional columns:

```csv
date,description,amount,type,category
```

`type` can be `income` or `expense`.

## Run in VS Code

### 1. Open the project folder

```bash
cd finpilot
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
python app.py
```

Open:

`http://127.0.0.1:5000`

The first run automatically creates `finpilot.db` and loads safe demo data.

## Project architecture

Browser UI → Flask REST API → SQLite → Analytics engine → Dashboard / Assistant

## Suggested future production upgrades

- Bank/open-banking connectors
- Authentication and encrypted storage
- PostgreSQL
- Background job processing
- More robust recurring-payment detection using transaction intervals
- ML anomaly detection
- LLM/RAG layer with strict financial-data grounding
- Audit logs and permission controls
- Deployment behind HTTPS
