# Power BI measure catalogue

Measures are centralised in the shared semantic model. Reports may reference measures but
must not create report-local business logic.

Measure groups:

- healthcare operations: appointment count, attended appointment count, attendance rate
  and encounter count;
- billing and finance: invoice count, invoiced amount, payment amount, outstanding
  balance and collection rate;
- revenue assurance: controls run, controls failed, control pass rate, open exception
  count, high-priority exception count and revenue at risk;
- data-science outputs: prediction count and average predicted probability.

Measures use governed source columns and do not reconstruct invoice totals, allocation
logic, value-at-risk logic, exception priority logic or model thresholds.
