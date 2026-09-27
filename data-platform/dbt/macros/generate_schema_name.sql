{# Use the custom schema name verbatim (marts -> business, staging -> curated) instead of dbt's
   default target_schema + custom concatenation (which produced business_business / business_curated).
   Safe here because this is a single-target, single-owner analytics DB. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
