terraform {
  required_version = ">= 1.7, < 2.0"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "2.17.0"
    }
  }
}
