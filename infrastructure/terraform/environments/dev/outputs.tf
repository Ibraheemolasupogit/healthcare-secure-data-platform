output "foundation" {
  description = "Declared DEV foundation objects; no secrets or account identifiers."
  value = {
    databases        = module.foundation.declared_databases
    schemas          = module.foundation.declared_schemas
    warehouses       = module.foundation.declared_warehouses
    roles            = module.foundation.declared_roles
    resource_monitor = module.foundation.resource_monitor
  }
}
