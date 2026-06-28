{% macro current_record_flag(valid_to_expression) -%}
    iff({{ valid_to_expression }} is null, true, false)
{%- endmacro %}
