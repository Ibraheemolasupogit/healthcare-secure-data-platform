# Pull-request validation

Pull requests remain credential-free. Required checks are represented by Python quality,
dbt structure, documentation/YAML, SQL lint, Terraform validation, secret scan and
deployment controls.

PR jobs use least-privilege GitHub permissions and must not use `pull_request_target`,
cloud credentials, production secrets, Terraform apply or live platform deployment.

