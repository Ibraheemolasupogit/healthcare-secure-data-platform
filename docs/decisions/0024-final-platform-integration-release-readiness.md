# ADR 0024: Final platform integration and local release-readiness

## Status

Accepted

## Context

The repository now contains local implementations, blueprints and simulations
across healthcare sources, interoperability, Snowflake, dbt, Airflow, Dataiku,
feature store, Fabric/Power BI, governance, deployment, recovery and operations.
The final milestone must prove those assets form one coherent platform without
inventing live evidence or introducing another technology domain.

## Decision

Create a metadata-first portfolio layer that owns golden-path validation,
capability and technology matrices, ownership consolidation, evidence indexing,
claim validation, and local v1.0 release-readiness evidence.

The release status is portfolio-oriented and local. It does not create a GitHub
release, deploy infrastructure, connect to cloud services, claim production
readiness, claim compliance, claim clinical validation or claim live resilience.

## Consequences

Reviewers get a single entry point for the platform story and evidence. Future
live deployment work must be explicitly authorised in a later milestone with
real environment, identity, monitoring, routing and data-protection decisions.
