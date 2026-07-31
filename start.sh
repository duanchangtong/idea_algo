#!/bin/bash
# 生活痛点收集站 - 启动脚本
# 用法:
#   ./start.sh          后台启动（默认）
#   ./start.sh -f       前台启动
#   ./start.sh stop     停止服务

APP_NAME="painpoint-platform"
PORT=5000
PID_FILE=".app.pid"
LOG_FILE="app.log"

# 进入脚本所在目录
cd "$(dirname "$0")"

# ===== 关闭旧进程 =====
stop_old_process() {
    # 方式1: 通过PID文件关闭
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "🛑 关闭旧进程 (PID: $OLD_PID)..."
            kill "$OLD_PID" 2>/dev/null
            sleep 1
            # 若仍未退出则强制杀死
            kill -9 "$OLD_PID" 2>/dev/null
        fi
        rm -f "$PID_FILE"
    fi

    # 方式2: 通过端口查找并关闭
    if command -v lsof &> /dev/null; then
        PIDS=$(lsof -ti :$PORT 2>/dev/null)
        if [ -n "$PIDS" ]; then
            echo "🛑 关闭占用端口 $PORT 的进程: $PIDS"
            echo "$PIDS" | xargs kill -9 2>/dev/null
            sleep 1
        fi
    elif command -v fuser &> /dev/null; then
        fuser -k ${PORT}/tcp 2>/dev/null
    fi
}

# ===== 停止命令 =====
if [ "$1" = "stop" ]; then
    stop_old_process
    echo "✅ 服务已停止"
    exit 0
fi

# ===== 启动流程 =====
echo "=========================================="
echo "  生活痛点收集站 - 启动中..."
echo "=========================================="

# 关闭旧进程
stop_old_process

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    else
        echo "❌ 未找到 Python，请先安装 Python 3.9+"
        exit 1
    fi
else
    PYTHON=python
fi

echo "📦 Python: $($PYTHON --version)"

# 安装依赖
echo "📥 安装依赖..."
$PYTHON -m pip install -r requirements.txt -q

# 检查环境变量
if [ -z "$BAILIAN_TOKEN_API_KEY" ]; then
    echo "⚠️  未设置 BAILIAN_TOKEN_API_KEY，AI建议功能将不可用"
    echo "   设置方式: export BAILIAN_TOKEN_API_KEY=你的API Key"
fi

if [ -z "$BAILIAN_BASE_URL" ]; then
    export BAILIAN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
fi

# ===== 启动服务 =====
if [ "$1" = "-f" ] || [ "$1" = "--foreground" ]; then
    # 前台启动
    echo ""
    echo "🚀 前台启动服务..."
    echo "   访问地址: http://127.0.0.1:$PORT"
    echo "   按 Ctrl+C 停止服务"
    echo "=========================================="
    $PYTHON app.py
else
    # 后台启动（默认）
    echo ""
    echo "🚀 后台启动服务..."
    nohup $PYTHON app.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 1
    echo "   PID: $(cat $PID_FILE)"
    echo "   日志: tail -f $LOG_FILE"
    echo "   停止: ./start.sh stop"
    echo "   访问: http://127.0.0.1:$PORT"
    echo "=========================================="
fi
