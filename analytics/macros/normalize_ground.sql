{% macro normalize_ground(column_name) %}
lower(trim(replace(replace(cast({{ column_name }} as varchar), '–', '-'), '—', '-')))
{% endmacro %}
