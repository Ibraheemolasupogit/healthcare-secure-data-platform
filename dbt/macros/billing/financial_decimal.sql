{% macro financial_decimal(expression, precision=18, scale=2) -%}
    try_to_decimal({{ expression }}, {{ precision }}, {{ scale }})
{%- endmacro %}
