locals {
  foundation_config = jsondecode(file("${path.root}/../../../../snowflake/config/foundation.json"))
}

module "foundation" {
  source            = "../../modules/snowflake_foundation"
  environment       = "DEV"
  foundation_config = local.foundation_config

  providers = {
    snowflake.accountadmin  = snowflake.accountadmin
    snowflake.securityadmin = snowflake.securityadmin
    snowflake.sysadmin      = snowflake.sysadmin
  }
}
