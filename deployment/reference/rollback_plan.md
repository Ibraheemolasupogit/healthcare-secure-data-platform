# Rollback plan

Automatic rollback is disabled. Rollback requires approval, compatibility review,
evidence capture and post-rollback validation.

- terraform: target `previous_reviewed_plan`, compatibility `state_and_provider_version_review`.
- dbt: target `previous_manifest_checksum`, compatibility `downstream_contract_review`.
- airflow: target `previous_dag_bundle`, compatibility `scheduler_import_validation`.
- dataiku: target `previous_project_bundle`, compatibility `model_output_contract_review`.
- feature_store: target `previous_feature_registry_version`, compatibility `consumer_compatibility_review`.
- fabric_powerbi: target `previous_semantic_model_and_report_bundle`, compatibility `refresh_and_security_review`.
- governance: target `previous_policy_registry_version`, compatibility `policy_gate_review`.
