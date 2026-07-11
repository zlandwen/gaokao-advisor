#!/usr/bin/env python3
"""高校详情v2：入学路径 + 真题资源 + 学期学习计划"""
import json, os, datetime, sqlite3

# ====== 强基真题资源库（互联网真实链接）====== 
QIANGJI_RESOURCES = {
    "清华大学": {
        "真题": [
            {"name":"📄 2025清华强基数学试题+答案详解（PDF可打印）","url":"https://www.docin.com/p-4937429530.html","type":"数学"},
            {"name":"📄 2025清华强基数学试卷（含答案）","url":"https://wenku.baidu.com/view/8d1e7c82deccda38376baf1ffc4ffe473268fd71.html","type":"数学"},
            {"name":"📄 2026清华强基笔试回忆版（数物化）","url":"https://www.gaokzx.com/gk/shitiku/157127.html","type":"数学"},
            {"name":"📄 2026清华强基面试考情+试题","url":"https://www.gaokzx.com/gk/shitiku/157126.html","type":"面试"},
            {"name":"📦 2024-2025强基校测笔面试真题集PDF","url":"https://xsyform.shuipingce.com/?xyppid=615974715315456210","type":"合集"}
        ]
    },
    "北京大学": {
        "真题": [
            {"name":"📄 2025北大强基数学试题+答案","url":"https://wenku.baidu.com/view/81661808f511f18583d049649b6648d7c0c7084f.html","type":"数学"},
            {"name":"📄 2026北大强基数学试题（回忆版）","url":"https://www.gaokzx.com/gk/shitiku/157096.html","type":"数学"},
            {"name":"📄 2026北大强基物理试题（回忆版）","url":"https://www.gaokzx.com/gk/shitiku/157097.html","type":"物理"},
            {"name":"📄 2026北大强基面试考情+试题","url":"https://www.gaokzx.com/gk/shitiku/157125.html","type":"面试"},
            {"name":"📦 2024-2025强基校测笔面试真题集PDF","url":"https://xsyform.shuipingce.com/?xyppid=615974715315456210","type":"合集"}
        ]
    },
    "default": {
        "真题": [
            {"name":"📦 39所高校2026强基校测试题汇总","url":"https://www.gaokzx.com/gk/shitiku/156101.html","type":"合集"},
            {"name":"📦 2024-2025强基校测笔面试真题集PDF","url":"https://xsyform.shuipingce.com/?xyppid=615974715315456210","type":"合集"},
            {"name":"📄 2020-2024强基校考笔试真题（学科网）","url":"https://www.zxxk.com/docpack/3151220.html","type":"合集"},
            {"name":"📄 东南大学强基面试真题PDF","url":"https://max.book118.com/html/2025/0611/8101004076007076.shtm","type":"面试"}
        ]
    }
}

ZONGPING_RESOURCES = {
    "南方科技大学": {
        "真题": [
            {"name":"📄 南科大2026综评能力测试机试安排","url":"https://www.sohu.com/a/1029042058_121124015","type":"机考"},
            {"name":"📄 南科大2026综评招生政策解读","url":"https://www.sohu.com/a/989970276_121124020","type":"政策"},
            {"name":"📄 南科大综评报名系统","url":"https://zs.sustech.edu.cn/","type":"报名"}
        ]
    },
    "香港中文大学(深圳)": {
        "真题": [
            {"name":"📄 港中深2026综评招生简章","url":"https://zs.cuhk.edu.cn/","type":"政策"},
            {"name":"📄 雅思剑18真题（港中深对标雅思6.0）","url":"https://www.britishcouncil.cn/exam/ielts","type":"雅思"}
        ]
    },
    "default": {
        "真题": [
            {"name":"📄 广东综评院校2026报考指南","url":"https://gaokao.chsi.com.cn/","type":"政策"}
        ]
    }
}

def get_resources(uni_name, path_type="强基"):
    """获取真题资源"""
    if path_type == "强基":
        return QIANGJI_RESOURCES.get(uni_name, QIANGJI_RESOURCES["default"])["真题"]
    else:
        return ZONGPING_RESOURCES.get(uni_name, ZONGPING_RESOURCES["default"])["真题"]

