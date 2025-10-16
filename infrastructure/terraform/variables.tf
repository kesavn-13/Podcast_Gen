# Variables for Paper→Podcast Infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "hackathon"
}

variable "owner_email" {
  description = "Owner email for resource tagging"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "paper-podcast"
}

variable "budget_limit" {
  description = "Budget limit for hackathon in USD"
  type        = number
  default     = 95.0
}

# SageMaker Configuration
variable "sagemaker_instance_type" {
  description = "SageMaker instance type for NIM endpoints"
  type        = string
  default     = "ml.g4dn.xlarge"  # GPU instance for NVIDIA NIM
}

variable "max_concurrent_transforms" {
  description = "Maximum concurrent SageMaker transforms"
  type        = number
  default     = 2
}

# OpenSearch Configuration
variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "search.t3.small.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 1
}

variable "opensearch_volume_size" {
  description = "OpenSearch EBS volume size in GB"
  type        = number
  default     = 10
}

# S3 Configuration
variable "enable_s3_versioning" {
  description = "Enable S3 versioning"
  type        = bool
  default     = false  # Disabled for cost optimization
}

variable "s3_lifecycle_days" {
  description = "Days after which objects transition to IA"
  type        = number
  default     = 30
}

# Networking
variable "create_vpc" {
  description = "Whether to create a new VPC"
  type        = bool
  default     = false  # Use default VPC for hackathon
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# Security
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access resources"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Open for hackathon demo
}

# Auto-shutdown configuration
variable "enable_auto_shutdown" {
  description = "Enable auto-shutdown for cost control"
  type        = bool
  default     = true
}

variable "auto_shutdown_time" {
  description = "Auto-shutdown time (24h format)"
  type        = string
  default     = "23:00"  # 11 PM
}

# NVIDIA NIM Configuration
variable "nvidia_ngc_api_key" {
  description = "NVIDIA NGC API key for NIM access"
  type        = string
  sensitive   = true
}

variable "nvidia_models" {
  description = "NVIDIA models to deploy"
  type = object({
    llama_nemotron = {
      model_name = string
      version    = string
    }
    retrieval_embedding = {
      model_name = string
      version    = string
    }
  })
  default = {
    llama_nemotron = {
      model_name = "llama-3.1-nemotron-nano-8b-v1"
      version    = "latest"
    }
    retrieval_embedding = {
      model_name = "nvidia/nv-embedqa-e5-v5"
      version    = "latest"
    }
  }
}