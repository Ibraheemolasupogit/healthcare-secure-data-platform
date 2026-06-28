{% test timestamp_order(model, earlier_column, later_column) %}
select *
from {{ model }}
where {{ earlier_column }} is not null
  and {{ later_column }} is not null
  and {{ later_column }} < {{ earlier_column }}
{% endtest %}
