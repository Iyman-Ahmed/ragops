variable "region" {
  type    = string
  default = "us-east-1"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "cpu" {
  type    = number
  default = 512
}

variable "memory" {
  type    = number
  default = 1024
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "execution_role_arn" {
  type        = string
  description = "IAM role ECS uses to pull the image and write logs"
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_ids" {
  type = list(string)
}

variable "llm_base_url" {
  type    = string
  default = "https://api.openai.com/v1"
}

variable "llm_model" {
  type    = string
  default = ""
}
