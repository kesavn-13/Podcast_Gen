"""
Simple setup script for Paper→Podcast without AWS credits
Installs dependencies and sets up local development environment
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle output"""
    print(f"\n🔧 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        if result.stdout:
            print(f"✅ Success: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr if e.stderr else str(e)}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    version_info = sys.version_info
    if version_info < (3, 8):
        print(f"❌ Python {version_info.major}.{version_info.minor} is too old. Need Python 3.8+")
        return False
    
    print(f"✅ Python {version_info.major}.{version_info.minor}.{version_info.micro} is compatible")
    return True


def install_requirements():
    """Install core requirements"""
    print("\n📦 Installing core dependencies...")
    
    # Install core requirements
    success = run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing core Python packages"
    )
    
    if not success:
        print("⚠️  Some packages failed to install. You may need to install them manually.")
        return False
    
    return True


def install_optional_packages():
    """Install optional packages for better performance"""
    print("\n🚀 Installing optional performance packages...")
    
    optional_packages = [
        ("faiss-cpu", "FAISS for fast vector similarity search"),
        ("torch", "PyTorch for better sentence-transformers performance")
    ]
    
    for package, description in optional_packages:
        print(f"\n🔍 Attempting to install {package} ({description})")
        success = run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installing {package}"
        )
        
        if success:
            print(f"✅ {package} installed successfully")
        else:
            print(f"⚠️  {package} installation failed - will use fallbacks")


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "temp",
        "temp/faiss_index", 
        "samples/papers",
        "logs",
        "data"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")


def create_env_file():
    """Create .env file with default settings"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env file already exists")
        return
    
    print("\n⚙️  Creating .env configuration file...")
    
    env_content = """# Paper→Podcast Configuration
# Development settings for running without AWS credits

# Environment
ENV=development
DEBUG=true

# Mock NIM Settings (Local Development)
USE_MOCK_CLIENTS=true
MOCK_REASONING_MODEL=llama-3.1-nemotron-nano-8B-v1
MOCK_EMBEDDING_MODEL=retrieval-embedding-nim

# Local RAG Settings
USE_LOCAL_RAG=true
FAISS_INDEX_PATH=temp/faiss_index
EMBEDDING_DIMENSION=768

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# AWS Settings (For future deployment)
# AWS_REGION=us-west-2
# SAGEMAKER_ENDPOINT_REASONING=your-reasoning-endpoint
# SAGEMAKER_ENDPOINT_EMBEDDING=your-embedding-endpoint
# OPENSEARCH_ENDPOINT=your-opensearch-endpoint

# Audio Settings
AUDIO_SAMPLE_RATE=22050
AUDIO_FORMAT=wav

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""

    with open(env_path, 'w') as f:
        f.write(env_content.strip())
    
    print("✅ Created .env file with development settings")


def test_installation():
    """Test basic functionality"""
    print("\n🧪 Testing installation...")
    
    # Test imports
    test_imports = [
        ("fastapi", "FastAPI web framework"),
        ("pydantic", "Data validation"),
        ("sentence_transformers", "Local embeddings"),
        ("numpy", "Numerical computing")
    ]
    
    for module, description in test_imports:
        try:
            __import__(module)
            print(f"✅ {description} import successful")
        except ImportError as e:
            print(f"❌ {description} import failed: {e}")
            return False
    
    # Test optional imports
    optional_imports = [
        ("faiss", "FAISS vector search"),
        ("torch", "PyTorch deep learning")
    ]
    
    for module, description in optional_imports:
        try:
            __import__(module)
            print(f"✅ {description} (optional) available")
        except ImportError:
            print(f"⚠️  {description} (optional) not available - using fallbacks")
    
    return True


def main():
    """Main setup process"""
    print("🚀 Paper→Podcast Setup (Mock-First Development)")
    print("=" * 60)
    print("Setting up local development environment without AWS credits")
    print("This will install dependencies and create a working mock system")
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Install packages
    if not install_requirements():
        print("\n❌ Core package installation failed!")
        return False
    
    install_optional_packages()
    
    # Setup environment
    create_directories()
    create_env_file()
    
    # Test everything works
    if not test_installation():
        print("\n❌ Installation test failed!")
        return False
    
    # Success message
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("  1. Test the RAG system:")
    print("     python scripts/test_rag_system.py")
    print("  2. Start the FastAPI backend:")
    print("     python -m uvicorn app.main:app --reload")
    print("  3. Run the Streamlit frontend:")
    print("     streamlit run app/frontend.py")
    print("  4. Generate your first podcast!")
    
    print("\n📚 Documentation:")
    print("  - README.md: Full project overview")
    print("  - docs/DEMO_SCRIPT.md: Demo walkthrough")
    print("  - PROJECT_STRUCTURE.md: Code organization")
    
    print("\n💡 This setup runs entirely locally - no AWS costs!")
    print("   When you get AWS credits, you can deploy with Terraform")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)