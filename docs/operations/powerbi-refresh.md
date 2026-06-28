# Power BI refresh operations

Refresh operations are documented as a future deployment capability. Power BI refresh
must occur only after governed upstream products are ready.

Future flow:

1. Airflow confirms trusted Snowflake products are complete.
2. Airflow records successful dbt and assurance completion.
3. Airflow may call an approved Power BI/Fabric refresh endpoint in a later deployment
   milestone.
4. Power BI refreshes the semantic model.
5. Refresh status returns to Airflow.
6. Airflow stores workflow evidence.

No live refresh API calls are implemented here.
