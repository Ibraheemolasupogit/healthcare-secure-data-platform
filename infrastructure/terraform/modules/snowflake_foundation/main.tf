locals {
  prefix = upper("${var.foundation_config.name_prefix}_${var.environment}")

  schemas = merge([
    for database_key, database in var.foundation_config.databases : {
      for schema_name, purpose in database.schemas : "${database_key}.${schema_name}" => {
        database_key = database_key
        schema_name  = schema_name
        purpose      = purpose
        owner_role   = database.owner_role
        retention    = database.retention_days[var.environment]
      }
    }
  ]...)

  roles = toset(concat(
    var.foundation_config.roles.ownership,
    var.foundation_config.roles.functional,
  ))

  hierarchy = {
    for child, parent in var.foundation_config.roles.hierarchy : child => {
      child  = child
      parent = parent
    }
  }

  warehouse_usage = merge([
    for role, warehouses in var.foundation_config.grants.warehouse_usage : {
      for warehouse in warehouses : "${role}.${warehouse}" => {
        role      = role
        warehouse = warehouse
      }
    }
  ]...)

  schema_usage = merge([
    for role, schemas in var.foundation_config.grants.schema_usage : {
      for schema_ref in schemas : "${role}.${schema_ref}" => {
        role       = role
        schema_ref = schema_ref
        database   = split(".", schema_ref)[0]
      }
    }
  ]...)

  database_usage = {
    for item in distinct([
      for grant in values(local.schema_usage) : "${grant.role}.${grant.database}"
      ]) : item => {
      role     = split(".", item)[0]
      database = split(".", item)[1]
    }
  }

  schema_create = merge([
    for role, schemas in var.foundation_config.grants.schema_create : {
      for schema_ref in schemas : "${role}.${schema_ref}" => {
        role       = role
        schema_ref = schema_ref
      }
    }
  ]...)

  future_read = merge([
    for role, schemas in var.foundation_config.grants.future_read : {
      for schema_ref in schemas : "${role}.${schema_ref}" => {
        role       = role
        schema_ref = schema_ref
      }
    }
  ]...)
}

resource "snowflake_database" "databases" {
  provider = snowflake.sysadmin
  for_each = var.foundation_config.databases

  name                        = "${local.prefix}_${each.key}"
  comment                     = "${each.value.purpose} Managed by Terraform; ${var.environment} environment."
  data_retention_time_in_days = each.value.retention_days[var.environment]
  is_transient                = false
}

resource "snowflake_schema" "schemas" {
  provider = snowflake.sysadmin
  for_each = local.schemas

  database                    = snowflake_database.databases[each.value.database_key].name
  name                        = each.value.schema_name
  comment                     = "${each.value.purpose} Managed by Terraform; no business tables in Milestone 3."
  with_managed_access         = true
  is_transient                = false
  data_retention_time_in_days = each.value.retention
}

resource "snowflake_resource_monitor" "environment" {
  provider = snowflake.accountadmin

  name                      = "${local.prefix}_RM_ENVIRONMENT"
  credit_quota              = var.foundation_config.resource_monitors.ENVIRONMENT.credit_quota[var.environment]
  frequency                 = var.foundation_config.resource_monitors.ENVIRONMENT.frequency
  start_timestamp           = var.foundation_config.resource_monitors.ENVIRONMENT.start_timestamp
  notify_triggers           = var.foundation_config.resource_monitors.ENVIRONMENT.notify_triggers
  suspend_trigger           = var.foundation_config.resource_monitors.ENVIRONMENT.suspend_trigger
  suspend_immediate_trigger = var.foundation_config.resource_monitors.ENVIRONMENT.suspend_immediate_trigger
}

resource "snowflake_warehouse" "warehouses" {
  provider = snowflake.accountadmin
  for_each = var.foundation_config.warehouses

  name                         = "${local.prefix}_${each.key}"
  comment                      = "${each.value.purpose} Initial sizing is unbenchmarked and cost-aware."
  warehouse_size               = each.value.sizes[var.environment]
  auto_suspend                 = each.value.auto_suspend_seconds
  auto_resume                  = each.value.auto_resume
  initially_suspended          = true
  min_cluster_count            = each.value.min_cluster_count
  max_cluster_count            = each.value.max_cluster_count
  scaling_policy               = each.value.scaling_policy
  statement_timeout_in_seconds = each.value.statement_timeout_seconds
  resource_monitor             = snowflake_resource_monitor.environment.fully_qualified_name
}

resource "snowflake_account_role" "roles" {
  provider = snowflake.securityadmin
  for_each = local.roles

  name    = "${local.prefix}_${each.value}"
  comment = "HEDP ${var.environment} ${lower(replace(each.value, "_", " "))} role; never grant objects directly to users."
}

resource "snowflake_grant_account_role" "hierarchy" {
  provider = snowflake.securityadmin
  for_each = local.hierarchy

  role_name = snowflake_account_role.roles[each.value.child].name
  parent_role_name = contains(var.foundation_config.roles.external_parents, each.value.parent) ? (
    each.value.parent
  ) : snowflake_account_role.roles[each.value.parent].name
}

resource "snowflake_grant_privileges_to_account_role" "warehouse_usage" {
  provider = snowflake.securityadmin
  for_each = local.warehouse_usage

  account_role_name = snowflake_account_role.roles[each.value.role].name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.warehouses[each.value.warehouse].fully_qualified_name
  }
}

