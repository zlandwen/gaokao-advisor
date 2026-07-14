#!/usr/bin/env python3
"""
高考升学规划智能体 - 个性化推荐引擎 v1.0
============================================
基于雪峰人方法论 + 实时数据库的智能推荐系统

功能：
  1. 根据用户画像（分数/选科/偏好）推荐院校
  2. 强基/综评/高考三条路径分析
  3. 专业匹配 + 就业前景评估
  4. 个性化时间线规划

运行方式：
  python3 recommend.py                    # 交互模式
  python3 recommend.py --user 燃爆        # 查看燃爆的方案
  python3 recommend.py --user 挺饱        # 查看挺饱的方案
"""

import sqlite3
import json
import os
import sys

# DB_PATH: search in common locations
for _path in [
    "/workspace/SCRIPTS/knowledge_base.db",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.db"),
    "/workspace/DB/knowledge_base.db",
]:
    if os.path.exists(_path):
        DB_PATH = _path
        break
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.db")

# ============================================================
# 用户画像数据库
# ============================================================
USER_PROFILES = {
    "燃爆": {
        "name": "燃爆",
        "school": "深圳科学高中",
        "school_size": 1000,
        "school_tier": "深圳第二梯队头部（全市约10-12名）",
        "school_600_rate": "349人/1000人(35%+)",
        "school_special_rate": ">90%",
        "subject_type": "物理类",
        "elective": ["物理", "化学", "生物"],
        "grade_rank": "前10",
        "grade_rank_num": 8,
        "estimated_province_rank_min": 800,
        "estimated_province_rank_max": 1500,
        "estimated_province_rank": 1200,
        "estimated_score_min": 665,
        "estimated_score_max": 680,
        "estimated_score": 670,
        "target_majors_priority": ["计算机科学与技术", "人工智能", "电子信息"],
        "region_preference": ["深圳", "北京", "上海", "香港"],
        "strength_subjects": ["物理", "数学", "生物"],
        "weak_subjects": ["语文"],
        "exam_scores": {"数学": 120, "语文": 109.5, "英语": 125, "物理": 89, "化学": 84, "生物": 95},
        "exam_ranks": {"数学": 15, "语文": 380, "英语": 89, "物理": 12, "化学": 78, "生物": 16},
        "family_background": "A8-A9，父母深圳互联网公司+海外资产",
        "family_implication": "⚠️ 不适用'普通家庭生存优先'假设。金融/创业/出国等路径全面打开",
        "interests": "对理科感兴趣，最喜欢数学",
        "notes": "A8-A9家庭背景重大修正：之前的分析基于普通家庭假设，建议全面重估"
    },
    "挺饱": {
        "name": "挺饱",
        "school": "深圳北理莫斯科大学附属实验中学",
        "school_size": 513,
        "school_tier": "深圳第二梯队中游（全市约25-30名）",
        "school_600_rate": "<30%",
        "school_special_rate": ">60%",
        "subject_type": "物理类",
        "elective": ["物理", "化学", "地理"],
        "grade_rank": "50-100名",
        "grade_rank_num": 75,
        "estimated_province_rank_min": 8000,
        "estimated_province_rank_max": 15000,
        "estimated_province_rank": 10000,
        "estimated_score_min": 590,
        "estimated_score_max": 625,
        "estimated_score": 615,
        "target_majors_priority": ["计算机科学与技术", "集成电路", "地理信息科学", "教育技术"],
        "region_preference": ["深圳", "广州", "香港"],
        "strength_subjects": ["地理"],
        "weak_subjects": [],
        "exam_scores": {"数学": 99, "语文": 109.5, "英语": 110.5, "物理": 60, "化学": 80, "地理": 83},
        "exam_ranks": {"数学": 133, "语文": 136, "英语": 124, "物理": 113, "化学": 107, "地理": 29},
        "family_background": "A8-A9，父母深圳互联网公司+海外资产",
        "family_implication": "⚠️ 不适用普通家庭假设。找资产10亿对象的目标因家庭背景而变得可行",
        "interests": "想当老师（3个月假期）；想找资产10亿的结婚对象",
        "notes": "家庭背景A8-A9重大修正：师范的动机从'谋生'变为'圈子'；出国/创业/接班都可行"
    }
}

# ============================================================
# 数据库查询
# ============================================================

def get_conn():
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH)

