#!/usr/bin/env python3
"""
Quick Setup Script for Paper→Podcast Hackathon Submission
Automates AWS infrastructure deployment and application setup
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}🚀 {text}{Colors.ENDC}")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

def run_command(command: str, cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command with proper error handling"""
    print_info(f"Running: {command}")
    try:
        result = subprocess.run(
            command.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stderr:
            print(e.stderr)
        if check:
            sys.exit(1)
        return e

def check_prerequisites():
    """Check if required tools are installed"""
    print_header("Checking Prerequisites")
    
    requirements = {
        "python": "python --version",
        "aws": "aws --version", 
        "terraform": "terraform version",
        "docker": "docker --version"
    }
    
    missing = []
    
    for tool, command in requirements.items():
        try:
            result = run_command(command, check=False)
            if result.returncode == 0:
                print_success(f"{tool.capitalize()} is installed")
            else:
                missing.append(tool)
        except FileNotFoundError:
            missing.append(tool)
    
    if missing:
        print_error(f"Missing required tools: {', '.join(missing)}")
        print_info("Please install the missing tools and run this script again")
        
        print("\n📋 Installation Instructions:")
        for tool in missing:
            if tool == "aws":
                print("   AWS CLI: https://aws.amazon.com/cli/")
            elif tool == "terraform":
                print("   Terraform: https://terraform.io/downloads")
            elif tool == "docker":
                print("   Docker: https://docker.com/get-started")
        
        sys.exit(1)
    
    print_success("All prerequisites are installed!")

def setup_environment():
    """Setup environment variables and configuration"""
    print_header("Environment Setup")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print_warning(".env file not found, copying from template")
        template = Path(".env.example")
        if template.exists():
            import shutil
            shutil.copy(template, env_file)
            print_info("Please edit .env file with your actual values")
            return False
        else:
            print_error(".env.example template not found")
            return False
    
    # Validate AWS credentials
    try:
        result = run_command("aws sts get-caller-identity")
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            print_success(f"AWS credentials valid for account: {identity['Account']}")
            return True
    except:
        print_error("AWS credentials not configured")
        print_info("Run 'aws configure' to set up your credentials")
        return False

def deploy_infrastructure():
    """Deploy AWS infrastructure using Terraform"""
    print_header("Deploying AWS Infrastructure")
    
    terraform_dir = Path("infrastructure/terraform")
    
    if not terraform_dir.exists():
        print_error("Terraform configuration not found")
        return False
    
    # Initialize Terraform
    print_info("Initializing Terraform...")
    run_command("terraform init", cwd=str(terraform_dir))
    
    # Plan deployment
    print_info("Planning infrastructure deployment...")
    run_command("terraform plan", cwd=str(terraform_dir))
    
    # Ask for confirmation
    response = input(f"\n{Colors.WARNING}Deploy infrastructure? This will incur AWS costs. (y/N): {Colors.ENDC}")
    
    if response.lower() != 'y':
        print_info("Infrastructure deployment skipped")
        return False
    
    # Apply Terraform configuration
    print_info("Deploying infrastructure... This may take 10-15 minutes")
    run_command("terraform apply -auto-approve", cwd=str(terraform_dir))
    
    # Get outputs
    result = run_command("terraform output -json", cwd=str(terraform_dir))
    if result.returncode == 0:
        outputs = json.loads(result.stdout)
        
        # Save outputs to environment file
        with open(".env", "a") as f:
            f.write("\n# Generated by setup script\n")
            if "sagemaker_endpoints" in outputs:
                endpoints = outputs["sagemaker_endpoints"]["value"]
                f.write(f"LLAMA_NEMOTRON_ENDPOINT={endpoints.get('llama_nemotron', '')}\n")
                f.write(f"RETRIEVAL_NIM_ENDPOINT={endpoints.get('retrieval_embedding', '')}\n")
            
            if "s3_bucket" in outputs:
                f.write(f"S3_BUCKET_NAME={outputs['s3_bucket']['value']}\n")
            
            if "opensearch_endpoint" in outputs:
                f.write(f"OPENSEARCH_ENDPOINT={outputs['opensearch_endpoint']['value']}\n")
        
        print_success("Infrastructure deployed successfully!")
        return True
    
    return False

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        print_info("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    print_info("Installing Python packages...")
    run_command(f"{pip_path} install -r requirements.txt")
    
    print_success("Dependencies installed!")
    return python_path

def build_containers():
    """Build Docker containers for services"""
    print_header("Building Containers")
    
    if Path("Dockerfile").exists():
        print_info("Building application container...")
        run_command("docker build -t paper-podcast .")
        print_success("Container built successfully!")
    else:
        print_info("No Dockerfile found, skipping container build")

def run_tests():
    """Run test suite to validate setup"""
    print_header("Running Tests")
    
    test_dir = Path("tests")
    if test_dir.exists():
        print_info("Running test suite...")
        run_command("python -m pytest tests/ -v")
        print_success("Tests passed!")
    else:
        print_info("No tests found, skipping test execution")

def start_application():
    """Start the application services"""
    print_header("Starting Application")
    
    print_info("Starting FastAPI server...")
    print_info("Server will be available at: http://localhost:8000")
    print_info("API documentation: http://localhost:8000/docs")
    print_info("Streamlit UI: http://localhost:8501")
    
    print(f"\n{Colors.OKCYAN}🎉 Setup Complete! Your Paper→Podcast system is ready for the hackathon demo.{Colors.ENDC}")
    print(f"{Colors.OKGREEN}📋 Next Steps:{Colors.ENDC}")
    print("1. Upload a research paper PDF")
    print("2. Watch the agentic workflow in action")
    print("3. Listen to your generated podcast!")
    print(f"4. Monitor costs at: https://console.aws.amazon.com/billing/")
    
    # Ask if user wants to start the server
    response = input(f"\n{Colors.WARNING}Start the application server now? (y/N): {Colors.ENDC}")
    
    if response.lower() == 'y':
        print_info("Starting server... (Press Ctrl+C to stop)")
        try:
            # Start both FastAPI and Streamlit
            import threading
            
            def start_fastapi():
                run_command("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            
            def start_streamlit():
                time.sleep(2)  # Give FastAPI time to start
                run_command("streamlit run ui/streamlit_app.py --server.port 8501")
            
            # Start servers in separate threads
            fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
            streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
            
            fastapi_thread.start()
            streamlit_thread.start()
            
            # Keep main thread alive
            fastapi_thread.join()
            
        except KeyboardInterrupt:
            print_info("Shutting down servers...")

def estimate_costs():
    """Estimate AWS costs for the deployment"""
    print_header("Cost Estimation")
    
    costs = {
        "SageMaker Endpoints (2x ml.g4dn.xlarge)": "~$3.00/hour",
        "OpenSearch (t3.small.search)": "~$0.05/hour", 
        "S3 Storage": "~$0.50/month",
        "Lambda Executions": "~$0.10/month",
        "Amazon Polly TTS": "~$4.00 per 1M characters",
        "Data Transfer": "~$1.00/month"
    }
    
    print(f"{Colors.WARNING}💰 Estimated Costs (within $100 hackathon budget):{Colors.ENDC}")
    total_hourly = 0
    
    for service, cost in costs.items():
        print(f"   {service}: {cost}")
        if "/hour" in cost:
            # Extract hourly cost for rough total
            hourly = float(cost.split("$")[1].split("/")[0])
            total_hourly += hourly
    
    print(f"\n{Colors.BOLD}📊 Estimated Total: ~${total_hourly:.2f}/hour{Colors.ENDC}")
    print(f"{Colors.OKGREEN}✅ 24-hour runtime would cost ~${total_hourly * 24:.2f} (within budget){Colors.ENDC}")
    
    print(f"\n{Colors.WARNING}💡 Cost Optimization Tips:{Colors.ENDC}")
    print("   • Auto-shutdown is enabled at 11 PM daily")
    print("   • Endpoints will scale to zero when idle")
    print("   • Use fast_mode=true for demo to reduce costs")
    print("   • Monitor usage at: https://console.aws.amazon.com/billing/")

def main():
    """Main setup function"""
    print(f"""
{Colors.HEADER}{Colors.BOLD}
🏆 Paper→Podcast: Agentic + Verified
   AWS & NVIDIA Hackathon Setup Script
{Colors.ENDC}
This script will:
1. ✅ Check prerequisites
2. 🔧 Setup environment  
3. ☁️  Deploy AWS infrastructure
4. 📦 Install dependencies
5. 🚀 Start the application

{Colors.WARNING}⚠️  This will deploy AWS resources and incur costs!{Colors.ENDC}
""")
    
    # Cost estimation first
    estimate_costs()
    
    response = input(f"\n{Colors.WARNING}Continue with setup? (y/N): {Colors.ENDC}")
    if response.lower() != 'y':
        print_info("Setup cancelled")
        return
    
    # Run setup steps
    try:
        check_prerequisites()
        
        if not setup_environment():
            print_error("Environment setup failed. Please configure .env file and try again.")
            return
        
        if deploy_infrastructure():
            install_dependencies()
            build_containers()
            run_tests()
            start_application()
        else:
            print_error("Infrastructure deployment failed")
            
    except KeyboardInterrupt:
        print_info("\nSetup interrupted by user")
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()