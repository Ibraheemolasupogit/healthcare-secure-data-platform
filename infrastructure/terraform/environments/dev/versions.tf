terraform {
  required_version = ">= 1.7, < 2.0"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "2.18.0"
    }
  }
}
