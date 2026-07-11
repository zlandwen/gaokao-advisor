---
name: gaokao-advisor
display_name: "🧠 雪峰人AI升学顾问"
display_name_en: "Gaokao Advisor"
description: >
  基于张雪峰思维体系的AI升学规划专家。整合中国TOP100大学数据库、QS全球前200大学排名、广东省高考录取数据、未来10年行业趋势与地缘政治分析、青少年心理健康支持。提供强基计划、综合评价、择校择专业个性化方案。支持网页端和微信端。
description_zh: >
  🧠 基于张雪峰思维体系的AI升学规划专家。
  
  📚 **数据能力**：中国TOP100大学（含录取分数/强基/综评）| QS全球前200大学 | 广东省历年高考数据 | 未来10年科技地缘趋势
  
  🎯 **核心功能**：个性化强基/综评/择校方案 | 16步问答式信息收集 | PDF报告生成与图片输出 | 心理支持陪伴 | 企业微信客服机器人
  
  💡 **雪峰人特色**：阶级追问（A5/A8不同策略）| 城市＞学校＞专业 | 数据驱动 | 就业优先 | 不模棱两可

version: 2.0.0
visibility: "public"
icon: "🧠"
category: "education"
tags: ["高考", "升学规划", "张雪峰", "志愿填报", "强基计划", "综评", "AI"]
---


# 🧠 雪峰人AI升学顾问

> "先谋生再谋爱" —— 基于张雪峰思维体系的AI升学规划专家

## 📋 核心能力

| 能力 | 说明 |
|:----|:------|
| **择校评估** | 根据成绩/排名/家庭背景推荐冲稳保院校矩阵 |
| **强基/综评规划** | 强基39校入围分析 + 广东省综评8校策略 |
| **专业推荐** | 结合未来10年科技趋势 + 地缘政治影响的专业前景评级 |
| **心理支持** | 备考焦虑疏导、情绪管理、学习动力维持 |
| **PDF报告** | 一键生成个性化升学分析报告（支持转图片） |

## 🗄️ 内置知识库

- **中国大学**：软科2026 TOP100，含层次/王牌学科/城市/强基综评标记
- **全球大学**：QS2026前200，含国家/优势学科
- **录取数据**：广东省近3年各校录取分数/位次
- **心理知识**：青少年心理健康管理（焦虑/压力/倦怠/危机干预）
- **行业前瞻**：未来10年科技趋势 + 中美脱钩对就业的影响
- **经典语录**：张雪峰核心金句/铁律/价值观库

## 🚀 快速启动

### 方式一：一键安装

```bash
# 在你的WorkBuddy环境中运行
curl -fsSL https://raw.githubusercontent.com/你的用户名/gaokao-advisor/main/install.sh | bash
```

### 方式二：手动安装

```bash
git clone https://github.com/你的用户名/gaokao-advisor.git
cd gaokao-advisor
bash install.sh
```

### 方式三：Docker

```bash
docker run -p 8081:8081 -p 8000:8000 ghcr.io/你的用户名/gaokao-advisor:latest
```

## 🎯 触发方式

### 在WorkBuddy中使用

| 命令 | 功能 |
|:----|:------|
| `/gaokao` | 开始升学咨询对话 |
| `/gaokao 开始` | 进入16步问答评估模式 |
| `/gaokao 报告` | 生成并导出我的报告 |
| `/gaokao 燃爆` | 加载燃爆的预存数据 |
| `/gaokao 挺饱` | 加载挺饱的预存数据 |

### 自然语言触发

当用户问以下问题时自动触发本Expert：
- "帮我选专业" / "什么专业好就业"
- "我考了XXX分能上什么大学"
- "强基计划怎么准备"
- "广东省综合评价有哪些学校"
- "计算机专业未来十年还有前途吗"
- "学不进去了" / "压力好大"（心理支持模式）

## ⚙️ 配置

编辑 `SCRIPTS/config.py`：

```python
# 核心配置
SERVER_PORT = 8081          # 网页服务端口
USER_PASSWORD = "12345678"  # 登录密码
LLM_MODEL = "doubao-1.5-32k"  # LLM模型
LLM_API_BASE = "..."        # API地址
LLM_API_KEY = "..."         # API密钥
```

## 🔌 企业微信对接

```bash
# 修改 wecom_config.json，填入你的企业信息
python3 wecom_bot.py --config wecom_config.json
```

## 📦 文件结构

```
gaokao-advisor/
├── SKILL.md                    ← Expert描述（本文件）
├── install.sh                  ← 一键安装脚本
├── SCRIPTS/
│   ├── config.py               ← 集中配置
│   ├── web_rec_server.py       ← 网页API服务器 (端口8081)
│   ├── recommend.py            ← 推荐引擎核心
│   ├── uni_detail.py           ← 高校详情数据
│   ├── generate_pdf.py         ← PDF报告生成
│   ├── train.py                ← 训练系统
│   ├── verify.py               ← 代码验证
│   ├── wecom_bot.py            ← 企业微信机器人
│   ├── wechat_bot.py           ← 通用微信机器人
│   ├── index_v2.html           ← 网页前端
│   ├── manifest.json           ← PWA清单
│   ├── knowledge_base.db       ← 主数据库（大学/分数/强基/综评）
│   ├── youth_psychology_knowledge.md  ← 青少年心理知识库
│   ├── geo_tech_outlook.md     ← 地缘科技趋势知识库
│   └── expand_universities.py  ← 大学数据扩展脚本
├── 核心用户画像.md
├── 燃爆_详细作战方案.md
└── 挺饱_详细作战方案.md
```

## 📊 数据来源

- 软科2026中国大学排名
- QS World University Rankings 2026
- 广东省教育考试院历年录取数据
- 智联招聘《高校毕业生就业报告》
- 麦可思研究院《中国本科生就业报告》
- 德勤《2026技术趋势》报告

## 📜 许可

MIT License — 可自由使用、修改、分享。

## 👤 作者

- 雪峰人AI — 基于WorkBuddy构建的升学规划数字人