def query_universities_by_score(score, subject_type="物理类", limit=15):
    """根据分数推荐大学"""
    conn = get_conn()
    if not conn:
        return []
    
    # 查找录取线在 score±30 范围内的院校
    conn.row_factory = None  # 返回元组
    cursor = conn.execute("""
        SELECT u.name, u.level, u.rank_soft, u.province, u.city, u.has_qiangji, 
               u.has_zongping_gd, a.min_score, a.min_rank, a.enrollment_plan
        FROM admission_scores a
        JOIN universities u ON a.university_id = u.id
        WHERE a.province='广东' AND a.subject_type=? AND a.year=2025
          AND a.min_score BETWEEN ? AND ?
        ORDER BY a.min_score DESC
        LIMIT ?
    """, (subject_type, score - 30, score + 15, limit))
    
    cols = ["name","level","rank_soft","province","city","has_qiangji","has_zongping_gd",
            "min_score","min_rank","enrollment_plan"]
    results = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return results

def query_qiangji_schools():
    """查询有强基计划的院校"""
    conn = get_conn()
    if not conn:
        return []
    conn.row_factory = None
    cursor = conn.execute("""
        SELECT u.name, u.rank_soft, u.level, u.province,
               q.majors, q.exam_format, q.registration_date, q.notes
        FROM qiangji_plan q
        JOIN universities u ON q.university_id = u.id
        WHERE q.year = 2026
        ORDER BY u.rank_soft
    """)
    cols = ["name","rank_soft","level","province","majors","exam_format","registration_date","notes"]
    results = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return results

def query_zongping_schools():
    """查询广东综评院校"""
    conn = get_conn()
    if not conn:
        return []
    conn.row_factory = None
    cursor = conn.execute("""
        SELECT u.name, u.level, u.rank_soft, z.majors, z.exam_format,
               z.weight_gaokao, z.enrollment_count
        FROM zongping_plan z
        JOIN universities u ON z.university_id = u.id
        ORDER BY u.rank_soft
    """)
    cols = ["name","level","rank_soft","majors","exam_format","weight_gaokao","enrollment_count"]
    results = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return results

