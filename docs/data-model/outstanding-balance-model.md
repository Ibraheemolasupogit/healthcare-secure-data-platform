# Outstanding balance model

`fct_outstanding_balance` is the authoritative Milestone 8 governed balance model.

Formula:

```text
governed outstanding balance
= governed invoice total
- valid allocated payments
+ valid refunds
+ signed adjustments
```

The model preserves the source balance, calculates governed balance, exposes source-to-governed variance, assigns deterministic ageing buckets using `billing_as_of_date`, and flags credit balances.

Milestone 9 will own operational reconciliation workflow and evidence packs.

