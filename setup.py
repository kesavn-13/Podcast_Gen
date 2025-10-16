from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="paper-podcast",
    version="1.0.0",
    author="Kesav N",
    author_email="kesavn13@example.com",
    description="An agentic system that turns research papers into verified podcast episodes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kesavn-13/Podcast_Gen",
    project_urls={
        "Bug Tracker": "https://github.com/kesavn-13/Podcast_Gen/issues",
        "Documentation": "https://github.com/kesavn-13/Podcast_Gen/docs",
        "Hackathon": "https://nvidia-aws.devpost.com/",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-mock>=3.12.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.4.8",
        ],
        "ui": [
            "streamlit>=1.28.0",
            "gradio>=4.8.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "sentry-sdk>=1.38.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "paper-podcast=app.main:main",
            "paper-podcast-ui=ui.streamlit_app:main",
            "paper-podcast-setup=scripts.setup_environment:main",
            "paper-podcast-deploy=scripts.deploy:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["data/style_bank/*.json", "data/templates/*.json"],
    },
    zip_safe=False,
)