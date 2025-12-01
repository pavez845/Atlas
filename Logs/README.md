# data/

This folder contains runtime data produced by the app. It is not committed to version control (add to .gitignore if needed).

Files:
- `logs.json`: persistent dump of `interaction_logs` recorded by the agent. Each item is a JSON object with fields:
  - `id`, `timestamp`, `query`, `response`, `metrics`, `error_occurred`, `context_count`, `context_scores`.

Usage:
- The Streamlit dashboard provides a button to save current logs to `data/logs.json` and an uploader to load a JSON file into the session.
- To include logs in your submission, export from the dashboard as CSV or copy `data/logs.json`.
