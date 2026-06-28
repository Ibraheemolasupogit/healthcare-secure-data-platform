{% macro generate_healthcare_surrogate_key(fields) -%}
    sha2(
        concat_ws(
            '|'
            {%- for field in fields -%}
                , coalesce(to_varchar({{ field }}), '∅')
            {%- endfor -%}
        ),
        256
    )
{%- endmacro %}
