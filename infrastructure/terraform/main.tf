# Paper→Podcast AWS Infrastructure
# Terraform configuration for hackathon submission

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Paper-Podcast"
      Hackathon   = "AWS-NVIDIA-Agentic-AI"
      Environment = var.environment
      Owner       = var.owner_email
      CostCenter  = "hackathon-budget"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local variables
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  
  common_tags = {
    Project     = "Paper-Podcast"
    Hackathon   = "AWS-NVIDIA-Agentic-AI"
    Environment = var.environment
  }
}