def get_admission_trend(university_name):
    """查询某校在广东的录取趋势"""
    conn = get_conn()
    if not conn:
        return []
    cursor = conn.execute("""
        SELECT year, min_score, min_rank, enrollment_plan
        FROM admission_scores a
        JOIN universities u ON a.university_id = u.id
        WHERE u.name=? AND a.province='广东' AND a.subject_type='物理类'
        ORDER BY a.year DESC
    """, (university_name,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

# ============================================================
# 推荐引擎核心逻辑
# ============================================================

class AdmissionRecommender:
    """基于雪峰人方法论的推荐引擎"""
    
    def __init__(self, user_profile):
        self.user = user_profile
        self.score = user_profile["estimated_score"]
        self.rank = user_profile["estimated_province_rank"]
        self.subject_type = user_profile["subject_type"]
        self.majors = user_profile["target_majors_priority"]
        self.region = user_profile["region_preference"]
        self.strengths = user_profile["strength_subjects"]
    
    def score_to_segment(self):
        """分数段定位（雪峰人方法论04）"""
        s = self.score
        if s >= 680: return "S段", "清北复交浙任选"
        if s >= 660: return "A+段", "C9/华五主力层"
        if s >= 640: return "A段", "中坚985"
        if s >= 610: return "B+段", "普通985/顶尖211"
        if s >= 580: return "B段", "211主力层"
        if s >= 550: return "C+段", "双一流/一本"
        return "C段", "省属重点/特色院校"
    
    def rank_chongwenbao(self):
        """冲稳保三档推荐"""
        score = self.score
        rank = self.rank
        
        # 冲一冲：高10-20分
        chong = query_universities_by_score(score + 15, self.subject_type, 5)
        # 稳一稳：±5分
        wen = query_universities_by_score(score, self.subject_type, 8)
        # 保一保：低10-20分
        bao = query_universities_by_score(score - 12, self.subject_type, 5)
        
        return {
            "chong": chong[:5],
            "wen": wen[:8],
            "bao": bao[:5]
        }
    
    def analyze_qiangji(self):
        """强基计划分析"""
        segment, _ = self.score_to_segment()
        qiangji_schools = query_qiangji_schools()
        
        # 筛选适合的强基院校
        suitable = []
        for s in qiangji_schools:
            # 只选排名比自己当前水平高的
            if s["rank_soft"] and s["rank_soft"] < 20:  # 前20的强基院校
                suitable.append(s)
        
        is_recommended = segment in ["S段", "A+段"]
        
        return {
            "recommended": is_recommended,
            "reason": "强基计划适合分数在目标校边缘且有学科特长的考生" if is_recommended else "当前分数段不建议主攻强基（限报1所风险大）",
            "suitable_schools": suitable[:5],
            "tip_2026": self._get_qiangji_tip()
        }
    
    def _get_qiangji_tip(self):
        """2026年强基特别提示"""
        tips = []
        for subj in self.strengths:
            if subj == "数学":
                tips.append("数学≥145分可关注华南理工、天津大学单科破格政策")
            if subj == "物理":
                tips.append("物理强可关注电子科大、华南理工的单科加权政策")
            if subj == "化学":
                tips.append("化学强可关注华工化生类（化学加权0.6）")
        return tips
    
    def analyze_zongping(self):
        """综合评价分析"""
        zongping_schools = query_zongping_schools()
        
        # 按层次分类
        high_level = [z for z in zongping_schools if "985" in (z.get("level","") or "")]
        medium_level = [z for z in zongping_schools if "985" not in (z.get("level","") or "")]
        
        return {
            "recommended": True,
            "reason": "综合评价是广东考生的优势通道，可报多所互不影响",
            "high_level": high_level,
            "medium_level": medium_level,
            "tip": "广东综评可同时报多所，建议把能报的都报上"
        }
    
    def recommend_majors(self):
        """专业推荐——带推荐高校的配对推荐"""
        score = self.score
        
        recommendations = []
        
        is_wealthy = "A8" in self.user.get("family_background", "") or "A9" in self.user.get("family_background", "")
        life_dir = self.user.get("life_direction", "").strip()
        is_entrepreneur = any(k in life_dir for k in ["创业","开公司","自己干"])
        is_successor = any(k in life_dir for k in ["接班","继承","管理家族"])
        is_teacher = any(k in life_dir for k in ["当老师","教书","师范","教师"])
        is_abroad = any(k in life_dir for k in ["出国","留学","海外"])
        has_geo = "地理" in self.user.get("elective", [])
        
        # 根据分数段确定推荐院校层级
        # S段(680+)：清北
        # A+段(660-679)：C9
        # A段(640-659)：中坚985
        # B+段(610-639)：211/综评985
        # B段(580-609)：深大/华师/广工
        
        # ====== 计算机科学与技术（基础盘：几乎所有人都会推荐） ======
        cs_reason = ""
        if is_entrepreneur: cs_reason = "想创业？计算机是最好的起点。"
        elif is_successor: cs_reason = "想接家族企业？技术在手才不会被下属忽悠。"
        elif is_abroad: cs_reason = "计算机全球通用，出国也好找工作。"
        else: cs_reason = "计算机是硬通货，不进化就淘汰。"
        
        cs_schools = self._pick_schools("计算机", score)
        recommendations.append({
            "major": "计算机科学与技术",
            "schools": cs_schools,
            "priority": "🥇 强推",
            "reason": cs_reason,
            "suitable": score >= 580,
            "note": "雪峰人：低端饱和高端缺人。大一大二死磕算法和数学。"
        })
        
        # ====== 人工智能 ======
        ai_note = "想做AI算法得读到硕博。"
        if is_entrepreneur: ai_note += " AI创业是风口。"
        ai_schools = self._pick_schools("人工智能", score)
        recommendations.append({
            "major": "人工智能",
            "schools": ai_schools,
            "priority": "🥇 强推" if score >= 640 else "🥈 推荐",
            "reason": "未来十年最热赛道，2026年AI岗薪资涨18%。",
            "suitable": score >= 620,
            "note": ai_note
        })
        
        # ====== 集成电路/电子 ======
        ic_schools = self._pick_schools("集成电路", score)
        recommendations.append({
            "major": "集成电路/电子",
            "schools": ic_schools,
            "priority": "🥇 强推",
            "reason": "卡脖子领域，大基金3440亿砸进去，人才缺口30万。",
            "suitable": score >= 580,
            "note": "雪峰人：唯一可以靠'国家战略'吃饭的专业。"
        })
        
        # ====== 机器人工程 ======
        robo_schools = self._pick_schools("机器人", score)
        recommendations.append({
            "major": "机器人工程",
            "schools": robo_schools,
            "priority": "🥈 推荐",
            "reason": "制造业升级+老龄化，机器人需求只增不减。",
            "suitable": score >= 580,
            "note": "深圳大疆优必选都在招，动手能力越强越吃香。"
        })
        
        # ====== 师范 ======
        teacher_priority = "🥇 强推"
        if score >= 640 and not is_teacher: teacher_priority = "🥈 推荐"
        teacher_schools = self._pick_schools("师范", score)
        recommendations.append({
            "major": "师范（公费师范生/信息技术方向）",
            "schools": teacher_schools,
            "priority": teacher_priority,
            "reason": "编制+寒暑假+越老越吃香。深圳教师年薪25-40万。",
            "suitable": score >= 540,
            "note": "公费师范生优先。别只盯着深圳，珠三角遍地是机会。"
        })
        
        # ====== 地理信息科学（物化地特有） ======
        if has_geo:
            geo_schools = self._pick_schools("地理信息", score)
            recommendations.append({
                "major": "地理信息科学/遥感",
                "schools": geo_schools,
                "priority": "🥈 特有优势",
                "reason": "物化地组合的独特路径，竞争小方向独特。",
                "suitable": True,
                "note": "武大该专业全球领先，智慧城市需求大。"
            })
        
        # ====== 商科/管理（仅A8-A9家庭） ======
        if is_wealthy:
            biz_schools = self._pick_schools("商科", score, wealthy=True)
            recommendations.append({
                "major": "商科/管理（企业管理方向）",
                "schools": biz_schools,
                "priority": "🥇 强推（限A8-A9）",
                "reason": "未来要继承或管理家族企业，技术+商科是黄金组合。",
                "suitable": True,
                "note": ""
            })
            fin_schools = self._pick_schools("金融", score, wealthy=True)
            recommendations.append({
                "major": "金融/金融科技",
                "schools": fin_schools,
                "priority": "🥇 推荐（限A8-A9）",
                "reason": "家里有资源，金融是高回报赛道。",
                "suitable": True,
                "note": "但必须考上清北复交人+港三校+国外TOP30才有意义。"
            })
        
        return [r for r in recommendations if r.get("suitable", True)]
    
    def _pick_schools(self, major, score, wealthy=False):
        """根据分数和学科匹配推荐院校"""
        # 分分数段的推荐院校映射
        s_schools = {  # 680+（清北段）
            "计算机": [("清华大学","A+"),("北京大学","A+"),("浙江大学","A+")],
            "人工智能": [("清华大学","A+"),("北京大学","A+"),("上海交通大学","A+"),("浙江大学","A+")],
            "集成电路": [("清华大学","A+"),("北京大学","A+"),("复旦大学","A"),("电子科技大学","A+")],
            "机器人": [("哈尔滨工业大学","A+"),("北京航空航天大学","A+"),("华中科技大学","A+")],
            "师范": [("北京师范大学","A+"),("华东师范大学","A+")],
            "金融": [("北京大学","A+"),("清华大学","A+"),("复旦大学","A+"),("上海交通大学","A+"),("中国人民大学","A+")],
            "商科": [("香港大学","QS17"),("香港科技大学","QS44"),("北京大学","A+"),("复旦大学","A+")],
            "地理信息": [("武汉大学","A+"),("南京大学","A"),("北京大学","A")],
        }
        a_schools = {  # 660-679（C9段）
            "计算机": [("浙江大学","A+"),("上海交通大学","A"),("南京大学","A"),("中国科学技术大学","A")],
            "人工智能": [("浙江大学","A+"),("上海交通大学","A+"),("南京大学","A"),("中国科学技术大学","A")],
            "集成电路": [("复旦大学","A"),("电子科技大学","A+"),("西安电子科技大学","A+"),("东南大学","A")],
            "机器人": [("哈尔滨工业大学","A+"),("华中科技大学","A+"),("上海交通大学","A")],
            "师范": [("北京师范大学","A+"),("华东师范大学","A+")],
            "金融": [("复旦大学","A+"),("上海交通大学","A+"),("中国人民大学","A+")],
            "商科": [("香港大学","QS17"),("香港中文大学","QS32"),("复旦大学","A+")],
            "地理信息": [("武汉大学","A+"),("南京大学","A")],
        }
        b_schools = {  # 640-659（中坚985段）
            "计算机": [("华中科技大学","A"),("电子科技大学","A"),("北京航空航天大学","A"),("中山大学","A-")],
            "人工智能": [("华中科技大学","A"),("电子科技大学","A"),("中山大学","A-")],
            "集成电路": [("电子科技大学","A+"),("西安电子科技大学","A+"),("华南理工大学","B+")],
            "机器人": [("华中科技大学","A+"),("哈尔滨工业大学","A+"),("华南理工大学","B+")],
            "师范": [("北京师范大学","A+"),("华东师范大学","A+"),("华南师范大学","A-")],
            "金融": [("上海财经大学","A"),("中央财经大学","A+"),("对外经济贸易大学","A")],
            "商科": [("香港中文大学(深圳)","合作"),("上海财经大学","A")],
            "地理信息": [("武汉大学","A+"),("中山大学","B+")],
        }
        c_schools = {  # 610-639（211/综评段）
            "计算机": [("华南理工大学","B+"),("深圳大学","B+"),("南方科技大学","-"),("电子科技大学","A")],
            "人工智能": [("南方科技大学","-"),("华南理工大学","B+"),("深圳大学","B+")],
            "集成电路": [("华南理工大学","B+"),("南方科技大学","-"),("广东工业大学","B")],
            "机器人": [("华南理工大学","B+"),("深圳大学","B+"),("广东工业大学","B")],
            "师范": [("华南师范大学","A-"),("南京师范大学","A-"),("华中师范大学","A")],
            "金融": [("暨南大学","B+"),("深圳大学","B+"),("广东外语外贸大学","B")],
            "商科": [("香港中文大学(深圳)","合作"),("暨南大学","B+")],
            "地理信息": [("武汉大学","A+"),("中山大学","B+"),("华南师范大学","B+")],
        }
        d_schools = {  # 580-609
            "计算机": [("深圳大学","B+"),("广东工业大学","B"),("广州大学","C+")],
            "集成电路": [("广东工业大学","B"),("深圳大学","B+"),("南方科技大学","-")],
            "机器人": [("广东工业大学","B"),("深圳大学","B+")],
            "师范": [("华南师范大学","A-"),("广州大学","C+"),("广东技术师范大学","C")],
            "金融": [("深圳大学","B+"),("广东外语外贸大学","B")],
            "商科": [("深圳大学","B+"),("广东外语外贸大学","B")],
            "地理信息": [("华南师范大学","B+"),("广州大学","C+")],
        }
        
        if score >= 680:
            pool = s_schools
        elif score >= 660:
            pool = a_schools
        elif score >= 640:
            pool = b_schools
        elif score >= 610:
            pool = c_schools
        else:
            pool = d_schools
        
        # 如果是A8-A9家庭，商科/金融推荐顶尖院校
        if wealthy and score >= 640:
            pool = s_schools if score >= 660 else b_schools
            
        return pool.get(major, [])
    
    def generate_timeline(self):
        """生成个性化时间线"""
        from datetime import datetime
        current_year = 2026
        current_month = 7
        life_dir = self.user.get("life_direction", "")
        is_entrepreneur = any(k in life_dir for k in ["创业","开公司","自己干","AI创业"])
        is_successor = any(k in life_dir for k in ["接班","继承"])
        
        timeline = []
        
        # 当前暑假
        summer_tasks = ["确定目标院校和专业方向"]
        if self.score >= 650:
            summer_tasks.append("刷强基校测题（数学+物理竞赛基础）")
        else:
            summer_tasks.append("查漏补缺，重点提升数学和英语")
        if is_entrepreneur:
            summer_tasks.append("了解科技创业案例，看3本创业入门书")
        elif is_successor:
            summer_tasks.append("暑假去家族企业实习一周，了解业务流程")
        summer_tasks.append("开始了解综评院校的特点和要求")
        summer_tasks.append("制定高二学习计划")
        
        timeline.append({
            "period": f"{current_year}年7-8月（暑假）",
            "tasks": summer_tasks
        })
        
        # 高二上
        timeline.append({
            "period": f"{current_year}年9月-{current_year+1}年1月（高二上）",
            "tasks": [
                "保持成绩，燃爆目标年级前10，挺饱目标年级前50",
                "数学/物理/英语重点突破",
                "关注2027年强基/综评政策动态",
                "开始准备综评材料（竞赛/活动/社会实践）"
            ]
        })
        
        # 高二下
        timeline.append({
            "period": f"{current_year+1}年2-7月（高二下）",
            "tasks": [
                "全力保持成绩",
                "参加学业水平考试",
                "暑假开始高三一轮复习",
                "确定强基/综评目标校"
            ]
        })
        
        # 高三
        timeline.append({
            "period": f"{current_year+1}年8月-{current_year+2}年6月（高三）",
            "tasks": [
                "一轮复习、二轮复习、三轮冲刺",
                f"{current_year+2}年4月：强基计划报名（如适用）",
                f"{current_year+2}年5月：综合评价报名",
                f"{current_year+2}年6月7-9日：高考 🎯",
                "6月中旬：综评校测",
                "6月底：出分+强基校测",
                "7月：志愿填报+录取"
            ]
        })
        
        return timeline
    
    def generate_future_outlook(self):
        """生成未来10年行业趋势与就业前瞻分析"""
        life_dir = self.user.get("life_direction", "").strip()
        interests = self.user.get("interests", "")
        family = self.user.get("family_background", "")
        is_wealthy = "A8" in family or "A9" in family
        is_tech = any(k in (life_dir + interests) for k in ["AI","计算机","编程","技术","创业","互联网"])
        is_teacher = "师范" in life_dir or "教师" in life_dir or "老师" in life_dir
        
        outlook = {
            "top_industries_10y": [
                "人工智能全产业链（国产AI芯片、大模型、人形机器人）",
                "新能源与储能（光伏/风电/固态电池/氢能）",
                "半导体与先进制造（国产替代主线）",
                "生物医药与生命科技（老龄化+基因技术）",
                "低空经济（无人机+eVTOL飞行器）"
            ],
            "geo_impact": "",
            "career_advice_10y": [],
            "risk_warning": ""
        }
        if is_tech:
            outlook["geo_impact"] = "中美科技脱钩=国产替代红利10年。你选技术方向正好踩在国家战略上"
        elif is_teacher:
            outlook["geo_impact"] = "教师行业受地缘影响小，稳定性高。注意深圳教师编制在收紧"
        else:
            outlook["geo_impact"] = "中美博弈长期化，选专业应优先考虑国家重点扶持产业方向"
        
        outlook["career_advice_10y"] = [
            "AI工具使用能力是2030年后的生存底线，无论什么专业都必须掌握",
            "没有一劳永逸的专业，持续学习能力比专业本身更重要",
            "城市大于学校大于专业：深圳/广州的实习机会碾压内陆城市",
            "本科打基础、硕士定方向——学历通胀下硕士已是标配",
            "技术+管理/技术+产品的复合型人才最抗周期波动"
        ]
        if is_wealthy:
            outlook["career_advice_10y"].insert(0, "A8-A9家庭优先考虑技术+管理路径，本科STEM+硕士商科")
        else:
            outlook["career_advice_10y"].insert(0, "普通家庭选确定性高的赛道（计算机/电子/电气），第一份工作必须能养活自己")
        
        risks = []
        if "文科" in interests or any(k in interests for k in ["历史","文学","哲学","新闻"]):
            risks.append("传统文科受AI冲击最大，建议文科+技能复合")
        if "金融" in interests and not is_wealthy:
            risks.append("普通家庭慎入金融——高端金融岗拼资源不是学历")
        if is_teacher and self.score and self.score > 640:
            risks.append("你这分数段当老师性价比偏低，AI+技术赛道长线收益更高")
        outlook["risk_warning"] = "；".join(risks) if risks else "你的选择方向目前风险可控"
        return outlook

    def _compute_score_min(self, score, exam_ranks, school):
        """根据分数、排名和学校计算分数范围下限（与JS引擎逻辑一致）"""
        rank = 999
        if exam_ranks:
            vals = [v for v in exam_ranks.values() if v > 0]
            if vals: rank = min(vals)
        is_top_school = any(kw in school for kw in ["深中","深圳中学","实验","高级","外国","科学","科高","深科","红岭","育才","宝安","华附","省实","执信"])
        if rank <= 3 and is_top_school:
            return score - 5
        return score - 15

    def _compute_score_max(self, score, exam_ranks, school):
        """根据分数、排名和学校计算分数范围上限"""
        rank = 999
        if exam_ranks:
            vals = [v for v in exam_ranks.values() if v > 0]
            if vals: rank = min(vals)
        is_top_school = any(kw in school for kw in ["深中","深圳中学","实验","高级","外国","科学","科高","深科","红岭","育才","宝安","华附","省实","执信"])
        if rank > 0 and rank <= 10 and is_top_school:
            upward = max(0, (11 - rank)) * 3  # #2→27, #5→18
            return min(score + upward + 15, score + 40)
        return score + 15

    def generate_full_report(self):
        """生成完整推荐报告"""
        segment, segment_desc = self.score_to_segment()
        cwb = self.rank_chongwenbao()
        qiangji = self.analyze_qiangji()
        zongping = self.analyze_zongping()
        majors = self.recommend_majors()
        timeline = self.generate_timeline()
        outlook = self.generate_future_outlook()
        
        scores = self.user.get("exam_scores", {})
        top_unis = []
        seen = set()
        for level_key in ["chong","wen","bao"]:
            for school in cwb.get(level_key, []):
                name = school.get("name","")
                if name and name not in seen:
                    seen.add(name)
                    top_unis.append({"name": name, "level": level_key, "source": "冲稳保"})
        for m in majors:
            if m.get("suitable"):
                for s in m.get("schools", []):
                    name = s if isinstance(s, str) else (s[0] if isinstance(s, tuple) else s.get("school",""))
                    if name and name not in seen and len(top_unis) < 5:
                        seen.add(name)
                        top_unis.append({"name": name, "level": "wen", "source": m.get("major","")})
        top3 = top_unis[:3]
        for i, u in enumerate(top3):
            u["stars"] = 3 - i

        # 旧continue
        weak_analysis = []
        ranks = self.user.get("exam_ranks", {})
        school_size = self.user.get("school_size", 500)
        for subj, rank in ranks.items():
            pct = rank / school_size
            if pct > 0.30:  # 排名在30%以后
                weak_analysis.append(f"{subj}(#{rank}/{school_size}, top {pct*100:.0f}%) — ⚠️ 偏弱，有提升空间")
            elif pct > 0.15:
                weak_analysis.append(f"{subj}(#{rank}/{school_size}, top {pct*100:.0f}%) — ➡️ 中等")
            else:
                weak_analysis.append(f"{subj}(#{rank}/{school_size}, top {pct*100:.0f}%) — ✅ 优势")
        
        return {
            "user_name": self.user["name"],
            "user_school": self.user["school"],
            "school_tier": self.user.get("school_tier", ""),
            "school_size": self.user.get("school_size", 500),
            "estimated_province_rank_min": self.user.get("estimated_province_rank_min", 0),
            "estimated_province_rank_max": self.user.get("estimated_province_rank_max", 0),
            # 以下为预估分数范围，如果profile中已有则使用，否则按rank+school推算
            "estimated_score_min": self.user.get("estimated_score_min", self._compute_score_min(self.user.get("estimated_score", 0), self.user.get("exam_ranks", {}), self.user.get("school", ""))),
            "estimated_score_max": self.user.get("estimated_score_max", self._compute_score_max(self.user.get("estimated_score", 0), self.user.get("exam_ranks", {}), self.user.get("school", ""))),
            "family_background": self.user.get("family_background", ""),
            "family_implication": self.user.get("family_implication", ""),
            "exam_scores": scores,
            "exam_ranks": self.user.get("exam_ranks", {}),
            "interests": self.user.get("interests", ""),
            "weak_analysis": weak_analysis,
            "segment": {"level": segment, "description": segment_desc},
            "chong_wen_bao": cwb,
            "qiangji": qiangji,
            "zongping": zongping,
            "majors": majors,
            "timeline": timeline,
            "future_outlook": outlook,
            "top3_unis": top3
        }


# ============================================================
# 报告显示
# ============================================================

def print_report(report):
    """打印推荐报告"""
    print(f"\n{'='*60}")
    print(f"📋 {report['user_name']}的个性化升学方案")
    print(f"🏫 {report['user_school']}")
    
    # 学校定位信息
    if "school_tier" in report:
        print(f"📈 学校定位：{report['school_tier']}")
    if "estimated_score_min" in report:
        print(f"🎯 省排名预估：{report['estimated_province_rank_min']}-{report['estimated_province_rank_max']}名")
        print(f"🎯 分数预估范围：{report['estimated_score_min']}-{report['estimated_score_max']}分")
    
    # 家庭背景信息
    if "family_background" in report:
        print(f"🏠 家庭背景：{report['family_background']}")
        print(f"⚠️  {report['family_implication']}")
    
    print(f"{'='*60}")
    
    # 成绩数据
    if "exam_scores" in report:
        scores = report["exam_scores"]
        ranks = report.get("exam_ranks", {})
        school_size = report.get("school_size", 500)
        print(f"\n📝 高一下期末成绩 + 年级排名：")
        print(f"   {'科目':>4} | {'分数':>4} | {'年级排名':>6} | 评价")
        print(f"   {'-'*4}-+-{'-'*4}-+-{'-'*6}-+------")
        
        sorted_subjects = sorted(scores.keys(), 
                                 key=lambda s: ranks.get(s, 999)/school_size if s in ranks else 999)
        for subj in sorted_subjects:
            score = scores.get(subj, 0)
            rank = ranks.get(subj, 0)
            pct = rank / school_size if school_size else 1
            
            if pct <= 0.10: flag = "✅ 优势"
            elif pct <= 0.25: flag = "➡️ 中等"
            elif pct <= 0.40: flag = "⚠️ 偏弱"
            else: flag = "🔴 短板"
            
            if isinstance(score, (int, float)):
                print(f"   {subj:>4} | {score:>4} | #{rank:>4} | {flag} (top {pct*100:.0f}%)")
        
        print(f"\n📊 学校总人数：物理类约{int(school_size)}人")
    
    if "interests" in report:
        print(f"🎯 个人偏好：{report['interests']}")
    
    if "weak_analysis" in report:
        print(f"\n🔍 弱科诊断：")
        for w in report["weak_analysis"]:
            print(f"  {w}")
    
    # 分数段
    seg = report["segment"]
    print(f"\n📊 分数段定位：{seg['level']} — {seg['description']}")
    
    # 冲稳保
    cwb = report["chong_wen_bao"]
    print(f"\n🎯 冲稳保推荐（基于2025广东录取数据）：")
    
    if cwb["chong"]:
        print(f"\n  🚀 冲一冲：")
        for u in cwb["chong"]:
            print(f"    {u['name']} ({u['level']}) — {u['min_score']}分 / {u['min_rank']}位次")
    
    if cwb["wen"]:
        print(f"\n  ✅ 稳一稳：")
        for u in cwb["wen"]:
            print(f"    {u['name']} ({u['level']}) — {u['min_score']}分 / {u['min_rank']}位次")
    
    if cwb["bao"]:
        print(f"\n  🛡️ 保一保：")
        for u in cwb["bao"]:
            print(f"    {u['name']} ({u['level']}) — {u['min_score']}分 / {u['min_rank']}位次")
    
    # 强基
    qj = report["qiangji"]
    print(f"\n🔬 强基计划分析：{'✅ 推荐参加强基' if qj['recommended'] else '❌ 不建议主攻强基'}")
    print(f"   原因：{qj['reason']}")
    if qj.get("tip_2026"):
        for t in qj["tip_2026"]:
            print(f"   💡 {t}")
    
    # 综评
    zp = report["zongping"]
    print(f"\n📝 综合评价分析：✅ 强烈推荐")
    print(f"   原因：{zp['reason']}")
    
    # 专业推荐
    print(f"\n💼 专业推荐（按优先级排序）：")
    for m in report["majors"]:
        print(f"  {m['priority']} {m['major']}")
        print(f"    理由：{m['reason']}")
        if m.get("note"):
            print(f"    提示：{m['note']}")
    
    # 时间线
    print(f"\n📅 专属时间线：")
    for t in report["timeline"]:
        print(f"\n  ⏰ {t['period']}:")
        for task in t["tasks"]:
            print(f"    ✔ {task}")
    
    print(f"\n{'='*60}")
    print(f"💡 数据来源：2025广东录取数据 + 2026强基/综评政策 + 雪峰人方法论")
    print(f"⚠️ 预估分数为参考值，实际以高考为准")


def interactive_mode():
    """交互式模式"""
    print("\n🧠 高考升学规划智能体 - 推荐引擎")
    print("=" * 50)
    print("1. 查看燃爆的方案")
    print("2. 查看挺饱的方案")
    print("3. 自定义用户方案")
    print("0. 退出")
    print("=" * 50)
    
    choice = input("\n请选择 (0-3): ").strip()
    
    if choice == "1":
        report = AdmissionRecommender(USER_PROFILES["燃爆"]).generate_full_report()
        print_report(report)
    elif choice == "2":
        report = AdmissionRecommender(USER_PROFILES["挺饱"]).generate_full_report()
        print_report(report)
    elif choice == "3":
        name = input("姓名: ")
        school = input("学校: ")
        score = int(input("预估高考分数: "))
        subject = input("物理类/历史类: ")
        majors = input("目标专业（逗号分隔）: ").split(",")
        
        profile = {
            "name": name, "school": school, "subject_type": subject,
            "elective": [], "grade_rank": "自定义", "estimated_province_rank": 0,
            "estimated_score": score, "target_majors_priority": majors,
            "region_preference": [], "strength_subjects": [], "notes": ""
        }
        report = AdmissionRecommender(profile).generate_full_report()
        print_report(report)
    elif choice == "0":
        print("再见!")
    else:
        print("无效选择")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--user":
        name = sys.argv[2]
        if name in USER_PROFILES:
            report = AdmissionRecommender(USER_PROFILES[name]).generate_full_report()
            print_report(report)
        else:
            print(f"未找到用户: {name}，可用用户: {list(USER_PROFILES.keys())}")
    else:
        interactive_mode()
