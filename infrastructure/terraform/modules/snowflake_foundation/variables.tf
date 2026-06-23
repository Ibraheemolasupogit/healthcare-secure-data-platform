variable "environment" {
  description = "Short environment name used for naming and tagging."
  type        = string

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test, or prod."
  }
}

variable "name_prefix" {
  description = "Non-sensitive prefix for future Snowflake objects."
  type        = string
  default     = "HSDP"
}
