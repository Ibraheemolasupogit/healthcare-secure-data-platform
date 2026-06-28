# Payment allocation

`bridge_payment_allocation` establishes a governed allocation interface at one payment-to-invoice row because Milestone 7 payments reference a single invoice.

The model exposes:

- allocated amount;
- unallocated amount;
- overpayment flag;
- unmatched invoice flag;
- currency mismatch flag;
- allocation chronology flag;
- allocation status.

It does not implement cash-application workflows, automated recovery, or external payment-gateway integration.

