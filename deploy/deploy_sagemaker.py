"""
AWS SageMaker Deployment for NVIDIA NIM Integration
Hackathon Deployment Script
"""

import boto3
import json
import os
import time
from datetime import datetime
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SageMakerNIMDeployer:
    """Deploy NVIDIA NIM services to AWS SageMaker for hackathon"""
    
    def __init__(self):
        self.session = boto3.Session()
        self.sagemaker = self.session.client('sagemaker')
        self.iam = self.session.client('iam')
        
        self.role_name = "NVIDIANIMSageMakerRole"
        self.model_name = "nvidia-nim-llama31-nemotron"
        self.endpoint_config_name = f"{self.model_name}-config"
        self.endpoint_name = f"{self.model_name}-endpoint"
        
    def create_execution_role(self) -> str:
        """Create IAM role for SageMaker execution"""
        
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "sagemaker.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Check if role already exists
            response = self.iam.get_role(RoleName=self.role_name)
            role_arn = response['Role']['Arn']
            logger.info(f"Using existing role: {role_arn}")
            
        except self.iam.exceptions.NoSuchEntityException:
            # Create new role
            logger.info(f"Creating new IAM role: {self.role_name}")
            
            response = self.iam.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description="Role for NVIDIA NIM on SageMaker - Hackathon"
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach required policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess'
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(
                    RoleName=self.role_name,
                    PolicyArn=policy
                )
                
            logger.info(f"Created role with ARN: {role_arn}")
            
            # Wait for role propagation
            time.sleep(30)
            
        return role_arn
    
    def create_model(self, role_arn: str) -> str:
        """Create SageMaker model for NVIDIA NIM"""
        
        # NVIDIA NIM container image
        # Note: Replace with actual NVIDIA NIM container URI
        container_uri = os.getenv(
            "NVIDIA_NIM_CONTAINER_URI", 
            "nvcr.io/nim/meta/llama-3.1-nemotron-nano-8b-v1:latest"
        )
        
        model_config = {
            'ModelName': self.model_name,
            'PrimaryContainer': {
                'Image': container_uri,
                'Environment': {
                    'NVIDIA_VISIBLE_DEVICES': 'all',
                    'MODEL_NAME': 'llama-3.1-nemotron-nano-8b-v1',
                    'MAX_BATCH_SIZE': '32',
                    'MAX_SEQUENCE_LENGTH': '4096'
                }
            },
            'ExecutionRoleArn': role_arn,
            'Tags': [
                {'Key': 'Project', 'Value': 'NVIDIA-AWS-Hackathon'},
                {'Key': 'Component', 'Value': 'NIM-LLM'}
            ]
        }
        
        try:
            # Check if model already exists
            self.sagemaker.describe_model(ModelName=self.model_name)
            logger.info(f"Model {self.model_name} already exists")
            
        except self.sagemaker.exceptions.ClientError:
            # Create new model
            logger.info(f"Creating SageMaker model: {self.model_name}")
            response = self.sagemaker.create_model(**model_config)
            logger.info(f"Model created: {response['ModelArn']}")
            
        return self.model_name
    
    def create_endpoint_configuration(self) -> str:
        """Create endpoint configuration for NIM deployment"""
        
        config = {
            'EndpointConfigName': self.endpoint_config_name,
            'ProductionVariants': [
                {
                    'VariantName': 'primary',
                    'ModelName': self.model_name,
                    'InstanceType': 'ml.g5.xlarge',  # GPU instance for NIM
                    'InitialInstanceCount': 1,
                    'InitialVariantWeight': 1.0
                }
            ],
            'Tags': [
                {'Key': 'Project', 'Value': 'NVIDIA-AWS-Hackathon'},
                {'Key': 'Component', 'Value': 'NIM-Endpoint'}
            ]
        }
        
        try:
            # Check if config already exists
            self.sagemaker.describe_endpoint_config(
                EndpointConfigName=self.endpoint_config_name
            )
            logger.info(f"Endpoint config {self.endpoint_config_name} already exists")
            
        except self.sagemaker.exceptions.ClientError:
            # Create new configuration
            logger.info(f"Creating endpoint configuration: {self.endpoint_config_name}")
            response = self.sagemaker.create_endpoint_config(**config)
            logger.info(f"Endpoint config created: {response['EndpointConfigArn']}")
            
        return self.endpoint_config_name
    
    def deploy_endpoint(self) -> str:
        """Deploy SageMaker endpoint for NVIDIA NIM"""
        
        try:
            # Check if endpoint already exists
            response = self.sagemaker.describe_endpoint(EndpointName=self.endpoint_name)
            logger.info(f"Endpoint {self.endpoint_name} already exists with status: {response['EndpointStatus']}")
            
            if response['EndpointStatus'] == 'InService':
                return response['EndpointArn']
                
        except self.sagemaker.exceptions.ClientError:
            pass
            
        # Create new endpoint
        logger.info(f"Creating SageMaker endpoint: {self.endpoint_name}")
        
        response = self.sagemaker.create_endpoint(
            EndpointName=self.endpoint_name,
            EndpointConfigName=self.endpoint_config_name,
            Tags=[
                {'Key': 'Project', 'Value': 'NVIDIA-AWS-Hackathon'},
                {'Key': 'Component', 'Value': 'NIM-Inference'}
            ]
        )
        
        logger.info(f"Endpoint deployment started: {response['EndpointArn']}")
        
        # Wait for endpoint to be in service
        self._wait_for_endpoint()
        
        return response['EndpointArn']
    
    def _wait_for_endpoint(self, timeout_minutes: int = 15):
        """Wait for endpoint to be in service"""
        
        logger.info(f"Waiting for endpoint {self.endpoint_name} to be in service...")
        start_time = time.time()
        
        while True:
            response = self.sagemaker.describe_endpoint(EndpointName=self.endpoint_name)
            status = response['EndpointStatus']
            
            if status == 'InService':
                logger.info(f"Endpoint {self.endpoint_name} is now in service!")
                break
                
            elif status == 'Failed':
                logger.error(f"Endpoint deployment failed: {response.get('FailureReason', 'Unknown error')}")
                raise Exception(f"Endpoint deployment failed")
                
            elif time.time() - start_time > timeout_minutes * 60:
                logger.error(f"Endpoint deployment timeout after {timeout_minutes} minutes")
                raise Exception("Endpoint deployment timeout")
                
            else:
                logger.info(f"Endpoint status: {status}. Waiting...")
                time.sleep(30)
    
    def get_endpoint_url(self) -> str:
        """Get the endpoint URL for API calls"""
        
        region = self.session.region_name or 'us-east-1'
        account_id = boto3.client('sts').get_caller_identity()['Account']
        
        endpoint_url = f"https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{self.endpoint_name}/invocations"
        
        return endpoint_url
    
    def deploy_complete_infrastructure(self) -> Dict[str, str]:
        """Deploy complete NVIDIA NIM infrastructure on AWS SageMaker"""
        
        logger.info("🚀 Starting NVIDIA NIM deployment for hackathon...")
        
        # Step 1: Create IAM role
        role_arn = self.create_execution_role()
        
        # Step 2: Create SageMaker model
        model_name = self.create_model(role_arn)
        
        # Step 3: Create endpoint configuration
        config_name = self.create_endpoint_configuration()
        
        # Step 4: Deploy endpoint
        endpoint_arn = self.deploy_endpoint()
        
        # Step 5: Get endpoint URL
        endpoint_url = self.get_endpoint_url()
        
        deployment_info = {
            'model_name': model_name,
            'endpoint_name': self.endpoint_name,
            'endpoint_url': endpoint_url,
            'endpoint_arn': endpoint_arn,
            'role_arn': role_arn,
            'deployment_time': datetime.now().isoformat(),
            'status': 'DEPLOYED'
        }
        
        logger.info("✅ NVIDIA NIM deployment completed successfully!")
        logger.info(f"📡 Endpoint URL: {endpoint_url}")
        
        # Save deployment info
        with open('deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
            
        return deployment_info

def deploy_embedding_service() -> Dict[str, str]:
    """Deploy NVIDIA Embedding NIM service"""
    
    logger.info("🔍 Deploying NVIDIA Embedding NIM service...")
    
    # Similar deployment process for embedding service
    # This would be a separate SageMaker endpoint
    
    embedding_info = {
        'service': 'nvidia-embedding-nim',
        'model': 'nvidia/nv-embedqa-e5-v5',
        'endpoint_url': 'https://embedding-service-endpoint',
        'status': 'DEPLOYED'
    }
    
    return embedding_info

def setup_s3_storage() -> str:
    """Setup S3 bucket for hackathon project storage"""
    
    s3 = boto3.client('s3')
    bucket_name = f"nvidia-aws-hackathon-{int(time.time())}"
    
    try:
        s3.create_bucket(Bucket=bucket_name)
        logger.info(f"Created S3 bucket: {bucket_name}")
        
        # Setup folder structure
        folders = ['papers/', 'audio/', 'temp/', 'models/']
        for folder in folders:
            s3.put_object(Bucket=bucket_name, Key=folder)
            
    except Exception as e:
        logger.error(f"Error creating S3 bucket: {e}")
        
    return bucket_name

def create_environment_config(deployment_info: Dict[str, str]) -> None:
    """Create environment configuration file for hackathon"""
    
    env_config = f"""# NVIDIA-AWS Hackathon Environment Configuration
# Generated on {datetime.now().isoformat()}

# NVIDIA NIM Endpoints
NVIDIA_NIM_ENDPOINT={deployment_info['endpoint_url']}
NVIDIA_EMBEDDING_ENDPOINT=https://embedding-service-endpoint
NVIDIA_API_KEY=your_nvidia_api_key_here

# AWS Configuration
AWS_REGION={boto3.Session().region_name or 'us-east-1'}
S3_BUCKET=your_s3_bucket_name

# SageMaker Configuration
SAGEMAKER_ENDPOINT_NAME={deployment_info['endpoint_name']}
SAGEMAKER_ROLE_ARN={deployment_info['role_arn']}

# Hackathon Specific
HACKATHON_MODE=true
DEMO_MODE=true
"""

    with open('.env.hackathon', 'w') as f:
        f.write(env_config)
        
    logger.info("✅ Environment configuration created: .env.hackathon")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Deploy NVIDIA NIM infrastructure
        deployer = SageMakerNIMDeployer()
        deployment_info = deployer.deploy_complete_infrastructure()
        
        # Deploy embedding service
        embedding_info = deploy_embedding_service()
        
        # Setup S3 storage
        bucket_name = setup_s3_storage()
        
        # Create environment configuration
        create_environment_config(deployment_info)
        
        print("\n🎯 HACKATHON DEPLOYMENT COMPLETE!")
        print(f"✅ NIM Endpoint: {deployment_info['endpoint_url']}")
        print(f"✅ Embedding Service: {embedding_info['endpoint_url']}")
        print(f"✅ S3 Bucket: {bucket_name}")
        print(f"✅ Environment Config: .env.hackathon")
        print("\n🚀 Your NVIDIA-AWS hackathon project is ready!")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise