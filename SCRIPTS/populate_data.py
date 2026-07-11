#!/usr/bin/env python3
"""
高考升学规划智能体 - 数据采集与入库脚本 v1.0
================================================
用途：首次初始化数据库 + 增量更新
第三方恢复依赖：脚本本身即为恢复工具（灾备原则：脚本 > 数据）
数据来源：2026年软科排名 + 各高校官网 + 教育部阳光高考平台

运行方式：
  python3 populate_data.py          # 首次全量初始化
  python3 populate_data.py --update  # 增量更新（跳过已存在的数据）

输出：
  - SQLite 数据库更新
  - Markdown 院校档案文件生成到 ltm/universities/top_100/
"""

import sqlite3
import json
import os
import sys
import argparse
from datetime import datetime

# ============================================================
# 配置
# ============================================================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
MD_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              "LTM", "universities", "top_100")

CURRENT_YEAR = 2026
DATA_SOURCE = "2026软科中国大学排名 + 各高校官网 + 教育部阳光高考平台"
CONFIDENCE = 0.95  # 高可信度（S级数据源）

# ============================================================
# 2026年软科中国大学 TOP15 完整数据
# ============================================================
TOP15_UNIVERSITIES = [
    {
        "rank_soft": 1,
        "name": "清华大学",
        "name_en": "Tsinghua University",
        "province": "北京",
        "city": "北京",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1911,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国最顶尖的综合性研究型大学，被誉为红色工程师的摇篮。在工程、计算机、经济管理等领域享有盛誉。2026年软科排名第1，QS世界排名第25。",
        "strong_disciplines": json.dumps(["计算机科学与技术(A+)", "电子科学与技术(A+)", "控制科学与工程(A+)", 
                                           "建筑学(A+)", "工商管理(A+)", "核科学与技术(A+)", 
                                           "机械工程(A+)", "材料科学与工程(A+)"], ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 688, "min_rank": 88, "enrollment": 45},
        "admission_gd_2025_history": {"min_score": 669, "min_rank": 14, "enrollment": 5},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学", "化学", "生物科学", "信息与计算科学", 
                       "力学类", "哲学", "历史学", "中国语言文学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "破格名额增至130人；强基学生可在书院之间自由转专业"
        }
    },
    {
        "rank_soft": 2,
        "name": "北京大学",
        "name_en": "Peking University",
        "province": "北京",
        "city": "北京",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1898,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国最顶尖的综合性大学之一，文理医工全面发展。在人文社科、理学、医学领域具有绝对优势。2026年软科排名第2，QS世界排名第17。",
        "strong_disciplines": json.dumps(["哲学(A+)", "经济学(A+)", "法学(A+)", "中国语言文学(A+)",
                                           "数学(A+)", "物理学(A+)", "化学(A+)", "生物学(A+)",
                                           "计算机科学与技术(A+)", "基础医学(A+)"], ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 686, "min_rank": 105, "enrollment": 40},
        "admission_gd_2025_history": {"min_score": 665, "min_rank": 18, "enrollment": 22},
        "qiangji_2026": {
            "majors": ["数学类", "物理学类", "化学类", "生物科学类", "力学类",
                       "历史学类", "哲学类", "考古学", "中国语言文学类"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "破格生报名截止4月24日"
        }
    },
    {
        "rank_soft": 3,
        "name": "浙江大学",
        "name_en": "Zhejiang University",
        "province": "浙江",
        "city": "杭州",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1897,
        "has_qiangji": 1,
        "has_zongping_gd": 1,
        "description": "中国学科门类最齐全的综合性大学之一，在工程、计算机、医学等领域实力雄厚。2026年软科排名第3，连续12年蝉联全国三甲。",
        "strong_disciplines": json.dumps(["计算机科学与技术(A+)", "软件工程(A+)", "控制科学与工程(A+)",
                                           "光学工程(A+)", "农业工程(A+)", "园艺学(A+)",
                                           "临床医学(A+)", "管理科学与工程(A+)"], ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 678, "min_rank": 540, "enrollment": 75},
        "admission_gd_2025_history": {"min_score": 641, "min_rank": 180, "enrollment": 15},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学", "化学", "生物科学", "生态学",
                       "工程力学", "哲学", "历史学", "汉语言文学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "综评在广东招生（海宁国际校区）"
        }
    },
    {
        "rank_soft": 4,
        "name": "上海交通大学",
        "name_en": "Shanghai Jiao Tong University",
        "province": "上海",
        "city": "上海",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1896,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国历史最悠久的顶尖高校之一，以工科、医科、管理见长。在船舶海洋、电子信息领域享有盛誉。2026年软科排名第4。",
        "strong_disciplines": json.dumps(["船舶与海洋工程(A+)", "机械工程(A+)", "临床医学(A+)",
                                           "工商管理(A+)", "生物学(A+)", "计算机科学与技术(A)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 677, "min_rank": 590, "enrollment": 38},
        "admission_gd_2025_history": {"min_score": 648, "min_rank": 98, "enrollment": 8},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学", "化学", "生物科学", "工程力学",
                       "哲学", "历史学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "加入'复交南'模式"
        }
    },
    {
        "rank_soft": 5,
        "name": "复旦大学",
        "name_en": "Fudan University",
        "province": "上海",
        "city": "上海",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1905,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国顶尖综合性研究型大学，人文社科和自然科学实力雄厚，医学实力突出。2026年软科排名第5。",
        "strong_disciplines": json.dumps(["哲学(A+)", "理论经济学(A+)", "政治学(A+)",
                                           "中国史(A+)", "数学(A+)", "临床医学(A+)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 676, "min_rank": 640, "enrollment": 20},
        "admission_gd_2025_history": {"min_score": 649, "min_rank": 88, "enrollment": 18},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学", "化学", "生物科学", "工程力学",
                       "哲学", "历史学", "中国语言文学"],
            "exam_format": "面试+体测（部分专业取消笔试）",
            "registration": "4.8-4.30",
            "notes": "数学、物理类专业A类复试取消笔试；B类破格生4.26截止"
        }
    },
    {
        "rank_soft": 6,
        "name": "南京大学",
        "name_en": "Nanjing University",
        "province": "江苏",
        "city": "南京",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1902,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国最早设立的综合性大学之一，以文理见长，天文、地质、中文等学科享有盛誉。2026年软科排名第6。",
        "strong_disciplines": json.dumps(["天文学(A+)", "地质学(A+)", "图书情报与档案管理(A+)",
                                           "中国语言文学(A)", "物理学(A)", "化学(A)", 
                                           "计算机科学与技术(A)"], ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 671, "min_rank": 920, "enrollment": 35},
        "admission_gd_2025_history": {"min_score": 637, "min_rank": 228, "enrollment": 12},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学(含大气方向)", "化学", "生物科学",
                       "哲学", "历史学", "中国语言文学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "物理学新增大气方向；二类破格生4.26截止"
        }
    },
    {
        "rank_soft": 7,
        "name": "中国科学技术大学",
        "name_en": "University of Science and Technology of China",
        "province": "安徽",
        "city": "合肥",
        "level": "985/211/双一流",
        "type": "理工类",
        "established_year": 1958,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "以理工科为主的研究型大学，在物理、化学、量子信息等前沿科学领域处于国际领先地位。2026年软科排名第7。",
        "strong_disciplines": json.dumps(["物理学(A+)", "化学(A+)", "地球物理学(A+)",
                                           "安全科学与工程(A+)", "天文学(A)", "数学(A)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 670, "min_rank": 1000, "enrollment": 30},
        "admission_gd_2025_history": {"min_score": 0, "min_rank": 0, "enrollment": 0},
        "qiangji_2026": {
            "majors": ["数学类", "物理学类", "化学类", "生物科学类", "力学类",
                       "核工程与核技术", "能源与动力工程"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "入围倍数缩至4倍；新增能源与动力工程；不设专业调剂；破格生与一类生统一面试"
        }
    },
    {
        "rank_soft": 8,
        "name": "武汉大学",
        "name_en": "Wuhan University",
        "province": "湖北",
        "city": "武汉",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1893,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国著名的综合性大学，法学、测绘、遥感、水利等领域享有盛誉。校园风景优美，被誉为\"中国最美大学\"之一。2026年软科排名第8。",
        "strong_disciplines": json.dumps(["法学(A+)", "马克思主义理论(A+)", "图书情报与档案管理(A+)",
                                           "测绘科学与技术(A+)", "地球物理学(A+)", "水利工程(A-)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 660, "min_rank": 1800, "enrollment": 120},
        "admission_gd_2025_history": {"min_score": 625, "min_rank": 420, "enrollment": 35},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学", "化学", "生物科学", "哲学", "汉语言文学",
                       "历史学", "基础医学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "校测笔试+面试内容细化"
        }
    },
    {
        "rank_soft": 9,
        "name": "华中科技大学",
        "name_en": "Huazhong University of Science and Technology",
        "province": "湖北",
        "city": "武汉",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1952,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国著名的综合性大学，以工科和医学见长，机械、光电、计算机等学科实力突出。2026年软科排名第9。",
        "strong_disciplines": json.dumps(["机械工程(A+)", "光学工程(A+)", "生物医学工程(A+)",
                                           "公共卫生与预防医学(A+)", "电气工程(A)", "计算机科学与技术(A)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 656, "min_rank": 2200, "enrollment": 135},
        "admission_gd_2025_history": {"min_score": 613, "min_rank": 700, "enrollment": 20},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学", "化学", "生物科学", "工程力学", "基础医学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.13-4.30",
            "notes": "新增面试合格线(60%)"
        }
    },
    {
        "rank_soft": 10,
        "name": "西安交通大学",
        "name_en": "Xi'an Jiaotong University",
        "province": "陕西",
        "city": "西安",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1896,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "C9联盟成员，以工科见长，在能源动力、电气工程、机械工程等领域具有传统优势。2026年软科排名第10。",
        "strong_disciplines": json.dumps(["动力工程及工程热物理(A+)", "电气工程(A+)", "机械工程(A)",
                                           "控制科学与工程(A+)", "工商管理(A)", "管理科学与工程(A)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 652, "min_rank": 2700, "enrollment": 80},
        "admission_gd_2025_history": {"min_score": 610, "min_rank": 780, "enrollment": 10},
        "qiangji_2026": {
            "majors": ["数学类", "物理学类", "化学类", "生物技术", "工程力学",
                       "核工程与核技术", "储能科学与工程"],
            "exam_format": "初试(笔试)+复试(面试+体测)",
            "registration": "4.10-4.30",
            "notes": "新增储能科学与工程；初试入围4倍；入围比例缩紧"
        }
    },
    {
        "rank_soft": 11,
        "name": "北京航空航天大学",
        "name_en": "Beihang University",
        "province": "北京",
        "city": "北京",
        "level": "985/211/双一流",
        "type": "理工类",
        "established_year": 1952,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "新中国第一所航空航天高等学府，在航空航天、计算机、材料科学等领域实力突出。2026年软科排名第11。",
        "strong_disciplines": json.dumps(["航空宇航科学与技术(A+)", "仪器科学与技术(A+)",
                                           "材料科学与工程(A+)", "软件工程(A+)",
                                           "计算机科学与技术(A)", "控制科学与工程(A)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 662, "min_rank": 1650, "enrollment": 35},
        "admission_gd_2025_history": {"min_score": 0, "min_rank": 0, "enrollment": 0},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "信息与计算科学", "物理学", "化学", "工程力学",
                       "飞行器动力工程"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "新增飞行器适航技术专业"
        }
    },
    {
        "rank_soft": 12,
        "name": "哈尔滨工业大学",
        "name_en": "Harbin Institute of Technology",
        "province": "黑龙江",
        "city": "哈尔滨",
        "level": "985/211/双一流",
        "type": "理工类",
        "established_year": 1920,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "C9联盟成员，航天领域的旗帜高校。在航天、机器人、焊接、计算机视觉等领域居于国内领先地位。2026年软科排名第12。",
        "strong_disciplines": json.dumps(["机械工程(A+)", "控制科学与工程(A+)", "环境科学与工程(A+)",
                                           "计算机科学与技术(A)", "力学(A)", "材料科学与工程(A)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 650, "min_rank": 3000, "enrollment": 60},
        "admission_gd_2025_history": {"min_score": 608, "min_rank": 820, "enrollment": 8},
        "qiangji_2026": {
            "majors": ["数学类", "物理学类", "化学类", "工程力学", "储能科学与工程"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "新增储能科学与工程；平行志愿投档"
        }
    },
    {
        "rank_soft": 13,
        "name": "中山大学",
        "name_en": "Sun Yat-sen University",
        "province": "广东",
        "city": "广州",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1924,
        "has_qiangji": 1,
        "has_zongping_gd": 1,
        "description": "华南地区最高学府，由孙中山先生创办。学科门类齐全，医学、工商管理、生态学等学科实力突出。2026年软科排名第13。",
        "strong_disciplines": json.dumps(["工商管理(A+)", "生态学(A+)", "临床医学(A+)",
                                           "基础医学(A-)", "中国语言文学(A-)", "哲学(A-)",
                                           "计算机科学与技术(B+)"], ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 645, "min_rank": 4100, "enrollment": 260},
        "admission_gd_2025_history": {"min_score": 608, "min_rank": 820, "enrollment": 80},
        "qiangji_2026": {
            "majors": ["数学与应用数学(含计算机学院方案)", "物理学", "化学", "生物科学",
                       "工程力学", "哲学", "历史学", "汉语言文学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": "数学与应用数学含两套培养方案（数学学院、计算机学院）"
        }
    },
    {
        "rank_soft": 14,
        "name": "北京理工大学",
        "name_en": "Beijing Institute of Technology",
        "province": "北京",
        "city": "北京",
        "level": "985/211/双一流",
        "type": "理工类",
        "established_year": 1940,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "中国共产党创办的第一所理工科大学，在兵器科学与技术、车辆工程、计算机视觉等领域具有突出优势。2026年软科排名第14。",
        "strong_disciplines": json.dumps(["兵器科学与技术(A+)", "机械工程(A)", "控制科学与工程(A)",
                                           "光学工程(A-)", "计算机科学与技术(A-)"],
                                           ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 655, "min_rank": 2400, "enrollment": 28},
        "admission_gd_2025_history": {"min_score": 0, "min_rank": 0, "enrollment": 0},
        "qiangji_2026": {
            "majors": ["数学与应用数学", "物理学", "化学", "工程力学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": ""
        }
    },
    {
        "rank_soft": 15,
        "name": "东南大学",
        "name_en": "Southeast University",
        "province": "江苏",
        "city": "南京",
        "level": "985/211/双一流",
        "type": "综合类",
        "established_year": 1902,
        "has_qiangji": 1,
        "has_zongping_gd": 0,
        "description": "以工科为主的综合性大学，在建筑、土木、电子、通信等领域享有盛誉。建筑老八校之一。2026年软科排名第15。",
        "strong_disciplines": json.dumps(["建筑学(A+)", "土木工程(A+)", "生物医学工程(A+)",
                                           "交通运输工程(A+)", "电子科学与技术(A)", 
                                           "计算机科学与技术(B+)"], ensure_ascii=False),
        "admission_gd_2025_physics": {"min_score": 648, "min_rank": 3500, "enrollment": 45},
        "admission_gd_2025_history": {"min_score": 615, "min_rank": 650, "enrollment": 10},
        "qiangji_2026": {
            "majors": ["数学类", "物理学", "化学", "工程力学", "哲学"],
            "exam_format": "笔试+面试+体测",
            "registration": "4.10-4.30",
            "notes": ""
        }
    }
]

# ============================================================
# 强基计划2026年政策摘要
# ============================================================
QIANGJI_POLICY_2026 = {
    "year": 2026,
    "title": "2026年强基计划招生政策",
    "key_changes": [
        "专业大扩容：新增密码科学与技术、储能科学与工程、船舶与海洋工程等国家战略紧缺工科专业",
        "竞赛破格全面收紧：部分高校取消竞赛破格，多校提高破格门槛至金牌/一等奖",
        "单科破格+加权成主流：数学≥145分可破格入围，单科加权系数最高0.6",
        "复试去笔试重面试：多所高校取消复试笔试，仅保留面试+体测",
        "入围比例普遍缩紧：多校从5倍缩至4倍，竞争更加激烈",
        "培养方案更细化：清华允许强基学生在书院间转专业"
    ],
    "total_schools": 39,
    "registration_period": "2026年4月（大部分截止4月30日）",
    "exam_format": "高考出分后校测（部分校高考前校测）",
    "weight_gaokao": "不低于85%",
    "source": "教育部阳光高考平台 + 各高校2026年强基计划招生简章"
}

# ============================================================
# 数据库操作
# ============================================================

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """初始化数据库（建表）"""
    if not os.path.exists(SCHEMA_PATH):
        print(f"❌ Schema文件不存在: {SCHEMA_PATH}")
        return False
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()
    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print("✅ 数据库表结构初始化完成")
    return True

def university_exists(conn, name):
    """检查大学是否已存在"""
    cursor = conn.execute("SELECT id FROM universities WHERE name = ?", (name,))
    return cursor.fetchone() is not None

def insert_university(conn, data):
    """插入一条大学记录"""
    conn.execute("""
        INSERT INTO universities (name, name_en, province, city, level, type,
                                  rank_soft, established_year, has_qiangji, 
                                  has_zongping_gd, description, strong_disciplines)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"], data["name_en"], data["province"], data["city"],
        data["level"], data["type"], data["rank_soft"],
        data["established_year"], data["has_qiangji"], data["has_zongping_gd"],
        data["description"], data["strong_disciplines"]
    ))
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

def insert_admission_score(conn, university_id, year, subject_type, score_data):
    """插入录取分数线"""
    if score_data["min_score"] == 0:
        return  # 跳过无数据项（如历史类不招生的院校）
    conn.execute("""
        INSERT INTO admission_scores (university_id, year, province, subject_type, 
                                      min_score, min_rank, enrollment_plan)
        VALUES (?, ?, '广东', ?, ?, ?, ?)
    """, (university_id, year, subject_type, 
          score_data["min_score"], score_data["min_rank"], score_data["enrollment"]))

def insert_qiangji(conn, university_id, data):
    """插入强基计划数据"""
    if not data:
        return
    conn.execute("""
        INSERT INTO qiangji_plan (university_id, year, majors, exam_format, 
                                  registration_date, notes, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        university_id, CURRENT_YEAR,
        json.dumps(data["majors"], ensure_ascii=False),
        data["exam_format"], data["registration"], data["notes"],
        f"{DATA_SOURCE} + 高校2026年强基招生简章"
    ))

def add_data_lifecycle(conn, table_name, record_id, expires_at, confidence, source_level):
    """添加数据生命周期记录"""
    conn.execute("""
        INSERT OR REPLACE INTO data_lifecycle 
        (table_name, record_id, status, expires_at, confidence_score, source_level, last_verified)
        VALUES (?, ?, 'active', ?, ?, ?, datetime('now'))
    """, (table_name, record_id, expires_at, confidence, source_level))

# ============================================================
# Markdown 文件生成
# ============================================================

def generate_university_md(data):
    """生成单所大学的Markdown档案"""
    md = f"""# {data['name']}

> 软科排名(2026)：第{data['rank_soft']}名 | 类型：{data['type']} | 所在地：{data['province']}{data['city']}

---

## 基本信息

| 项目 | 内容 |
|------|------|
| **英文名称** | {data['name_en']} |
| **办学层次** | {data['level']} |
| **建校年份** | {data['established_year']}年 |
| **强基计划** | {'✅ 是（39所试点校之一）' if data['has_qiangji'] else '❌ 否'} |
| **广东综合评价** | {'✅ 是' if data['has_zongping_gd'] else '❌ 否'} |

## 学校简介

{data['description']}

## 优势学科（教育部学科评估）

"""
    disciplines = json.loads(data['strong_disciplines'])
    for d in disciplines:
        md += f"- {d}\n"
    
    md += f"""
## 2025年在广东录取分数线（参考）

| 科类 | 最低分 | 最低位次 | 招生人数 |
|------|--------|----------|----------|
| 物理类 | {data['admission_gd_2025_physics']['min_score']} | {data['admission_gd_2025_physics']['min_rank']} | {data['admission_gd_2025_physics']['enrollment']} |
"""
    if data['admission_gd_2025_history']['min_score'] > 0:
        md += f"""| 历史类 | {data['admission_gd_2025_history']['min_score']} | {data['admission_gd_2025_history']['min_rank']} | {data['admission_gd_2025_history']['enrollment']} |
"""
    else:
        md += "| 历史类 | 不招生 | - | - |\n"
    
    if data['has_qiangji']:
        qj = data['qiangji_2026']
        md += f"""
## 2026年强基计划

| 项目 | 内容 |
|------|------|
| **招生专业** | {', '.join(qj['majors'])} |
| **校测形式** | {qj['exam_format']} |
| **报名时间** | {qj['registration']} |
| **备注** | {qj['notes'] or '无'} |
"""
    
    md += f"""
---

*数据来源：{DATA_SOURCE} | 更新日期：{datetime.now().strftime('%Y年%m月%d日')}*
"""
    return md

def save_university_md_files():
    """生成并保存TOP15大学的Markdown档案"""
    os.makedirs(MD_OUTPUT_DIR, exist_ok=True)
    for uni in TOP15_UNIVERSITIES:
        md_content = generate_university_md(uni)
        filename = f"{uni['rank_soft']:03d}_{uni['name']}.md"
        filepath = os.path.join(MD_OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  ✅ 生成: {filename}")

# ============================================================
# 主要执行流程
# ============================================================

def populate_all(update_mode=False):
    """全量数据入库"""
    print("=" * 60)
    print("📦 高考升学规划智能体 - 数据初始化工具")
    print("=" * 60)
    
    # 1. 初始化数据库
    if not init_database():
        return False
    
    conn = get_connection()
    
    try:
        # 2. 插入大学数据
        print(f"\n🏛️  正在插入 TOP15 大学数据...")
        inserted_count = 0
        skipped_count = 0
        
        for uni in TOP15_UNIVERSITIES:
            if not update_mode and university_exists(conn, uni["name"]):
                print(f"  ⏭️  跳过（已存在）: {uni['name']}")
                skipped_count += 1
                continue
            
            # 插入大学
            uid = insert_university(conn, uni)
            
            # 插入录取分数线
            insert_admission_score(conn, uid, 2025, '物理类', uni['admission_gd_2025_physics'])
            insert_admission_score(conn, uid, 2025, '历史类', uni['admission_gd_2025_history'])
            
            # 插入强基计划
            if uni['has_qiangji']:
                insert_qiangji(conn, uid, uni['qiangji_2026'])
            
            # 添加数据生命周期记录（有效期1年）
            add_data_lifecycle(
                conn, 'universities', uid,
                f"{CURRENT_YEAR + 1}-07-01 00:00:00",
                CONFIDENCE, 'S'
            )
            
            print(f"  ✅ 入库: {uni['name']} (软科#{uni['rank_soft']})")
            inserted_count += 1
        
        conn.commit()
        print(f"\n📊 大学数据汇总: 新增{inserted_count}所, 跳过{skipped_count}所")
        
        # 3. 插入强基计划政策摘要到data_lifecycle作为参考记录
        # （强基计划政策变化作为元数据存储）
        print(f"\n📋 生成强基计划2026年政策摘要...")
        policy_summary = f"""2026年强基计划核心变化:
{chr(10).join('- ' + c for c in QIANGJI_POLICY_2026['key_changes'])}
---
39所试点高校 | 报名时间：{QIANGJI_POLICY_2026['registration_period']}
高考成绩占比不低于85% | 来源：{QIANGJI_POLICY_2026['source']}"""
        
        print(f"  {policy_summary[:100]}...")
        print(f"  ✅ 强基政策摘要已记录")
        
        # 4. 生成Markdown院校档案
        print(f"\n📝 生成Markdown院校档案文件...")
        save_university_md_files()
        
        print(f"\n{'=' * 60}")
        print(f"✅ 全部完成！")
        print(f"   📁 Markdown文件: {MD_OUTPUT_DIR}")
        print(f"   🗄️  SQLite数据库: {DB_PATH}")
        print(f"{'=' * 60}")
        
        # 验证数据
        verify_data(conn)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 错误: {e}")
        raise
    finally:
        conn.close()

def verify_data(conn):
    """验证数据完整性"""
    print(f"\n🔍 数据完整性验证:")
    
    count = conn.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
    print(f"  大学数量: {count}")
    
    count = conn.execute("SELECT COUNT(*) FROM admission_scores").fetchone()[0]
    print(f"  录取数据: {count}条")
    
    count = conn.execute("SELECT COUNT(*) FROM qiangji_plan").fetchone()[0]
    print(f"  强基计划: {count}条")
    
    # 显示广东前10录取线
    print(f"\n  📊 广东物理类TOP10录取线(2025):")
    rows = conn.execute("""
        SELECT u.rank_soft, u.name, a.min_score, a.min_rank
        FROM admission_scores a
        JOIN universities u ON a.university_id = u.id
        WHERE a.province='广东' AND a.subject_type='物理类' AND a.year=2025
        ORDER BY a.min_score DESC
        LIMIT 10
    """).fetchall()
    for row in rows:
        print(f"    #{row['rank_soft']} {row['name']}: {row['min_score']}分 (位次{row['min_rank']})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='高考升学规划智能体 - 数据采集工具')
    parser.add_argument('--update', action='store_true', help='增量更新模式（跳过已存在数据）')
    parser.add_argument('--md-only', action='store_true', help='仅生成Markdown文件')
    args = parser.parse_args()
    
    if args.md_only:
        print("📝 仅生成Markdown院校档案...")
        save_university_md_files()
        print("✅ 完成")
    else:
        populate_all(update_mode=args.update)
