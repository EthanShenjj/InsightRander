#!/bin/bash

# 确保后台进程在退出时被关闭
trap "kill 0" EXIT

echo "🚀 Starting InsightRadar Ecosystem..."

# 1. 启动 Flask 后端 (端口 5001)
echo "📡 Starting Flask Backend..."
(cd backend && python3 app.py) &

# 2. 启动 Next.js 前端 (端口 3000)
echo "💻 Starting Next.js Frontend..."
(cd frontend && npm run dev) &

# 等待所有后台进程
wait
