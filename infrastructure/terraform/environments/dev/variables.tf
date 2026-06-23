variable "snowflake_profile" {
  description = "Optional Snowflake CLI/Terraform profile; environment variables are preferred in CI."
  type        = string
  default     = null
  nullable    = true
}

variable "snowflake_organization_name" {
  description = "Optional organisation name; prefer SNOWFLAKE_ORGANIZATION_NAME."
  type        = string
  default     = null
  nullable    = true
}

variable "snowflake_account_name" {
  description = "Optional account name; prefer SNOWFLAKE_ACCOUNT_NAME."
  type        = string
  default     = null
  nullable    = true
}

variable "snowflake_account_locator" {
  description = "Optional inventory metadata only; never commit a real locator."
  type        = string
  default     = null
  nullable    = true
}

variable "snowflake_region" {
  description = "Optional inventory metadata only; provider derives connection region from account settings."
  type        = string
  default     = null
  nullable    = true
}

variable "snowflake_user" {
  description = "Optional deployment user; prefer SNOWFLAKE_USER with key-pair or workload identity."
  type        = string
  default     = null
  nullable    = true
}
