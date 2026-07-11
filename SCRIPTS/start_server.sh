#!/bin/bash
# 高考升学规划 - Web服务 + 心跳启动脚本
# 沙箱唤醒后运行此脚本恢复所有服务
# 使用方式: bash /workspace/SCRIPTS/start_server.sh

# 先确保cron在运行（沙箱休眠后cron可能丢失）
if ! pgrep -x crond > /dev/null; then
    echo "🔄 重启cron服务..."
    crond
fi

# 确保心跳任务在crontab中
(crontab -l 2>/dev/null | grep -q "heartbeat.py") || {
    echo "⏰ 注册心跳任务..."
    (crontab -l 2>/dev/null; echo "0 9 * * 1 cd /workspace/SCRIPTS && python3 heartbeat.py >> /workspace/SCRIPTS/heartbeat.log 2>&1") | crontab -
}

PORT=8081
PID_FILE="/tmp/gaokao_web.pid"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "✅ 服务已在运行 (PID: $OLD_PID, 端口: $PORT)"
        echo "   http://localhost:$PORT"
        exit 0
    fi
fi

# 检查端口占用
PID_ON_PORT=$(lsof -ti:$PORT 2>/dev/null)
if [ -n "$PID_ON_PORT" ]; then
    echo "⚠️  端口 $PORT 被占用 (PID: $PID_ON_PORT)，正在关闭..."
    kill -9 "$PID_ON_PORT" 2>/dev/null
    sleep 1
fi

# 启动服务
cd /workspace/SCRIPTS
nohup python3 web_rec_server.py > /tmp/gaokao_web.log 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

# 等待启动
sleep 3
if kill -0 "$PID" 2>/dev/null; then
    echo "✅ 服务已启动 (PID: $PID, 端口: $PORT)"
    echo "   http://localhost:$PORT"
    echo ""
    echo "📋 日志文件: /tmp/gaokao_web.log"
else
    echo "❌ 服务启动失败，查看日志: /tmp/gaokao_web.log"
    tail -20 /tmp/gaokao_web.log
fi
