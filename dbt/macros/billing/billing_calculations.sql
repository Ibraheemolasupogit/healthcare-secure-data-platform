{% macro calculate_invoice_line_amount(quantity_expression, unit_price_expression, tax_expression='0') -%}
    round(coalesce({{ quantity_expression }}, 0)::number(18,2) * coalesce({{ unit_price_expression }}, 0)::number(18,2) + coalesce({{ tax_expression }}, 0)::number(18,2), 2)
{%- endmacro %}

{% macro calculate_signed_adjustment(adjustment_type_expression, amount_expression) -%}
    case
        when upper({{ adjustment_type_expression }}) in ('DEBIT', 'CORRECTION') then coalesce({{ amount_expression }}, 0)::number(18,2)
        when upper({{ adjustment_type_expression }}) in ('CREDIT', 'WRITE_OFF', 'CONTRACTUAL') then -1 * coalesce({{ amount_expression }}, 0)::number(18,2)
        else coalesce({{ amount_expression }}, 0)::number(18,2)
    end
{%- endmacro %}

{% macro calculate_outstanding_balance(invoice_total_expression, payment_expression, refund_expression, signed_adjustment_expression) -%}
    round(
        coalesce({{ invoice_total_expression }}, 0)::number(18,2)
        - coalesce({{ payment_expression }}, 0)::number(18,2)
        + coalesce({{ refund_expression }}, 0)::number(18,2)
        + coalesce({{ signed_adjustment_expression }}, 0)::number(18,2),
        2
    )
{%- endmacro %}

{% macro calculate_ageing_bucket(due_date_expression, as_of_date_expression, outstanding_amount_expression) -%}
    case
        when coalesce({{ outstanding_amount_expression }}, 0)::number(18,2) < 0 then 'CREDIT_BALANCE'
        when coalesce({{ outstanding_amount_expression }}, 0)::number(18,2) = 0 then 'CLOSED'
        when {{ due_date_expression }} > {{ as_of_date_expression }} then 'NOT_DUE'
        when datediff(day, {{ due_date_expression }}, {{ as_of_date_expression }}) <= 0 then 'CURRENT'
        when datediff(day, {{ due_date_expression }}, {{ as_of_date_expression }}) <= 30 then '1_30_DAYS'
        when datediff(day, {{ due_date_expression }}, {{ as_of_date_expression }}) <= 60 then '31_60_DAYS'
        when datediff(day, {{ due_date_expression }}, {{ as_of_date_expression }}) <= 90 then '61_90_DAYS'
        when datediff(day, {{ due_date_expression }}, {{ as_of_date_expression }}) <= 120 then '91_120_DAYS'
        else 'OVER_120_DAYS'
    end
{%- endmacro %}

{% macro financial_variance_status(variance_expression, tolerance_expression='0.01') -%}
    case
        when abs(coalesce({{ variance_expression }}, 0)::number(18,2)) <= {{ tolerance_expression }}::number(18,2) then 'MATCHED'
        else 'VARIANCE'
    end
{%- endmacro %}

{% macro currency_compatible(left_currency_expression, right_currency_expression) -%}
    coalesce(upper({{ left_currency_expression }}), 'UNKNOWN') = coalesce(upper({{ right_currency_expression }}), 'UNKNOWN')
{%- endmacro %}
