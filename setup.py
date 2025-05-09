from setuptools import setup, find_packages

setup(
    name="mcp-vector",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Vector database server for LLM with Model Context Protocol",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mcp-vector",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "hnswlib>=0.7.0",
        "numpy>=1.22.0",
        "sentence-transformers>=2.2.2",
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "pydantic>=1.10.7",
        "watchdog>=3.0.0",
        "python-multipart>=0.0.5",
        "pypdf>=3.7.0",
        "python-pptx>=0.6.21",
        "openpyxl>=3.1.2",
        "python-docx>=0.8.11",
    ],
    entry_points={
        "console_scripts": [
            "mcp-vector=mcp_vector.main:main",
        ],
    },
)
