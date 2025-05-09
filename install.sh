#!/bin/bash

# mcp-vector 설치 스크립트

echo "MCP-Vector 설치를 시작합니다..."

# Python 설치 확인
if ! command -v python3 &> /dev/null; then
    echo "Python 3가 설치되어 있지 않습니다. 먼저 Python 3를 설치해주세요."
    exit 1
fi

# pip 설치 확인
if ! command -v pip3 &> /dev/null; then
    echo "pip3가 설치되어 있지 않습니다. pip3를 설치합니다..."
    python3 -m ensurepip --upgrade
fi

# 가상 환경 생성 (선택 사항)
read -p "가상 환경을 생성하시겠습니까? (y/n): " create_venv
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "가상 환경을 생성합니다..."
    python3 -m venv venv
    source venv/bin/activate
    echo "가상 환경이 활성화되었습니다."
fi

# 패키지 설치
echo "필요한 패키지를 설치합니다..."
pip3 install -e .

# 설정 파일 생성
config_dir="$HOME/.config/mcp-vector"
mkdir -p "$config_dir"

if [ ! -f "$config_dir/config.json" ]; then
    cat > "$config_dir/config.json" << EOL
{
    "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
    "db_path": "~/.mcp-vector/db",
    "watch_folders": [
        "~/Documents"
    ],
    "supported_extensions": [
        ".txt", ".md", ".py", ".js", ".java", ".c", ".cpp", ".cs",
        ".html", ".css", ".json", ".xml", ".yml", ".yaml",
        ".pdf", ".docx", ".xlsx", ".pptx"
    ],
    "host": "127.0.0.1",
    "port": 5000
}
EOL
    echo "설정 파일이 생성되었습니다: $config_dir/config.json"
fi

echo ""
echo "MCP-Vector 설치가 완료되었습니다!"
echo ""
echo "실행 방법:"
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "1. 가상 환경 활성화: source venv/bin/activate"
fi
echo "2. 서버 실행: mcp-vector --config $config_dir/config.json"
echo ""
echo "상세한 설명은 README.md 파일을 참고하세요."
