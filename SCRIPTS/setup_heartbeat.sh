#!/bin/bash
# 设置心跳定时任务（每周一上午9点运行）
# 安装cron并写入定时任务

# 确保cron服务已安装
which crond || apt-get install -y cron 2>/dev/null

# 写入crontab
CRON_JOB="0 9 * * 1 cd /workspace/SCRIPTS && python3 heartbeat.py >> /workspace/SCRIPTS/heartbeat.log 2>&1"

# 检查是否已存在
EXISTING=$(crontab -l 2>/dev/null || echo "")
if echo "$EXISTING" | grep -q "heartbeat.py"; then
    echo "⏰ 心跳任务已存在"
else
    (echo "$EXISTING"; echo "$CRON_JOB") | crontab -
    echo "✅ 心跳任务已设置：每周一上午9点"
fi

# 立即运行一次
echo "🚀 立即运行首次心跳..."
cd /workspace/SCRIPTS && python3 heartbeat.py

# 启动cron服务
crond 2>/dev/null || echo "cron已在运行"
echo ""
echo "📋 查看心跳日志: tail -20 /workspace/SCRIPTS/heartbeat.log"
