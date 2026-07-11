#!/bin/bash
# 高考升学规划 - 一键部署脚本
# 用法：bash deploy.sh
# 前提：Python 3.9+，pip已安装

set -e

echo "========================================"
echo "  🚀 高考升学规划 - 服务部署"
echo "========================================"

# 1. 获取脚本所在目录
cd "$(dirname "$0")"
PROJ_DIR=$(pwd)
echo "📁 项目目录: $PROJ_DIR"

# 2. 安装依赖
echo "📦 安装Python依赖..."
pip install -r "$PROJ_DIR/requirements.txt" -q

# 3. 检查配置文件
if [ ! -f "$PROJ_DIR/config.py" ]; then
    echo "❌ config.py 不存在！请先配置"
    exit 1
fi

# 4. 检查数据库
if [ ! -f "$PROJ_DIR/knowledge_base.db" ]; then
    echo "⚠️ 数据库不存在，是否从备份恢复？"
    echo "   请将 knowledge_base.db 放入 $PROJ_DIR"
fi

# 5. 检查目录结构
mkdir -p "$PROJ_DIR/download"
mkdir -p "$PROJ_DIR/uploads"

# 6. 验证代码
echo "🔍 验证代码..."
python3 "$PROJ_DIR/verify.py" || {
    echo "⚠️ 验证未全部通过，但可以继续"
}

# 7. 启动服务
echo "🌐 启动Web服务..."
PORT=$(python3 -c "from config import SERVER_PORT; print(SERVER_PORT)")
nohup python3 "$PROJ_DIR/web_rec_server.py" > "$PROJ_DIR/server.log" 2>&1 &
PID=$!
echo "   PID: $PID"
echo "   端口: $PORT"
echo "   日志: $PROJ_DIR/server.log"

sleep 3
if kill -0 $PID 2>/dev/null; then
    echo "✅ 服务已启动！"
    echo "   http://localhost:$PORT"
else
    echo "❌ 启动失败，查看日志: $PROJ_DIR/server.log"
    tail -10 "$PROJ_DIR/server.log"
    exit 1
fi

# 8. 设置cron心跳
echo "⏰ 设置心跳任务..."
(crontab -l 2>/dev/null | grep -q "$PROJ_DIR/heartbeat.py") || {
    (crontab -l 2>/dev/null; echo "0 9 * * 1,3,5 cd $PROJ_DIR && python3 heartbeat.py >> $PROJ_DIR/heartbeat.log 2>&1") | crontab -
    echo "   每周一三五上午9点自动检查"
}

echo ""
echo "========================================"
echo "  ✅ 部署完成！"
echo "========================================"
echo "  访问地址: http://localhost:$PORT"
echo "  停止服务: kill $PID"
echo "  查看日志: tail -f $PROJ_DIR/server.log"
