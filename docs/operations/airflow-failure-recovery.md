# Airflow failure recovery

Milestone 10 failure callbacks write structured local JSON Lines records under orchestration outputs.

Captured fields include DAG ID, task ID, run ID, logical date, try number, exception class, execution mode, batch ID, timestamp and synthetic flag.

Callbacks do not:

- send email, Slack, Teams, PagerDuty or ticket notifications;
- include secrets;
- include patient-level payloads;
- swallow task failures.

Rerun failed tasks only after the failed contract is corrected. Deterministic validation failures should not be retried indefinitely.
