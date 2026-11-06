#!/bin/bash
# ==============================================================================
# 盲盒旅行AI (BlindBoxTravelAI) - Claude Code 专属启动器
# 双击此文件即可在 macOS 终端中自动进入项目目录、加载专属状态栏并启动 Claude Code
# ==============================================================================

PROJECT_DIR="/Users/David1/BlindBoxTravelAI"
cd "$PROJECT_DIR" || exit 1

# 针对本地网关/代理 (127.0.0.1:57321) 自动关闭服务端分类器检查提示，避免每次拦截弹窗
export CLAUDE_CODE_AUTO_MODE_SERVER=0

# 设置专属终端窗口标题与配色提示符
printf "\033]0;🎁 盲盒旅行AI (BlindBoxTravelAI) — Claude Code 研发驾驶舱\007"
clear

echo "======================================================================"
echo "  🎁 盲盒旅行AI (BlindBoxTravelAI) — Claude Code 专属工作台"
echo "  📂 工作目录: $PROJECT_DIR"
echo "  🔗 GitHub  : https://github.com/SpaceSQ/BlindBoxTravelAI"
echo "  📜 核心文档: CLAUDE.md | 01_PRD | 02_Claude交底书 | 03_Grok千里眼交底书"
echo "  🛡️  网关兼容: 已启用 CLAUDE_CODE_AUTO_MODE_SERVER=0 (静默本地代理提示)"
echo "======================================================================"
echo ""

# 确保常见 Node / Homebrew / Claude 路径已加载
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

if ! command -v claude &> /dev/null; then
    echo "⚠️  检测到当前环境尚未安装 Claude Code CLI。"
    echo "👉 正在为您提供安装指令（需已安装 Node.js 18+）："
    echo "   npm install -g @anthropic-ai/claude-code"
    echo ""
    read -p "是否现在自动为您执行安装？(y/n): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        npm install -g @anthropic-ai/claude-code
    else
        echo "您可以稍后在终端运行: npm install -g @anthropic-ai/claude-code"
        exec $SHELL
    fi
fi

echo "🚀 正在启动 Claude Code（将自动加载根目录下的 CLAUDE.md 规范）..."
echo "💡 提示：如需恢复上一次的对话界面与上下文，可随时使用 'claude --continue' 或 'claude --resume'"
echo ""

# 启动 Claude Code
claude
exec $SHELL
