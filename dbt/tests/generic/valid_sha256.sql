{% test valid_sha256(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} is not null
  and not regexp_like({{ column_name }}, '^[0-9a-f]{64}$')
{% endtest %}
