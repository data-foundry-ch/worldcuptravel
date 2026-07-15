{% macro haversine_km(lat1, lon1, lat2, lon2, radius=6371.0088) %}
(
    {{ radius }} * 2 * asin(sqrt(
        power(sin(radians(({{ lat2 }} - {{ lat1 }}) / 2)), 2) +
        cos(radians({{ lat1 }})) * cos(radians({{ lat2 }})) *
        power(sin(radians(({{ lon2 }} - {{ lon1 }}) / 2)), 2)
    ))
)
{% endmacro %}
