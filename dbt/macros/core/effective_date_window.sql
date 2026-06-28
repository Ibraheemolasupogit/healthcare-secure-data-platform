{% macro effective_date_window(start_expression, end_expression) -%}
    {{ start_expression }} as valid_from,
    {{ end_expression }} as valid_to,
    {{ current_record_flag(end_expression) }} as is_current
{%- endmacro %}
