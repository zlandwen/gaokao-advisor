"""
高考升学规划 - 部署配置文件
部署到云服务器时只需修改此文件中的路径和密钥
"""
import os

# ====== 项目根目录（部署时修改为服务器上的实际路径）====== 
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ====== 各模块路径 ======
SCRIPT_DIR = PROJECT_ROOT
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "download")
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge_base.db")
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
HTML_FILE = os.path.join(PROJECT_ROOT, "index_v2.html")
QUESTIONS_FILE = os.path.join(PROJECT_ROOT, "questions.json")
UPDATES_FILE = os.path.join(PROJECT_ROOT, "user_updates.json")
TRAINING_DATA = os.path.join(PROJECT_ROOT, "training_data.jsonl")
LOG_FILE = os.path.join(PROJECT_ROOT, "heartbeat.log")

# ====== LLM API配置 ======
LLM_API_BASE = "https://agiletoken.agileone.cloud"
LLM_API_KEY = "sk-bhPP9LeJ_e3h3KSMDVyc-w"
LLM_MODEL = "doubao-seed-2.0-pro-openai"

# ====== Web服务配置 ======
SERVER_PORT = 8081

# ====== 用户密码 ======
USER_PASSWORD = "F1-1402"

# ====== 构建目录 ======
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