def get_current_plan(user_name, uni_name, best_path_type, profile):
    """基于当前时间点和用户状态生成具体学习计划"""
    now = datetime.datetime.now()
    year, month, day = now.year, now.month, now.day
    
    # ====== 学期判断（基于2026年7月=高一结束的时间线）====== 
    if year == 2026:
        if month <= 1:
            semester = "高一下学期"  # 2026年初还是高一上
        elif month <= 7:
            semester = "高一升高二暑假" if month >= 7 else "高一下学期"
        else:
            semester = "高二上学期"  # 2026年9月起
    elif year == 2027:
        if month <= 1:
            semester = "高二上学期期末"
        elif month <= 7:
            semester = "高二下学期" if month <= 6 else "高二升高三暑假"
        else:
            semester = "高三上学期"
    else:  # 2028
        if month <= 6:
            semester = "高三下学期（高考冲刺）"
        else:
            semester = "已高考"
    
    # 细化：当前月份为7月 → 统一为暑假
    if 7 <= month <= 8:
        semester = "高一升高二暑假" if year == 2026 else ("高二升高三暑假" if year == 2027 else "暑假")
    
    is_top = user_name == "燃爆"
    score = profile.get("estimated_score", 600)
    
    if best_path_type == "强基计划":
        return {
            "current_semester": semester,
            "current_tasks": [
                f"【数学】每周3套强基数学真题限时训练（高考压轴~预赛难度）",
                f"【物理】每周2套强基物理真题，重点攻坚力学+电学",
                f"【化学】每周1套强基化学真题（高考压轴难度）" if is_top else "",
                "【面试】每月1次模拟面试，练表达练逻辑",
                f"【真题】刷目标校近3年强基笔试真题（gaokzx.com有汇总）"
            ],
            "holiday_tasks": [
                "【暑假集训】每天4小时强基专项：数学2h+物理1.5h+化学0.5h",
                "【真题突破】完成目标校近5年全部强基真题",
                "【面试准备】整理个人陈述+科研/竞赛经历",
                "【弱科攻坚】针对性地补强基笔试的薄弱模块"
            ],
            "resources": get_resources(uni_name, "强基"),
            "key_link": "https://www.gaokzx.com/gk/shitiku/156101.html"
        }
    elif best_path_type == "综合评价":
        return {
            "current_semester": semester,
            "current_tasks": [
                f"【校测准备】了解{uni_name}综评校测形式（机考/面试/英语）",
                "【机考训练】数学+物理/英语每周各1套限时模拟" if "南科大" in uni_name else "【英语训练】雅思阅读+听力每周3套（港中深对标雅思6.0）",
                "【面试准备】每周1次模拟面试，练中英文表达",
                "【材料整理】梳理获奖证书、社会实践活动、个人陈述",
                "【政策跟踪】关注目标校综评简章发布时间"
            ],
            "holiday_tasks": [
                "【暑假集训】校测专项突破：每天3小时",
                "【机考模拟】完成近3年校测真题，分析错题规律",
                "【面试打磨】找老师/家长模拟面试，录视频复盘",
                "【英语冲刺】如果目标校考英语，集中突破阅读和听力"
            ],
            "resources": get_resources(uni_name, "综评"),
            "key_link": "https://gaokao.chsi.com.cn/"
        }
    else:
        return {
            "current_semester": semester,
            "current_tasks": [
                f"【高考冲刺】稳住年级排名，保持各科均衡",
                f"【数学】基础题零失误，中档题拿满分，压轴题突破",
                f"【英语】每天1套阅读+完形，词汇持续积累",
                f"【理科】理综限时训练，提高答题速度和准确率"
            ],
            "holiday_tasks": [
                "【暑假】一轮复习：地毯式过完高一高二知识点",
                "【真题】近5年高考真题刷2遍，分析命题规律"
            ],
            "resources": [],
            "key_link": ""
        }

