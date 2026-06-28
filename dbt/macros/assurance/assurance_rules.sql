{% macro assurance_status(record_count_variance, amount_variance, fixed_tolerance, timing_difference_flag) -%}
    case
        when {{ timing_difference_flag }} then 'PASS_WITH_TIMING_DIFFERENCE'
        when abs(coalesce({{ record_count_variance }}, 0)) = 0
            and abs(coalesce({{ amount_variance }}, 0)::number(18,2))
                <= coalesce({{ fixed_tolerance }}, 0)::number(18,2)
            then 'PASS'
        when abs(coalesce({{ record_count_variance }}, 0)) = 0
            and abs(coalesce({{ amount_variance }}, 0)::number(18,2))
                <= coalesce({{ fixed_tolerance }}, 0)::number(18,2) * 10
            then 'WARNING'
        else 'FAIL'
    end
{%- endmacro %}

{% macro exception_age_days(detected_at_expression, as_of_date_expression) -%}
    datediff(day, cast({{ detected_at_expression }} as date), {{ as_of_date_expression }})
{%- endmacro %}

{% macro priority_band(score_expression) -%}
    case
        when {{ score_expression }} >= 80 then 'P1'
        when {{ score_expression }} >= 55 then 'P2'
        when {{ score_expression }} >= 30 then 'P3'
        else 'P4'
    end
{%- endmacro %}

{% macro assurance_status_precedence(failed_expression, warned_expression, open_exception_expression) -%}
    case
        when coalesce({{ failed_expression }}, 0) > 0 then 'FAIL'
        when coalesce({{ open_exception_expression }}, 0) > 0 then 'WARNING'
        when coalesce({{ warned_expression }}, 0) > 0 then 'WARNING'
        else 'PASS'
    end
{%- endmacro %}