resource "snowflake_grant_privileges_to_account_role" "database_usage" {
  provider = snowflake.securityadmin
  for_each = local.database_usage

  account_role_name = snowflake_account_role.roles[each.value.role].name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.databases[each.value.database].fully_qualified_name
  }
}

resource "snowflake_grant_privileges_to_account_role" "schema_usage" {
  provider = snowflake.securityadmin
  for_each = local.schema_usage

  account_role_name = snowflake_account_role.roles[each.value.role].name
  privileges        = ["USAGE"]
  on_schema {
    schema_name = snowflake_schema.schemas[each.value.schema_ref].fully_qualified_name
  }
}

resource "snowflake_grant_privileges_to_account_role" "schema_create" {
  provider = snowflake.securityadmin
  for_each = local.schema_create

  account_role_name = snowflake_account_role.roles[each.value.role].name
  privileges        = ["CREATE TABLE", "CREATE VIEW", "CREATE DYNAMIC TABLE"]
  on_schema {
    schema_name = snowflake_schema.schemas[each.value.schema_ref].fully_qualified_name
  }
}

resource "snowflake_grant_privileges_to_account_role" "future_tables_read" {
  provider = snowflake.securityadmin
  for_each = local.future_read

  account_role_name = snowflake_account_role.roles[each.value.role].name
  privileges        = ["SELECT"]
  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = snowflake_schema.schemas[each.value.schema_ref].fully_qualified_name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "future_views_read" {
  provider = snowflake.securityadmin
  for_each = local.future_read

  account_role_name = snowflake_account_role.roles[each.value.role].name
  privileges        = ["SELECT"]
  on_schema_object {
    future {
      object_type_plural = "VIEWS"
      in_schema          = snowflake_schema.schemas[each.value.schema_ref].fully_qualified_name
    }
  }
}

resource "snowflake_tag" "tags" {
  provider = snowflake.sysadmin
  for_each = var.foundation_config.tags

  name                   = each.key
  database               = snowflake_database.databases[each.value.database].name
  schema                 = snowflake_schema.schemas["${each.value.database}.${each.value.schema}"].name
  comment                = each.value.purpose
  ordered_allowed_values = each.value.allowed_values
}

# Ownership transfer remains Terraform-managed. The protected bootstrap identity uses
# ACCOUNTADMIN only for monitor assignment, SECURITYADMIN for roles/grants, and SYSADMIN
# for databases/schemas/tags. No human or service user grants are managed here.
resource "snowflake_grant_ownership" "database_ownership" {
  provider = snowflake.securityadmin
  for_each = var.foundation_config.databases

  depends_on = [
    snowflake_grant_ownership.schema_ownership,
    snowflake_grant_privileges_to_account_role.database_usage,
  ]

  account_role_name   = snowflake_account_role.roles[each.value.owner_role].name
  outbound_privileges = "COPY"
  on {
    object_type = "DATABASE"
    object_name = snowflake_database.databases[each.key].fully_qualified_name
  }
}

resource "snowflake_grant_ownership" "schema_ownership" {
  provider = snowflake.securityadmin
  for_each = local.schemas

  depends_on = [
    snowflake_grant_account_role.hierarchy,
    snowflake_grant_privileges_to_account_role.schema_usage,
    snowflake_grant_privileges_to_account_role.schema_create,
    snowflake_grant_privileges_to_account_role.future_tables_read,
    snowflake_grant_privileges_to_account_role.future_views_read,
    snowflake_tag.tags,
  ]

  account_role_name   = snowflake_account_role.roles[each.value.owner_role].name
  outbound_privileges = "COPY"
  on {
    object_type = "SCHEMA"
    object_name = snowflake_schema.schemas[each.key].fully_qualified_name
  }
}

resource "snowflake_grant_ownership" "warehouse_ownership" {
  provider = snowflake.securityadmin
  for_each = var.foundation_config.warehouses

  depends_on = [
    snowflake_grant_account_role.hierarchy,
    snowflake_grant_privileges_to_account_role.warehouse_usage,
  ]

  account_role_name   = snowflake_account_role.roles[each.value.owner_role].name
  outbound_privileges = "COPY"
  on {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.warehouses[each.key].fully_qualified_name
  }
}

resource "snowflake_grant_ownership" "monitor_ownership" {
  provider = snowflake.securityadmin

  depends_on = [
    snowflake_grant_account_role.hierarchy,
    snowflake_warehouse.warehouses,
  ]

  account_role_name   = snowflake_account_role.roles[var.foundation_config.resource_monitors.ENVIRONMENT.owner_role].name
  outbound_privileges = "COPY"
  on {
    object_type = "RESOURCE MONITOR"
    object_name = snowflake_resource_monitor.environment.fully_qualified_name
  }
}

resource "snowflake_grant_ownership" "tag_ownership" {
  provider = snowflake.securityadmin
  for_each = var.foundation_config.tags

  depends_on = [snowflake_grant_account_role.hierarchy]

  account_role_name   = snowflake_account_role.roles[each.value.owner_role].name
  outbound_privileges = "COPY"
  on {
    object_type = "TAG"
    object_name = snowflake_tag.tags[each.key].fully_qualified_name
  }
}
