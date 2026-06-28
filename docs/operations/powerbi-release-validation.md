# Power BI release validation

Release validation must confirm:

- semantic metadata validates locally;
- reports remain thin;
- visual accessibility metadata exists;
- measures and KPIs resolve;
- RLS and OLS objects resolve;
- refresh policies are controlled;
- no credentials or real identities are present;
- no raw-source references or duplicated business logic exist;
- local reference checksums match.

The release remains blocked until live tenant-specific validation is performed in a later
deployment milestone.
