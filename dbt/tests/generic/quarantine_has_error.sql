{% test quarantine_has_error(model, column_name) %}
select *
from {{ model }}
where {{ column_name }} is null
   or array_size({{ column_name }}) = 0
{% endtest %}
