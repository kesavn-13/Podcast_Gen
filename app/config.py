"""
Configuration management for Paper→Podcast
Uses Pydantic Settings for type-safe environment variable handling
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # ============================================================================
    # HACKATHON SUBMISSION REQUIREMENTS
    # ============================================================================
    
    # NVIDIA NIM Configuration (OPTIONAL - for AWS deployment)
    NVIDIA_NIM_ENDPOINT: Optional[str] = Field(None, description="NVIDIA NIM endpoint URL")
    NVIDIA_API_KEY: Optional[str] = Field(None, description="NVIDIA API key")
    NVIDIA_ORG_ID: Optional[str] = Field(None, description="NVIDIA organization ID")
    
    # Specific model endpoints
    LLAMA_NEMOTRON_ENDPOINT: Optional[str] = Field(None, description="Llama Nemotron endpoint")
    RETRIEVAL_NIM_ENDPOINT: Optional[str] = Field(None, description="Retrieval NIM endpoint")
    
    # Google Gemini Configuration (PRIMARY)
    GOOGLE_API_KEY: str = Field(..., description="Google Gemini API key")
    GOOGLE_MODEL: str = Field("gemini-1.5-pro", description="Google Gemini model")
    GOOGLE_EMBEDDING_MODEL: str = Field("models/embedding-001", description="Google embedding model")
    
    # ============================================================================
    # AWS CONFIGURATION
    # ============================================================================
    
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, description="AWS access key")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, description="AWS secret key")
    AWS_DEFAULT_REGION: str = Field("us-east-1", description="AWS region")
    AWS_ACCOUNT_ID: Optional[str] = Field(None, description="AWS account ID")
    
    # SageMaker Configuration
    SAGEMAKER_EXECUTION_ROLE: Optional[str] = Field(None, description="SageMaker execution role ARN")
    SAGEMAKER_INSTANCE_TYPE: str = Field("ml.g4dn.xlarge", description="SageMaker instance type")
    
    # OpenSearch Serverless (Optional for local development)
    OPENSEARCH_ENDPOINT: Optional[str] = Field(None, description="OpenSearch endpoint URL")
    OPENSEARCH_INDEX_NAME: str = Field("paper-podcast-index", description="Main index name")
    OPENSEARCH_FACTS_INDEX: str = Field("facts-index", description="Facts index name")
    OPENSEARCH_STYLE_INDEX: str = Field("style-index", description="Style index name")
    
    # S3 Configuration (Optional for local development)
    S3_BUCKET_NAME: Optional[str] = Field(None, description="S3 bucket name")
    S3_PAPERS_PREFIX: str = Field("papers/", description="S3 prefix for papers")
    S3_AUDIO_PREFIX: str = Field("audio/", description="S3 prefix for audio")
    S3_TRANSCRIPTS_PREFIX: str = Field("transcripts/", description="S3 prefix for transcripts")
    
    # ============================================================================
    # APPLICATION CONFIGURATION
    # ============================================================================
    
    # FastAPI Settings
    DEBUG: bool = Field(True, description="Debug mode")
    API_VERSION: str = Field("v1", description="API version")
    HOST: str = Field("0.0.0.0", description="Host address")
    PORT: int = Field(8000, description="Port number")
    RELOAD: bool = Field(True, description="Auto-reload on changes")
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        description="Allowed CORS origins"
    )
    ALLOWED_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE"],
        description="Allowed HTTP methods"
    )
    
    # ============================================================================
    # PROCESSING CONFIGURATION
    # ============================================================================
    
    # PDF Processing
    MAX_FILE_SIZE_MB: int = Field(50, description="Maximum file size in MB")
    CHUNK_SIZE: int = Field(1000, description="Text chunk size")
    CHUNK_OVERLAP: int = Field(200, description="Chunk overlap size")
    MIN_CHUNK_SIZE: int = Field(100, description="Minimum chunk size")
    
    # Audio Generation
    DEFAULT_VOICE_1: str = Field("Joanna", description="Amazon Polly voice for host 1")
    DEFAULT_VOICE_2: str = Field("Matthew", description="Amazon Polly voice for host 2")
    AUDIO_FORMAT: str = Field("mp3", description="Audio output format")
    SAMPLE_RATE: int = Field(22050, description="Audio sample rate")
    SILENCE_DURATION: float = Field(0.5, description="Silence duration between segments")
    
    # Episode Structure - Extended for longer podcasts
    DEFAULT_INTRO_DURATION: int = Field(120, description="Default intro duration in seconds")
    DEFAULT_CORE_DURATION: int = Field(1200, description="Default core duration in seconds (20 minutes)")
    DEFAULT_OUTRO_DURATION: int = Field(180, description="Default outro duration in seconds")
    MAX_TOTAL_DURATION: int = Field(1800, description="Maximum total duration in seconds (30 minutes)")
    
    # Podcast Generation Settings
    SEGMENTS_PER_EPISODE: int = Field(8, description="Number of segments per episode")
    WORDS_PER_SEGMENT: int = Field(200, description="Target words per segment")
    SPEAKING_RATE_WPM: int = Field(160, description="Average speaking rate in words per minute")
    
    # ============================================================================
    # COST CONTROLS (HACKATHON BUDGET MANAGEMENT)
    # ============================================================================
    
    # Budget Limits ($100 hackathon credits)
    MAX_TOTAL_COST: float = Field(95.00, description="Maximum total cost")
    COST_ALERT_THRESHOLD: float = Field(80.00, description="Cost alert threshold")
    MAX_PROCESSING_TIME: int = Field(3600, description="Max processing time per paper")
    
    # Token Limits
    MAX_TOKENS_PER_REQUEST: int = Field(4000, description="Max tokens per API request")
    MAX_TOTAL_TOKENS_PER_PAPER: int = Field(50000, description="Max total tokens per paper")
    
    # Resource Management
    AUTO_SHUTDOWN_ENDPOINTS: bool = Field(True, description="Auto-shutdown idle endpoints")
    IDLE_TIMEOUT_MINUTES: int = Field(15, description="Idle timeout in minutes")
    MAX_CONCURRENT_JOBS: int = Field(2, description="Maximum concurrent processing jobs")
    
    # ============================================================================
    # MONITORING & LOGGING
    # ============================================================================
    
    # Logging Configuration
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    LOG_FORMAT: str = Field("json", description="Log format")
    LOG_FILE: str = Field("logs/app.log", description="Log file path")
    
    # Metrics Collection
    ENABLE_METRICS: bool = Field(True, description="Enable metrics collection")
    METRICS_PORT: int = Field(9090, description="Metrics port")
    PROMETHEUS_PUSHGATEWAY: Optional[str] = Field(None, description="Prometheus pushgateway")
    
    # Error Tracking
    SENTRY_DSN: Optional[str] = Field(None, description="Sentry DSN for error tracking")
    ENVIRONMENT: str = Field("development", description="Environment name")
    
    # ============================================================================
    # EXTERNAL SERVICES (OPTIONAL)
    # ============================================================================
    
    # Redis Cache (for development)
    REDIS_URL: str = Field("redis://localhost:6379/0", description="Redis connection URL")
    CACHE_TTL: int = Field(3600, description="Cache TTL in seconds")
    
    # Database (SQLite for development)
    DATABASE_URL: str = Field("sqlite:///./podcast_gen.db", description="Database connection URL")
    
    # ============================================================================
    # DEVELOPMENT & TESTING
    # ============================================================================
    
    # Testing Configuration
    TEST_S3_BUCKET: str = Field("paper-podcast-test", description="Test S3 bucket")
    TEST_OPENSEARCH_INDEX: str = Field("test-index", description="Test OpenSearch index")
    USE_MOCK_SERVICES: bool = Field(False, description="Use mock services for testing")
    
    # Feature Flags
    ENABLE_PLAIN_LANGUAGE_MODE: bool = Field(True, description="Enable plain language mode")
    ENABLE_SEGMENT_REGENERATION: bool = Field(True, description="Enable segment regeneration")
    ENABLE_CITATION_TRACKING: bool = Field(True, description="Enable citation tracking")
    ENABLE_COST_TRACKING: bool = Field(True, description="Enable cost tracking")
    
    # Sample Data
    SAMPLE_PAPERS_DIR: str = Field("data/samples/papers", description="Sample papers directory")
    STYLE_BANK_PATH: str = Field("data/style_bank/patterns.json", description="Style bank file path")
    
    # ============================================================================
    # UI CONFIGURATION
    # ============================================================================
    
    # Streamlit Settings
    STREAMLIT_SERVER_PORT: int = Field(8501, description="Streamlit server port")
    STREAMLIT_SERVER_ADDRESS: str = Field("0.0.0.0", description="Streamlit server address")
    
    # ============================================================================
    # SECURITY
    # ============================================================================
    
    # API Security
    SECRET_KEY: str = Field("your-super-secret-jwt-key", description="JWT secret key")
    ALGORITHM: str = Field("HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="Access token expiry")
    
    # File Upload Security
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".pdf"], description="Allowed file extensions")
    MAX_UPLOAD_SIZE: int = Field(52428800, description="Max upload size in bytes")  # 50MB
    SCAN_UPLOADS: bool = Field(True, description="Scan uploads for security")
    
    # ============================================================================
    # HACKATHON DEMO CONFIGURATION
    # ============================================================================
    
    # Demo Settings
    DEMO_MODE: bool = Field(True, description="Enable demo mode")
    DEMO_PAPER_PATH: str = Field(
        "data/samples/papers/sample_research_paper.pdf",
        description="Demo paper path"
    )
    DEMO_FAST_MODE: bool = Field(True, description="Fast mode for demo")
    DEMO_SHORT_SEGMENTS: bool = Field(True, description="Short segments for demo")
    
    # Recording Settings
    DEMO_VIDEO_LENGTH: int = Field(180, description="Demo video length in seconds")
    ENABLE_SCREEN_RECORDING: bool = Field(False, description="Enable screen recording")
    DEMO_STEP_DELAYS: int = Field(2, description="Delay between demo steps")
    
    # ============================================================================
    # VALIDATORS
    # ============================================================================
    
    @validator("MAX_FILE_SIZE_MB")
    def validate_file_size(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("File size must be between 1 and 100 MB")
        return v
    
    @validator("MAX_TOTAL_COST")
    def validate_cost_limit(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("Cost limit must be between $0 and $100 for hackathon")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Helper functions for configuration
def get_model_config():
    """Get model configuration for NVIDIA NIM"""
    return {
        "llama_endpoint": settings.LLAMA_NEMOTRON_ENDPOINT,
        "retrieval_endpoint": settings.RETRIEVAL_NIM_ENDPOINT,
        "api_key": settings.NVIDIA_API_KEY,
        "max_tokens": settings.MAX_TOKENS_PER_REQUEST,
    }


def get_aws_config():
    """Get AWS configuration"""
    return {
        "region": settings.AWS_DEFAULT_REGION,
        "account_id": settings.AWS_ACCOUNT_ID,
        "sagemaker_role": settings.SAGEMAKER_EXECUTION_ROLE,
        "s3_bucket": settings.S3_BUCKET_NAME,
        "opensearch_endpoint": settings.OPENSEARCH_ENDPOINT,
    }


def get_processing_config():
    """Get processing configuration"""
    return {
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "max_duration": settings.MAX_TOTAL_DURATION,
        "voices": {
            "host_1": settings.DEFAULT_VOICE_1,
            "host_2": settings.DEFAULT_VOICE_2,
        },
        "audio_format": settings.AUDIO_FORMAT,
        "sample_rate": settings.SAMPLE_RATE,
    }


def is_demo_mode():
    """Check if running in demo mode"""
    return settings.DEMO_MODE


def get_budget_info():
    """Get current budget information"""
    return {
        "max_cost": settings.MAX_TOTAL_COST,
        "alert_threshold": settings.COST_ALERT_THRESHOLD,
        "auto_shutdown": settings.AUTO_SHUTDOWN_ENDPOINTS,
        "max_concurrent": settings.MAX_CONCURRENT_JOBS,
    }