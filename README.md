# 🧠 雪峰人AI 升学顾问

> "先谋生再谋爱" —— 基于张雪峰思维体系的高考升学规划AI

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![WorkBuddy](https://img.shields.io/badge/WorkBuddy-Skill-4a6cf7)](https://www.workbuddy.ai)

## 📋 简介

**雪峰人AI升学顾问**是一个基于张雪峰思维体系的AI升学规划专家系统。它整合了：

- 📚 **大学数据库**：中国TOP100大学 + QS全球前200大学
- 🎯 **强基/综评**：37所强基计划院校 + 8所广东综合评价策略
- 📊 **择校评估**：根据分数/排名/家庭背景推荐冲稳保院校矩阵
- 🧠 **心理支持**：备考焦虑疏导、情绪管理、学习动力维持
- 🔭 **行业前瞻**：未来10年科技趋势 + 地缘政治对就业的影响分析
- 📄 **PDF报告**：一键生成个性化升学分析报告

## 🚀 安装

### 方式一：WorkBuddy市场安装

在WorkBuddy中输入：

```
/plugin marketplace add zlandwen/gaokao-advisor
```

然后在市场中找到「雪峰人AI升学顾问」点击安装。

### 方式二：手动安装

```bash
git clone https://github.com/zlandwen/gaokao-advisor.git
cd gaokao-advisor
bash install.sh
```

## ⚙️ 配置

编辑 `SCRIPTS/config.py`：

```python
# 核心配置
SERVER_PORT = 8081           # 网页服务端口
USER_PASSWORD = "12345678"   # 登录密码
LLM_MODEL = "doubao-1.5-32k" # LLM模型
LLM_API_BASE = "..."         # API地址
LLM_API_KEY = "..."          # API密钥
```

需要准备一个兼容OpenAI接口的LLM（支持豆包、DeepSeek、OpenAI等）。

## 🎯 使用方式

### WorkBuddy对话中
| 命令 | 功能 |
|:----|:------|
| `/gaokao` | 开始升学咨询对话 |
| `/gaokao 开始` | 进入16步问答评估模式 |
| `/gaokao 报告` | 生成并导出报告 |

### 网页版
启动后访问 `http://localhost:8081`
- 预设用户：**燃爆** / **挺饱**（密码：12345678）
- 也支持「自己来」自定义评估

### 企业微信对接
```bash
python3 SCRIPTS/wecom_bot.py --config SCRIPTS/wecom_config.json
```

## 🗄️ 内置知识库

| 数据库 | 内容 |
|:-------|:-----|
| **中国大学** | 软科2026 TOP100（层次/城市/王牌学科/强基/综评）|
| **全球大学** | QS2026前200（国家/优势学科）|
| **录取数据** | 广东省近3年录取分数/位次 |
| **心理知识** | 青少年心理健康管理完整体系 |
| **行业前瞻** | 10年科技趋势 + 中美科技脱钩影响 |

## 📦 文件结构

```
gaokao-advisor/
├── SKILL.md                    ← WorkBuddy技能描述
├── .codebuddy-plugin/
│   └── marketplace.json        ← 插件市场配置
├── install.sh                  ← 一键安装脚本
├── requirements.txt            ← Python依赖
├── SCRIPTS/
│   ├── config.py               ← 集中配置（端口/密码/API Key）
│   ├── web_rec_server.py       ← 网页API服务器
│   ├── recommend.py            ← 推荐引擎核心
│   ├── generate_pdf.py         ← PDF报告生成
│   ├── wecom_bot.py            ← 企业微信机器人
│   ├── knowledge_base.db       ← 主数据库
│   ├── youth_psychology_knowledge.md  ← 心理知识库
│   └── geo_tech_outlook.md     ← 地缘科技趋势
```

## 📊 数据来源

- 软科2026中国大学排名
- QS World University Rankings 2026
- 广东省教育考试院
- 德勤《2026技术趋势》
- 智联招聘/麦可思研究院就业报告

## 📜 许可

MIT License

## 👤 维护者

- [zlandwen](https://github.com/zlandwen)
