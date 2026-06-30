# Disaster-recovery boundaries

Recovery design is metadata and local simulation only. Terraform ownership remains with
Milestone 3, deployment promotion and rollback governance remain with Milestone 15, and
governance policy semantics remain with Milestone 14.

Recovery runbooks may reference these controls but must not create duplicate Terraform
roots, live replication resources, Kubernetes deployments, DNS failover or production
incident automation.

