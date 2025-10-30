# SageMaker Infrastructure for NVIDIA NIM Deployment
# This is the REQUIRED component for hackathon submission

# SageMaker Execution Role for NIM endpoints
resource "aws_iam_role" "sagemaker_execution_role" {
  name = "${var.project_name}-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# SageMaker execution policy
resource "aws_iam_role_policy_attachment" "sagemaker_execution_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# Additional policies for S3 and CloudWatch
resource "aws_iam_role_policy_attachment" "sagemaker_s3_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_cloudwatch_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# Custom policy for NVIDIA NIM access
resource "aws_iam_role_policy" "nvidia_nim_policy" {
  name = "${var.project_name}-nvidia-nim-policy"
  role = aws_iam_role.sagemaker_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.nvidia_api_key.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
}

# Store NVIDIA API key securely
resource "aws_secretsmanager_secret" "nvidia_api_key" {
  name        = "${var.project_name}-nvidia-api-key"
  description = "NVIDIA NGC API key for NIM access"
  
  tags = merge(local.common_tags, {
    Purpose = "NVIDIA-NIM-Authentication"
  })
}

resource "aws_secretsmanager_secret_version" "nvidia_api_key" {
  secret_id     = aws_secretsmanager_secret.nvidia_api_key.id
  secret_string = var.nvidia_ngc_api_key
}

# SageMaker Model for Llama Nemotron (REQUIRED)
resource "aws_sagemaker_model" "llama_nemotron" {
  name               = "${var.project_name}-llama-nemotron-model"
  execution_role_arn = aws_iam_role.sagemaker_execution_role.arn

  primary_container {
    # NVIDIA NIM container image
    image = "nvcr.io/nim/meta/llama-3.1-8b-instruct:1.0.0"
    
    environment = {
      NVIDIA_NIM_CACHE_PATH    = "/tmp/nim_cache"
      NGC_API_KEY_SECRET_ARN   = aws_secretsmanager_secret.nvidia_api_key.arn
      MODEL_NAME               = var.nvidia_models.llama_nemotron.model_name
      MAX_MODEL_LEN           = "4096"
      CUDA_VISIBLE_DEVICES    = "0"
    }
  }

  tags = merge(local.common_tags, {
    ModelType = "llama-nemotron"
    Purpose   = "hackathon-submission-requirement"
  })
}

# SageMaker Endpoint Configuration for Llama Nemotron
resource "aws_sagemaker_endpoint_configuration" "llama_nemotron" {
  name = "${var.project_name}-llama-nemotron-config"

  production_variants {
    variant_name           = "primary"
    model_name            = aws_sagemaker_model.llama_nemotron.name
    initial_instance_count = 1
    instance_type         = var.sagemaker_instance_type
    initial_variant_weight = 1
  }

  # Auto-scaling configuration for cost control
  async_inference_config {
    output_config {
      s3_output_path = "s3://${aws_s3_bucket.main.bucket}/sagemaker-outputs/"
    }
  }

  tags = local.common_tags
}

# SageMaker Endpoint for Llama Nemotron (REQUIRED)
resource "aws_sagemaker_endpoint" "llama_nemotron" {
  name                 = "${var.project_name}-llama-nemotron-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.llama_nemotron.name

  tags = merge(local.common_tags, {
    CriticalForDemo = "true"
    AutoShutdown    = var.enable_auto_shutdown ? "enabled" : "disabled"
  })
}

# SageMaker Model for Retrieval Embedding (REQUIRED)
resource "aws_sagemaker_model" "retrieval_embedding" {
  name               = "${var.project_name}-retrieval-embedding-model"
  execution_role_arn = aws_iam_role.sagemaker_execution_role.arn

  primary_container {
    # NVIDIA Retrieval NIM container
    image = "nvcr.io/nim/nvidia/nv-embedqa-e5-v5:1.0.0"
    
    environment = {
      NVIDIA_NIM_CACHE_PATH  = "/tmp/nim_cache"
      NGC_API_KEY_SECRET_ARN = aws_secretsmanager_secret.nvidia_api_key.arn
      MODEL_NAME             = var.nvidia_models.retrieval_embedding.model_name
    }
  }

  tags = merge(local.common_tags, {
    ModelType = "retrieval-embedding"
    Purpose   = "hackathon-submission-requirement"
  })
}

# SageMaker Endpoint Configuration for Retrieval Embedding
resource "aws_sagemaker_endpoint_configuration" "retrieval_embedding" {
  name = "${var.project_name}-retrieval-embedding-config"

  production_variants {
    variant_name           = "primary"
    model_name            = aws_sagemaker_model.retrieval_embedding.name
    initial_instance_count = 1
    instance_type         = var.sagemaker_instance_type
    initial_variant_weight = 1
  }

  tags = local.common_tags
}

# SageMaker Endpoint for Retrieval Embedding (REQUIRED)
resource "aws_sagemaker_endpoint" "retrieval_embedding" {
  name                 = "${var.project_name}-retrieval-embedding-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.retrieval_embedding.name

  tags = merge(local.common_tags, {
    CriticalForDemo = "true"
    AutoShutdown    = var.enable_auto_shutdown ? "enabled" : "disabled"
  })
}

# Auto-shutdown Lambda function for cost control
resource "aws_lambda_function" "endpoint_scheduler" {
  count = var.enable_auto_shutdown ? 1 : 0
  
  filename         = "endpoint_scheduler.zip"
  function_name    = "${var.project_name}-endpoint-scheduler"
  role            = aws_iam_role.lambda_scheduler_role[0].arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      LLAMA_ENDPOINT_NAME     = aws_sagemaker_endpoint.llama_nemotron.name
      RETRIEVAL_ENDPOINT_NAME = aws_sagemaker_endpoint.retrieval_embedding.name
      BUDGET_LIMIT           = var.budget_limit
    }
  }

  tags = local.common_tags
}

# IAM role for Lambda scheduler
resource "aws_iam_role" "lambda_scheduler_role" {
  count = var.enable_auto_shutdown ? 1 : 0
  name  = "${var.project_name}-lambda-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda policy for SageMaker endpoint management
resource "aws_iam_role_policy" "lambda_scheduler_policy" {
  count = var.enable_auto_shutdown ? 1 : 0
  name  = "${var.project_name}-lambda-scheduler-policy"
  role  = aws_iam_role.lambda_scheduler_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:DescribeEndpoint",
          "sagemaker:UpdateEndpoint",
          "sagemaker:DeleteEndpoint",
          "ce:GetCostAndUsage",
          "ce:GetUsageReport"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# EventBridge rule for scheduled shutdown
resource "aws_cloudwatch_event_rule" "endpoint_scheduler" {
  count = var.enable_auto_shutdown ? 1 : 0
  
  name                = "${var.project_name}-endpoint-scheduler"
  description         = "Trigger endpoint management for cost control"
  schedule_expression = "cron(0 ${replace(var.auto_shutdown_time, ":", " ")} * * ? *)"
}

# EventBridge target
resource "aws_cloudwatch_event_target" "endpoint_scheduler" {
  count = var.enable_auto_shutdown ? 1 : 0
  
  rule      = aws_cloudwatch_event_rule.endpoint_scheduler[0].name
  target_id = "EndpointSchedulerTarget"
  arn       = aws_lambda_function.endpoint_scheduler[0].arn
}

# Lambda permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  count = var.enable_auto_shutdown ? 1 : 0
  
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.endpoint_scheduler[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.endpoint_scheduler[0].arn
}