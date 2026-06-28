{% macro normalise_empty_string(expression) -%}
    nullif(trim(to_varchar({{ expression }})), '')
{%- endmacro %}
