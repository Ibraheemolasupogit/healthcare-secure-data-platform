provider "snowflake" {
  alias   = "accountadmin"
  role    = "ACCOUNTADMIN"
  profile = var.snowflake_profile
}
provider "snowflake" {
  alias   = "securityadmin"
  role    = "SECURITYADMIN"
  profile = var.snowflake_profile
}
provider "snowflake" {
  alias   = "sysadmin"
  role    = "SYSADMIN"
  profile = var.snowflake_profile
}
