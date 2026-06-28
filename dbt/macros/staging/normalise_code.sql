{% macro normalise_code(expression) -%}
    upper({{ normalise_empty_string(expression) }})
{%- endmacro %}
