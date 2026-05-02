"""Setup configuration for Socrates Agent Library."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="socrates-agents",
    version="0.5.0",
    author="Anthropic",
    author_email="support@anthropic.com",
    description="Socrates AI - Intelligent agent system for guided questioning and project development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anthropics/socrates",
    project_urls={
        "Bug Tracker": "https://github.com/anthropics/socrates/issues",
        "Documentation": "https://docs.socrates.ai",
        "Source Code": "https://github.com/anthropics/socrates",
    },
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    python_requires=">=3.9",
    install_requires=[
        "python-dotenv>=0.19.0",
        "pydantic>=1.10.0",
        "socratic-nexus>=0.2.0",
        "socratic-maturity>=0.1.0",
        "socratic-workflow>=0.1.0",
        "socratic-conflict>=0.1.0",
        "socratic-learning>=0.1.0",
        "socratic-docs>=0.1.0",
        "socratic-analyzer>=0.1.0",
    ],
    extras_require={
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "httpx>=0.24.0",
        ],
        "database": [
            "sqlalchemy>=2.0.0",
            "chromadb>=0.4.0",
        ],
        "full": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "httpx>=0.24.0",
            "sqlalchemy>=2.0.0",
            "chromadb>=0.4.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "socrates=socrates_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="agents ai socratic questioning education learning development",
    zip_safe=False,
)
