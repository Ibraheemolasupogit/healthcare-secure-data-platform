provider "snowflake" {
  alias             = "accountadmin"
  role              = "ACCOUNTADMIN"
  profile           = var.snowflake_profile
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  user              = var.snowflake_user
}

provider "snowflake" {
  alias             = "securityadmin"
  role              = "SECURITYADMIN"
  profile           = var.snowflake_profile
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  user              = var.snowflake_user
}

provider "snowflake" {
  alias             = "sysadmin"
  role              = "SYSADMIN"
  profile           = var.snowflake_profile
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  user              = var.snowflake_user
}
