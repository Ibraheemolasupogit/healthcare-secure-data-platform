# Milestone 1 intentionally declares no remote resources.
# Milestone 3 will add focused database, schema, warehouse, monitor and role modules.
locals {
  normalised_prefix = upper("${var.name_prefix}_${var.environment}")
}
