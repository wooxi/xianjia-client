#!/bin/bash
# 闲管家项目 - 快速同步推送到 GitHub

set -e

PROJECT_DIR="/root/.openclaw/workspace/xianjia_client"
MESSAGE="${1:-auto: 更新项目}"

cd "$PROJECT_DIR"

echo "📦 闲管家项目同步推送"
echo "===================="
echo "目录：$PROJECT_DIR"
echo "提交信息：$MESSAGE"
echo ""

# 添加所有更改
git add -A

# 检查是否有更改
if git diff --staged --quiet; then
    echo "✅ 没有需要提交的更改"
else
    # 提交
    git commit -m "$MESSAGE"
    echo "✅ 提交完成"
    
    # 推送
    git push origin master
    echo "✅ 推送完成"
fi

echo ""
echo "🔗 https://github.com/wooxi/xianjia-client"
