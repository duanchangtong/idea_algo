#!/bin/bash
# 阿里云函数计算 FC 一键部署脚本
# 用法: ./deploy_fc.sh

set -e

echo "=========================================="
echo "  具身智能·生活体验创意站 - FC部署"
echo "=========================================="

cd "$(dirname "$0")"

# ===== 1. 检查 Serverless Devs 是否安装 =====
if ! command -v s &> /dev/null; then
    echo "❌ 未检测到 Serverless Devs (s 命令)"
    echo "   请先安装: npm install -g @serverless-devs/s"
    echo ""
    echo "   如果没有 Node.js，先安装:"
    echo "   https://nodejs.org/ (建议 LTS 版本)"
    exit 1
fi
echo "✅ Serverless Devs: $(s --version 2>/dev/null | head -1)"

# ===== 2. 检查密钥配置 =====
if ! s config get -a default &> /dev/null; then
    echo ""
    echo "⚠️  尚未配置阿里云密钥，现在开始配置..."
    echo "   请准备你的 AccessKey ID 和 AccessKey Secret"
    echo "   获取方式: 阿里云控制台 → 右上角头像 → AccessKey管理"
    echo ""
    s config add -a default
fi
echo "✅ 密钥配置完成"

# ===== 3. 检查环境变量 =====
if [ -z "$BAILIAN_TOKEN_API_KEY" ]; then
    echo ""
    echo "⚠️  未设置 BAILIAN_TOKEN_API_KEY 环境变量"
    echo "   请执行: export BAILIAN_TOKEN_API_KEY=你的百炼API密钥"
    echo ""
    read -p "   或者直接输入API Key: " api_key
    if [ -n "$api_key" ]; then
        export BAILIAN_TOKEN_API_KEY="$api_key"
    else
        echo "   跳过AI功能，继续部署..."
    fi
fi

if [ -z "$BAILIAN_BASE_URL" ]; then
    export BAILIAN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
fi

# ===== 4. 确保 bootstrap 有执行权限 =====
chmod +x bootstrap

# ===== 5. 创建 .fcignore 排除不需要的文件 =====
cat > .fcignore << 'EOF'
.git
.gitignore
.env
.env.example
__pycache__
*.pyc
painpoints.db
app.log
.app.pid
start.sh
deploy_fc.sh
README.md
EOF
echo "✅ 已生成 .fcignore"

# ===== 6. 执行部署 =====
echo ""
echo "🚀 开始部署到阿里云函数计算..."
echo "   区域: cn-hangzhou"
echo "   函数: painpoint-platform"
echo ""

s deploy -y

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "  部署成功后，终端会输出访问地址，格式类似:"
echo "  https://painpoint-platform-xxxx.cn-hangzhou.fcapp.run"
echo ""
echo "  将该链接分享给任何人即可访问！"
echo ""
echo "  常用命令:"
echo "    s deploy -y     重新部署（代码更新后）"
echo "    s invoke        测试函数"
echo "    s logs --tail   查看实时日志"
echo "    s remove        删除函数"
echo "=========================================="
