# Entity relationships

```mermaid
erDiagram
    ORGANISATIONS ||--o{ LOCATIONS : owns
    ORGANISATIONS ||--o{ PROVIDERS : employs
    ORGANISATIONS ||--o{ PATIENTS : registers
    PATIENTS ||--o{ ENCOUNTERS : attends
    ORGANISATIONS ||--o{ ENCOUNTERS : delivers
    LOCATIONS ||--o{ ENCOUNTERS : hosts
    PROVIDERS ||--o{ ENCOUNTERS : leads
    ENCOUNTERS ||--o| ADMISSIONS : includes
    ADMISSIONS o|--o{ ADMISSIONS : prior_readmission
    PATIENTS ||--o{ APPOINTMENTS : books
    LOCATIONS ||--o{ APPOINTMENTS : schedules
    PROVIDERS ||--o{ APPOINTMENTS : assigned
    CLINICAL_EVENTS ||--o| APPOINTMENTS : referral
    PATIENTS ||--o{ PATHWAYS : follows
    ORGANISATIONS ||--o{ PATHWAYS : manages
    ENCOUNTERS ||--o{ CLINICAL_EVENTS : contains
    PROVIDERS ||--o{ CLINICAL_EVENTS : records
    ENCOUNTERS ||--o{ PATHOLOGY_RESULTS : requests
    PROVIDERS ||--o{ PATHOLOGY_RESULTS : requests
    ORGANISATIONS ||--o{ PATHOLOGY_RESULTS : processes
    ENCOUNTERS ||--o{ MEDICATION_EVENTS : contains
    PATIENTS ||--o{ RESEARCH_CONSENT : decides
    PATIENTS ||--o{ RESEARCH_COHORTS : joins
```

Audit events reference synthetic platform actors and object labels rather than foreign keys to clinical entities. Data-quality events identify the affected dataset and synthetic record through a generic reference so deliberately malformed negative fixtures can still be described.
