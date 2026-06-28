# Data classification

| Class | Examples | Default handling |
|---|---|---|
| Public | Published documentation | Open read |
| Internal | Non-sensitive operational metadata | Authenticated workforce |
| Confidential | Cost, quality and internal audit summaries | Need-to-know roles |
| Sensitive health | Pseudonymised clinical and pathway records | Approved purpose, row/policy controls |
| Direct identifier | Name, address, source patient identifier | Isolated vault, tightly restricted |
| Secret | Credentials and private keys | Secret manager only; never in data tables/repo |

Classification is inherited into derived products unless a documented assessment reduces it. Pseudonymised data remains sensitive health data. Anonymisation requires a recorded disclosure-risk assessment and is not achieved merely by removing names. Synthetic records must be labelled synthetic and must not be derived from a real person.

Future dbt metadata and Snowflake tags will carry classification, owner, retention and allowed-use attributes. CI will fail published models missing required metadata.

Milestone 14 reconciles these classes into `governance/registry/classifications.yaml` and
maps them to controlled sensitivity levels. The mapping is static metadata only and does
not claim live Purview or Snowflake label application.