def get_university_detail(user_name, uni_name, base_dir):
    """获取高校详情（供web_rec_server调用）"""
    if not user_name or not uni_name:
        return None
    
    DB_PATH = os.path.join(base_dir, "knowledge_base.db")
    UPDATES_PATH = os.path.join(base_dir, "user_updates.json")
    
    import sys
    sys.path.insert(0, base_dir)
    from recommend import USER_PROFILES
    
    def get_merged(user):
        import copy
        base = copy.deepcopy(USER_PROFILES.get(user, {}))
        # 如果用户不在预设画像中（"自己来"模式），创建一个基本画像
        if not base:
            base = {"name": user, "estimated_score": 600, "estimated_province_rank": 6000}
        if os.path.exists(UPDATES_PATH):
            with open(UPDATES_PATH) as f:
                updates = json.load(f).get(user, {})
            if "exam_scores" in updates: base.setdefault("exam_scores",{}).update(updates["exam_scores"])
            if "estimated_score" in updates:
                base["estimated_score"] = updates["estimated_score"]
                base["estimated_score_min"] = updates["estimated_score"] - 15
                base["estimated_score_max"] = updates["estimated_score"] + 15
            if "estimated_province_rank_min" in updates: base["estimated_province_rank_min"] = updates["estimated_province_rank_min"]
            if "estimated_province_rank_max" in updates: base["estimated_province_rank_max"] = updates["estimated_province_rank_max"]
            if "interests" in updates: base["interests"] = updates["interests"]
            if "life_direction" in updates: base["life_direction"] = updates["life_direction"]
        return base
    
    profile = get_merged(user_name)
    if not profile: return {"error": "用户不存在"}
    score = profile.get("estimated_score", 600)
    
    # 数据库查询
    uni_info = {"name": uni_name, "level": "", "province": "", "city": ""}
    admission_score = admission_rank = None
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            row = conn.execute("SELECT level, province, city FROM universities WHERE name=?", (uni_name,)).fetchone()
            if row: uni_info = {"name": uni_name, "level": row[0], "province": row[1], "city": row[2]}
            sr = conn.execute("SELECT min_score, min_rank FROM admission_scores WHERE university_id=(SELECT id FROM universities WHERE name=?) AND province='广东' AND subject_type='物理类' AND year=2025", (uni_name,)).fetchone()
            if sr: admission_score, admission_rank = sr[0], sr[1]
            conn.close()
        except: pass
    
    # 路径判断
    qiangji_unis = ["清华大学","北京大学","复旦大学","上海交通大学","浙江大学","中国科学技术大学","南京大学",
                   "武汉大学","华中科技大学","西安交通大学","北京航空航天大学","哈尔滨工业大学","中山大学",
                   "北京理工大学","东南大学","四川大学","中国人民大学","同济大学","北京师范大学","天津大学",
                   "南开大学","山东大学","西北工业大学","中国农业大学","厦门大学","吉林大学","中南大学",
                   "大连理工大学","华东师范大学","华南理工大学","电子科技大学","重庆大学","湖南大学"]
    zongping_unis = {"南方科技大学","香港中文大学(深圳)","中山大学","华南理工大学","西交利物浦大学","北师港浸大"}
    
    paths = []
    score_gap = (admission_score - score) if admission_score else 0
    
    if uni_name in qiangji_unis:
        paths.append({
            "type": "强基计划", "match": "冲刺" if score_gap > 5 else ("稳妥" if score_gap > -10 else "保底"),
            "recommended": 0 < score_gap < 15, "line": admission_score, "gap": score_gap,
            "detail": "高考85%+校测15%。限报1所。数理强者优势。",
            "prep": "刷强基真题（数理竞赛基础），暑假开始准备校测笔试"
        })
    if uni_name in zongping_unis:
        paths.append({
            "type": "综合评价", "match": "适合", "recommended": True,
            "detail": "高考60%+校测30%+学考10%。可降10-20分。",
            "prep": "准备校测（南科大：数理机考；港中深：英语机考+面试）"
        })
    paths.append({
        "type": "高考普通批", "match": "冲刺" if score_gap > 5 else ("稳妥" if score_gap > -10 else "保底"),
        "recommended": abs(score_gap) <= 5, "line": admission_score, "gap": score_gap,
        "detail": "完全看高考分数。2025广东物理类录取线。",
        "prep": "全力冲刺高考"
    })
    
    best = None
    for p in paths:
        if p.get("recommended"): best = p; break
    if not best and paths: best = paths[-1]
    
    # 最近活动时间
    last_activity = "2026年7月"
    try:
        if os.path.exists(UPDATES_PATH):
            with open(UPDATES_PATH) as f:
                updates = json.load(f).get(user_name, {})
            history = updates.get("update_history", [])
            if history: last_activity = history[-1].get("time", last_activity)
    except: pass
    
    # 生成当前学期学习计划
    plan_data = get_current_plan(user_name, uni_name, best["type"] if best else "高考普通批", profile)
    
    return {
        "university": uni_info,
        "admission_score": admission_score,
        "admission_rank": admission_rank,
        "paths": paths,
        "best_path": best["type"] if best else "高考",
        "plan_data": plan_data,
        "last_activity": last_activity
    }
