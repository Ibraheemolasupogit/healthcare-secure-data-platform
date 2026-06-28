{% macro reconciliation_status(key_expression) -%}
    case
        when {{ key_expression }} is null then 'UNMATCHED'
        else 'MATCHED'
    end
{%- endmacro %}
