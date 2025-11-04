# AI Research Podcast Agent - Production Docker Build
# NVIDIA-AWS Hackathon Compliant Full-Stack Application
# Supports both Amazon EKS and Amazon SageMaker deployments

FROM python:3.9-slim AS base

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Hackathon environment
ENV HACKATHON_MODE=true
ENV USE_NVIDIA_NIM=true
ENV AWS_DEFAULT_REGION=us-east-1

# Create application user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install system dependencies for AI/ML workloads
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    git \
    wget \
    libsndfile1 \
    libportaudio2 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies with production optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install additional production dependencies
RUN pip install --no-cache-dir \
    boto3 \
    sagemaker \
    kubernetes \
    gunicorn \
    uvicorn[standard] \
    prometheus-client

# Production stage
FROM base AS production

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/temp /app/logs /opt/ml/model /opt/ml/code && \
    chown -R appuser:appuser /app /opt/ml

# Copy SageMaker inference script
COPY --chown=appuser:appuser deploy/inference.py /opt/ml/code/

# Switch to non-root user for security
USER appuser

# Expose ports for both EKS (8000) and SageMaker (8080)
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default production command (EKS)
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "300"]

# Development stage
FROM base AS development

# Install development dependencies  
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    black \
    isort \
    flake8 \
    mypy \
    jupyter \
    notebook

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8501 8888

# Command for development
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# SageMaker stage
FROM production AS sagemaker

# SageMaker specific setup
ENV SAGEMAKER_PROGRAM=inference.py
ENV SAGEMAKER_SUBMIT_DIRECTORY=/opt/ml/code

# SageMaker inference command
CMD ["python", "/opt/ml/code/inference.py"]

# Expose port
EXPOSE 8000

# Production command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]