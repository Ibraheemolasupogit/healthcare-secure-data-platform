# Scaling generation

Profiles define approximate relationship density:

| Profile | Patients | Expected character |
|---|---:|---|
| small | 100 | CI/sample, roughly 1,000 total rows |
| medium | 10,000 | local rehearsal, roughly 150,000 total rows |
| large | 1,000,000 | future benchmark, roughly 20 million total rows |

Counts can be overridden. The large profile is configuration only and was not executed. Current generation materialises relationships in memory before deterministic writing; this is comfortable for small and typically medium runs but is a known blocker for the million-patient profile. Depending on string/cardinality, large output could require tens of gigabytes and substantially more transient memory.

Writers already flush CSV and JSON Lines in the profile's deterministic `chunk_size`; relationship generation still materialises records. A future benchmark implementation should partition by stable patient ordinal ranges, derive each partition's stream from seed/domain/partition, write fixed-size chunks atomically, and merge checksum manifests in partition order. Organisation/location/provider dimensions can be shared read-only. Parallel workers must never allocate IDs by completion order. Compression is deliberately deferred.
