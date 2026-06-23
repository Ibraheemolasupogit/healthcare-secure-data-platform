variable "environment" {
  description = "Environment suffix used for strict object isolation."
  type        = string

  validation {
    condition     = contains(["DEV", "TEST", "PROD"], var.environment)
    error_message = "environment must be DEV, TEST, or PROD."
  }
}

variable "foundation_config" {
  description = "Decoded snowflake/config/foundation.json contract."
  type        = any
}
