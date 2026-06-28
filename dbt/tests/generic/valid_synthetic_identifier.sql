{% test valid_synthetic_identifier(model, column_name, prefix) %}
select *
from {{ model }}
where {{ column_name }} is not null
  and not regexp_like({{ column_name }}, '^' || '{{ prefix }}' || '-[0-9]{9}$')
{% endtest %}
