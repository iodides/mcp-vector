# MCP-Vector

[![PyPI version](https://badge.fury.io/py/mcp-vector.svg)](https://badge.fury.io/py/mcp-vector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README_EN.md) | 한국어

MCP-Vector는 LLM(대규모 언어 모델)이 Model Context Protocol을 통해 로컬 파일 시스템의 문서를 검색할 수 있도록 하는 벡터 검색 서버입니다. 이 도구는 여러 폴더 내의 문서에 대한 실시간 모니터링, 자동 임베딩, 효율적인 벡터 검색을 제공합니다.

## 주요 기능

- **HNSWLib 벡터 데이터베이스**: 고성능 벡터 유사성 검색
- **다국어 지원**: 다국어 임베딩 모델을 사용하여 한국어를 포함한 다양한 언어 지원
- **Model Context Protocol(MCP) 지원**: Claude, VS Code Copilot 등의 AI 도구와 통합
- **실시간 파일 모니터링**: 파일 추가, 수정, 삭제 시 자동 임베딩 업데이트
- **다양한 파일 형식 지원**: 텍스트 파일, 소스 코드, PDF, Office 문서(DOCX, XLSX, PPTX) 지원
- **HTTP API**: 벡터 검색 및 관리를 위한 REST API 제공

## 설치

### pip를 이용한 설치

```bash
pip install mcp-vector
```

### 소스코드에서 설치

```bash
git clone https://github.com/yourusername/mcp-vector.git
cd mcp-vector
pip install -e .
```

## 빠른 시작

### 기본 실행

```bash
mcp-vector --watch-folder ~/Documents --watch-folder ~/Projects
```

### 설정 파일 사용

config.json 파일 작성:

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

설정 파일로 실행:

```bash
mcp-vector --config config.json
```

## Model Context Protocol (MCP) 도구

MCP-Vector는 다음 MCP 도구를 제공합니다:

1. **vector_search**: 벡터 검색을 수행합니다.
   ```json
   {
     "query": "검색어",
     "top_k": 5,
     "paths": ["특정 경로", "..."]  // 선택 사항
   }
   ```

2. **vector_status**: 임베딩 상태를 조회합니다.
   ```json
   {}  // 파라미터 필요 없음
   ```

3. **vector_run**: 감시 폴더의 모든 파일에 대한 임베딩을 재시작합니다.
   ```json
   {
     "paths": ["특정 경로", "..."]  // 선택 사항
   }
   ```

## HTTP API

서버가 실행되면 다음 HTTP API 엔드포인트를 사용할 수 있습니다:

- `POST /api/vector/search` - 벡터 검색 수행
- `GET /api/vector/status` - 임베딩 상태 조회
- `POST /api/vector/run` - 임베딩 재시작

## VS Code 설정

VS Code와 통합하려면 다음 설정을 settings.json에 추가하세요:

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

## Claude Desktop 설정

Claude Desktop과 통합하려면 다음 설정을 ~/.config/claude-desktop/settings.json에 추가하세요:

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

## 설정 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| model_name | 임베딩 모델 이름 | paraphrase-multilingual-MiniLM-L12-v2 |
| db_path | 벡터 데이터베이스 저장 경로 | ~/.mcp-vector/db |
| watch_folders | 모니터링할 폴더 목록 | [] |
| supported_extensions | 처리할 파일 확장자 목록 | [".txt", ".md", ...] |
| host | 서버 호스트 | 127.0.0.1 |
| port | 서버 포트 | 5000 |

## 환경 변수

환경 변수를 통해 설정할 수도 있습니다:

- `MCP_VECTOR_HOST` - 서버 호스트
- `MCP_VECTOR_PORT` - 서버 포트
- `MCP_VECTOR_MODEL` - 임베딩 모델 이름
- `MCP_VECTOR_DB_PATH` - 벡터 데이터베이스 저장 경로
- `MCP_VECTOR_WATCH_FOLDERS` - 모니터링할 폴더 목록 (세미콜론으로 구분)
- `MCP_VECTOR_EXTENSIONS` - 처리할 파일 확장자 목록 (쉼표로 구분)

## 라이선스

MIT License
