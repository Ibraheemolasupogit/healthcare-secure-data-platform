output "declared_databases" {
  description = "Environment-scoped database names declared by Terraform."
  value       = { for key, database in snowflake_database.databases : key => database.name }
}

output "declared_schemas" {
  description = "Managed schema names declared by Terraform."
  value       = { for key, schema in snowflake_schema.schemas : key => schema.fully_qualified_name }
}

output "declared_warehouses" {
  description = "Workload-isolated warehouse names declared by Terraform."
  value       = { for key, warehouse in snowflake_warehouse.warehouses : key => warehouse.name }
}

output "declared_roles" {
  description = "Ownership and functional account roles declared by Terraform."
  value       = { for key, role in snowflake_account_role.roles : key => role.name }
}

output "resource_monitor" {
  description = "Environment cost guardrail assigned to HEDP warehouses."
  value       = snowflake_resource_monitor.environment.name
}
