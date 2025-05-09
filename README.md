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
git clone https://github.com/iodides/mcp-vector.git
cd mcp-vector
pip install -e .
```