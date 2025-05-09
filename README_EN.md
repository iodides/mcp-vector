# MCP-Vector

[![PyPI version](https://badge.fury.io/py/mcp-vector.svg)](https://badge.fury.io/py/mcp-vector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

English | [한국어](README.md)

MCP-Vector is a vector search server that enables Large Language Models (LLMs) to search documents in the local file system via the Model Context Protocol. It provides real-time monitoring of documents across multiple folders, automatic embedding, and efficient vector search capabilities.

## Key Features

- **HNSWLib Vector Database**: High-performance vector similarity search
- **Multilingual Support**: Uses multilingual embedding models to support various languages including Korean
- **Model Context Protocol (MCP) Support**: Integration with AI tools like Claude, VS Code Copilot, etc.
- **Real-time File Monitoring**: Automatic embedding updates when files are added, modified, or deleted
- **Multiple File Format Support**: Support for text files, source code, PDFs, Office documents (DOCX, XLSX, PPTX)
- **HTTP API**: REST API for vector search and management

## Installation

### Install via pip

```bash
pip install mcp-vector
```

### Install from source

```bash
git clone https://github.com/yourusername/mcp-vector.git
cd mcp-vector
pip install -e .
```

## Quick Start

### Basic Usage

```bash
mcp-vector --watch-folder ~/Documents --watch-folder ~/Projects
```

### Using Configuration File

Create a config.json file:

```json
{
    "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
    "db_path": "~/.mcp-vector/db",
    "watch_folders": [
        "~/Documents",
        "~/Projects"
    ],
    "supported_extensions": [
        ".txt", ".md", ".py", ".js", ".java", ".c", ".cpp", ".cs",
        ".html", ".css", ".json", ".xml", ".yml", ".yaml",
        ".pdf", ".docx", ".xlsx", ".pptx"
    ]
}
```

Run with configuration file:

```bash
mcp-vector --config config.json
```

## Model Context Protocol (MCP) Tools

MCP-Vector provides the following MCP tools:

1. **vector_search**: Performs vector search.
   ```json
   {
     "query": "search query",
     "top_k": 5,
     "paths": ["specific path", "..."]  // optional
   }
   ```

2. **vector_status**: Retrieves embedding status.
   ```json
   {}  // no parameters required
   ```

3. **vector_run**: Restarts embedding for all files in monitored folders.
   ```json
   {
     "paths": ["specific path", "..."]  // optional
   }
   ```

## HTTP API

When the server is running, the following HTTP API endpoints are available:

- `POST /api/vector/search` - Perform vector search
- `GET /api/vector/status` - Check embedding status
- `POST /api/vector/run` - Restart embedding

## VS Code Integration

To integrate with VS Code, add the following to your settings.json:

```json
{
    "mcp": {
        "servers": {
            "vector": {
                "command": "mcp-vector",
                "args": [
                    "--config",
                    "${workspaceFolder}/.vscode/mcp-vector-config.json"
                ]
            }
        }
    }
}
```

## Claude Desktop Integration

To integrate with Claude Desktop, add the following to your ~/.config/claude-desktop/settings.json:

```json
{
    "servers": {
        "mcp-vector": {
            "command": "mcp-vector",
            "args": [
                "--config", 
                "~/.config/claude-desktop/mcp-vector-config.json"
            ]
        }
    }
}
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| model_name | Embedding model name | paraphrase-multilingual-MiniLM-L12-v2 |
| db_path | Vector database storage path | ~/.mcp-vector/db |
| watch_folders | List of folders to monitor | [] |
| supported_extensions | List of file extensions to process | [".txt", ".md", ...] |
| host | Server host | 127.0.0.1 |
| port | Server port | 5000 |

## Environment Variables

You can also configure using environment variables:

- `MCP_VECTOR_HOST` - Server host
- `MCP_VECTOR_PORT` - Server port
- `MCP_VECTOR_MODEL` - Embedding model name
- `MCP_VECTOR_DB_PATH` - Vector database storage path
- `MCP_VECTOR_WATCH_FOLDERS` - List of folders to monitor (semicolon-separated)
- `MCP_VECTOR_EXTENSIONS` - List of file extensions to process (comma-separated)

## License

MIT License
