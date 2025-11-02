# Paper→Podcast Project Structure

## Core Components

```
Podcast_Gen/
├── README.md                      # Hackathon submission & setup guide
├── requirements.txt              # Python dependencies
├── setup.py                     # Package installation
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Local development setup
├── Dockerfile                   # Container definition
│
├── infrastructure/              # AWS Infrastructure as Code
│   ├── terraform/               # Terraform configurations
│   │   ├── main.tf             # Main infrastructure setup
│   │   ├── sagemaker.tf        # SageMaker endpoints for NIM
│   │   ├── opensearch.tf       # OpenSearch Serverless setup
│   │   ├── s3.tf              # S3 buckets and policies
│   │   ├── iam.tf             # IAM roles and permissions
│   │   └── variables.tf        # Configuration variables
│   └── cloudformation/         # Alternative CF templates
│
├── app/                        # Main application code
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── models/                 # Pydantic models and schemas
│   │   ├── __init__.py
│   │   ├── paper.py           # Paper processing models
│   │   ├── podcast.py         # Podcast generation models
│   │   └── state.py           # State machine models
│   │
│   ├── agents/                 # Core agentic components
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Main state machine orchestrator
│   │   ├── planner.py         # Episode planning agent
│   │   ├── generator.py       # Content generation agent
│   │   ├── verifier.py        # Fact-checking agent
│   │   └── rewriter.py        # Content rewriting agent
│   │
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── pdf_processor.py   # PDF text extraction & chunking
│   │   ├── nim_client.py      # NVIDIA NIM API client
│   │   ├── embedding_service.py # Embedding generation service
│   │   ├── rag_service.py     # Dual RAG implementation
│   │   ├── tts_service.py     # Text-to-speech with Polly
│   │   ├── audio_processor.py # Audio stitching & post-processing
│   │   └── citation_tracker.py # Citation management
│   │
│   ├── storage/                # Data persistence layer
│   │   ├── __init__.py
│   │   ├── opensearch_client.py # OpenSearch operations
│   │   ├── s3_client.py       # S3 file operations
│   │   └── cache.py           # Redis/in-memory caching
│   │
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py      # File upload endpoints
│   │   │   ├── generation.py  # Podcast generation API
│   │   │   ├── playback.py    # Audio playback & streaming
│   │   │   └── monitoring.py  # Cost & performance metrics
│   │   └── middleware.py      # Auth, CORS, error handling
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── logging_config.py  # Structured logging setup
│       ├── metrics.py         # Cost & performance tracking
│       ├── validation.py      # Input validation helpers
│       └── formatting.py      # Text formatting utilities
│
├── ui/                         # User Interface
│   ├── streamlit_app.py       # Streamlit prototype UI
│   ├── components/            # Reusable UI components
│   │   ├── __init__.py
│   │   ├── upload_widget.py   # File upload component
│   │   ├── progress_tracker.py # Generation progress display
│   │   ├── audio_player.py    # Custom audio player
│   │   └── citation_viewer.py # Citation navigation
│   │
│   └── nextjs/                # Production Next.js frontend (optional)
│       ├── package.json
│       ├── pages/
│       ├── components/
│       └── styles/
│
├── data/                       # Data and assets
│   ├── style_bank/            # Conversational style templates
│   │   ├── patterns.json      # Podcast conversation patterns
│   │   ├── transitions.json   # Segment transition templates
│   │   └── personas.json      # Host personality definitions
│   │
│   ├── samples/               # Sample papers and outputs
│   │   ├── papers/           # Test research papers
│   │   ├── generated/        # Sample generated podcasts
│   │   └── benchmarks/       # Performance benchmarks
│   │
│   └── templates/             # Content templates
│       ├── episode_structure.json # Episode planning template
│       ├── script_format.json     # Script generation template
│       └── citation_format.json   # Citation formatting rules
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── unit/                  # Unit tests
│   │   ├── test_agents.py
│   │   ├── test_services.py
│   │   └── test_storage.py
│   │
│   ├── integration/           # Integration tests
│   │   ├── test_nim_integration.py
│   │   ├── test_aws_services.py
│   │   └── test_end_to_end.py
│   │
│   ├── fixtures/              # Test data and mocks
│   │   ├── sample_papers/
│   │   └── mock_responses/
│   │
│   └── conftest.py           # Pytest configuration
│
├── scripts/                   # Utility scripts
│   ├── setup_environment.py  # Environment setup automation
│   ├── deploy.py             # Deployment automation
│   ├── cost_calculator.py    # Cost estimation tool
│   ├── benchmark_performance.py # Performance testing
│   └── data_migration.py     # Data management scripts
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md       # Technical architecture guide
│   ├── API.md               # API documentation
│   ├── DEPLOYMENT.md        # Deployment instructions
│   ├── COST_ANALYSIS.md     # Cost breakdown and optimization
│   ├── DEMO_SCRIPT.md       # Demo video script
│   └── images/              # Architecture diagrams and screenshots
│
├── monitoring/               # Observability and monitoring
│   ├── cloudwatch_dashboard.json # AWS CloudWatch dashboard
│   ├── prometheus_config.yml     # Prometheus monitoring
│   └── grafana_dashboard.json    # Grafana visualization
│
└── deployment/               # Deployment configurations
    ├── k8s/                  # Kubernetes manifests
    │   ├── namespace.yaml
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── ingress.yaml
    │
    ├── helm/                 # Helm charts
    │   ├── Chart.yaml
    │   ├── values.yaml
    │   └── templates/
    │
    └── github_actions/       # CI/CD workflows
        ├── test.yml
        ├── build.yml
        └── deploy.yml
```

## Key Architecture Principles

### 1. **Agentic Design**
- State machine pattern with clear transitions
- Autonomous decision-making at each stage
- Self-correction through verification loops
- Resource-aware planning and execution

### 2. **Hackathon Compliance**
- NVIDIA NIM integration as core requirement
- AWS SageMaker deployment for scalability
- Retrieval-augmented generation with citations
- End-to-end demonstrable workflow

### 3. **Production Ready**
- Comprehensive error handling and logging
- Cost monitoring and budget controls
- Scalable infrastructure design
- Testing and documentation coverage

### 4. **User Experience**
- Intuitive upload and monitoring interface
- Real-time progress feedback
- Interactive citation navigation
- Segment-level editing capabilities

This structure supports both rapid hackathon development and future production scaling while maintaining code quality and hackathon requirements compliance.