variable "snowflake_profile" {
  description = "Optional protected PROD deployment profile; workload identity is preferred."
  type        = string
  default     = null
  nullable    = true
}
