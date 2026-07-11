#!/usr/bin/env bash
set -e

# ═══════════════════════════════════════════════════════════════
# 雪峰人AI 升学顾问 - 一键安装脚本
# ═══════════════════════════════════════════════════════════════
# 用法: curl -fsSL https://你的域名/install.sh | bash
# ═══════════════════════════════════════════════════════════════

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }

INSTALL_DIR="${INSTALL_DIR:-/opt/gaokao-advisor}"
SKILL_DIR="${SKILL_DIR:-/root/.codebuddy/skills/gaokao-advisor}"
DOWNLOADS_URL="https://github.com/你的用户名/gaokao-advisor/releases/latest/download"

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  雪峰人AI 升学顾问 v2.0 — 一键安装${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo ""

# 检测系统
PYTHON=""
for cmd in python3.11 python3 python; do
    if command -v $cmd &>/dev/null; then PYTHON=$cmd; break; fi
done
if [ -z "$PYTHON" ]; then
    err "需要 Python 3.8+"
    exit 1
fi
ok "Python: $($PYTHON --version)"

# 安装依赖
info "安装系统依赖..."
apt-get update -qq && apt-get install -y -qq wget unzip poppler-utils supervisor nginx 2>/dev/null || true

# 创建目录
info "创建安装目录: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR/SCRIPTS" "$INSTALL_DIR/download"

# 下载核心文件（如果用GitHub发布，改为wget；如果用本地复制，直接cp）
cd "$(dirname "$0")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 复制文件
info "复制核心文件..."
for f in SCRIPTS/*.py SCRIPTS/*.html SCRIPTS/*.json SCRIPTS/*.md SCRIPTS/*.sh; do
    [ -f "$f" ] && cp "$f" "$INSTALL_DIR/$f"
done
[ -f "SCRIPTS/knowledge_base.db" ] && cp "SCRIPTS/knowledge_base.db" "$INSTALL_DIR/SCRIPTS/"
[ -f "SCRIPTS/manifest.json" ] && cp "SCRIPTS/manifest.json" "$INSTALL_DIR/SCRIPTS/"

ok "文件复制完成"

# 安装Python依赖
info "安装Python依赖..."
$PYTHON -m pip install -q flask fpdf2 pandas openpyxl requests pillow pdf2image 2>/dev/null || \
$PYTHON -m pip install --break-system-packages -q flask fpdf2 pandas openpyxl requests pillow pdf2image 2>/dev/null || true

# 检测中文字体
FONT_DIR="/usr/share/fonts"
if [ ! -f "$FONT_DIR/truetype/wqy/wqy-zenhei.ttc" ]; then
    info "安装中文字体..."
    apt-get install -y -qq fonts-wqy-zenhei 2>/dev/null || true
fi

# 配置Supervisor
info "配置守护进程..."
cat > /etc/supervisor/conf.d/gaokao-web.conf << 'SUPERVISOR'
[program:gaokao-web]
command=python3 /opt/gaokao-advisor/SCRIPTS/web_rec_server.py
directory=/opt/gaokao-advisor/SCRIPTS
autostart=true
autorestart=true
user=root
SUPERVISOR

cat > /etc/supervisor/conf.d/gaokao-http.conf << 'SUPERVISOR2'
[program:gaokao-http]
command=python3 -m http.server 8000 --bind 0.0.0.0 --directory /opt/gaokao-advisor/download
directory=/opt/gaokao-advisor/download
autostart=true
autorestart=true
user=root
SUPERVISOR2

supervisorctl update 2>/dev/null || true

# 安装为WorkBuddy Skill
if [ -d "$SKILL_DIR" ]; then
    info "更新Skill目录..."
    mkdir -p "$SKILL_DIR"
    cp "$SCRIPT_DIR/SKILL.md" "$SKILL_DIR/" 2>/dev/null || true
    ok "Skill已注册"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 安装完成！${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo "  网页版: http://localhost:8081"
echo "  下载:   http://localhost:8000"
echo "  配置:   $INSTALL_DIR/SCRIPTS/config.py"
echo ""
echo "  使用密码登录: 12345678"
echo "  预设用户: 燃爆 / 挺饱"
echo ""
echo "  📖 技能命令:"
echo "    /gaokao      开始升学咨询"
echo "    /gaokao:报告 查看我的报告"
echo "    /gaokao:问答 开始问答式评估"
echo ""

# 启动服务
info "启动服务..."
cd "$INSTALL_DIR/SCRIPTS"
nohup $PYTHON web_rec_server.py > /tmp/gaokao-web.log 2>&1 &
nohup $PYTHON -m http.server 8000 --bind 0.0.0.0 --directory "$INSTALL_DIR/download" > /tmp/gaokao-http.log 2>&1 &
sleep 2
if pgrep -f "web_rec_server" > /dev/null; then
    ok "✅ 网页服务已启动 (端口 8081)"
else
    warn "⚠️ 网页服务启动失败，查看日志: cat /tmp/gaokao-web.log"
fi

echo ""
echo -e "${YELLOW}💡 提示：修改端口/密码请编辑 config.py${NC}"
echo ""
