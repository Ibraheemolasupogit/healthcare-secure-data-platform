{% macro safe_to_boolean(expression) -%}
    try_to_boolean({{ expression }})
{%- endmacro %}

{% macro safe_to_timestamp(expression) -%}
    try_to_timestamp_tz({{ expression }})
{%- endmacro %}

{% macro safe_to_date(expression) -%}
    try_to_date({{ expression }})
{%- endmacro %}

{% macro safe_to_number(expression) -%}
    try_to_number({{ expression }})
{%- endmacro %}
