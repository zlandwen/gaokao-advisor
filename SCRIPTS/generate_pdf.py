#!/usr/bin/env python3
"""生成PDF报告 + 高校推荐数据"""
import json, os, datetime
from fpdf import FPDF

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.db")

def md_to_pdf(md_path, pdf_path, title):
    """Convert markdown-style text to PDF"""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('CJK', '', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', uni=True)
    pdf.add_font('CJK', 'B', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', uni=True)
    pdf.set_font('CJK', 'B', 16)
    pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    pdf.set_font('CJK', '', 10)
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        if line.startswith('# '):
            pdf.set_font('CJK', 'B', 14)
            pdf.cell(0, 10, line[2:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('CJK', '', 10)
        elif line.startswith('## '):
            pdf.set_font('CJK', 'B', 12)
            pdf.cell(0, 8, line[3:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('CJK', '', 10)
        elif line.startswith('### '):
            pdf.set_font('CJK', 'B', 11)
            pdf.cell(0, 7, line[4:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('CJK', '', 10)
        elif line.startswith('|') and '---' not in line:
            # Table row
            cells = [c.strip() for c in line.split('|') if c.strip()]
            row = ' | '.join(cells)
            pdf.cell(0, 6, row[:120], new_x="LMARGIN", new_y="NEXT")
        elif line.startswith('- ') or line.startswith('* '):
            pdf.cell(0, 6, '  ' + line[:118], new_x="LMARGIN", new_y="NEXT")
        elif len(line) > 120:
            pdf.cell(0, 6, line[:118], new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.cell(0, 6, line[:118], new_x="LMARGIN", new_y="NEXT")
    
    pdf.output(pdf_path)
    return os.path.getsize(pdf_path)

def generate_uni_recommendations():
    """Generate university comparison data"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        
        # 燃爆的目标院校对比
        ranbao = conn.execute("""
            SELECT rank_soft, name, level, 
                   (SELECT min_score FROM admission_scores 
                    WHERE university_id=u.id AND province='广东' AND subject_type='物理类' AND year=2025) as score,
                   (SELECT min_rank FROM admission_scores 
                    WHERE university_id=u.id AND province='广东' AND subject_type='物理类' AND year=2025) as rank
            FROM universities u
            WHERE name IN ('清华大学','北京大学','复旦大学','上海交通大学','浙江大学','中国科学技术大学','南京大学','中山大学')
            ORDER BY rank_soft
        """).fetchall()
        
        # 挺饱的目标院校对比
        tingbao = conn.execute("""
            SELECT name, level,
                   (SELECT min_score FROM admission_scores 
                    WHERE university_id=u.id AND province='广东' AND subject_type='物理类' AND year=2025) as score
            FROM universities u
            WHERE name IN ('南方科技大学','华南理工大学','深圳大学','暨南大学','华南师范大学','广东工业大学')
            ORDER BY score DESC
        """).fetchall()
        
        conn.close()
        
        result = {
            "ranbao": [{"name": r[1], "level": r[2], "score": r[3], "rank": r[4]} for r in ranbao if r[3]],
            "tingbao": [{"name": r[0], "level": r[1], "score": r[2]} for r in tingbao if r[2]]
        }
        return result
    except:
        return {"ranbao": [], "tingbao": []}

def build_core_advice():
    """构建核心建议摘要"""
    return {
        "ranbao": """
🔥 燃爆核心建议（2026年7月更新）：
━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 定位：C9冲顶选手（省排800-1500，665-680分）
📍 家庭：A8-A9（金融/商科/出国路径打开）

🎯 暑假优先级：
1️⃣ 语文突破（#380→目标前200，提10分=总排名前进几百名）
2️⃣ 强基入门（物理#12+数学#15，刷清北真题）
3️⃣ 英语135+（目前125，#89→前50）

🏫 目标矩阵：
冲顶：清华/北大/复旦（强基主通道）
主攻：上交/浙大/中科大/南大（强基+高考）
保底：中大/南科大（综评）

💼 专业方向：计算机/AI/集成电路（主）+商科/金融（A8备选）
📅 高二上目标：数学135+、物理95+、英语135+、语文115+""",
        "tingbao": """
🍜 挺饱核心建议（2026年7月更新）：
━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 定位：综评冲985+高考稳211（省排8000-15000，590-625分）
📍 家庭：A8-A9（出国/创业路径打开）

🎯 暑假优先级：
1️⃣ 英语突破（110→130+，港中深综评需要雅思6.0水平）
2️⃣ 物理补基础（#113不是差是卷子难，高二电学跟上）
3️⃣ 地理保持优势（#29→目标前15，赋分95+）

🏫 目标矩阵：
综评冲刺：南科大（机考数理）/港中深（英语机考）/中大
高考主攻：华工/深大/暨大/华南师大
保底：广工/广大

💼 专业方向：计算机/电子/师范（公费师范生优先）/地理信息
📅 高二上目标：英语#124→#90、数学#133→#100、地理#29→#20"""
    }

def generate_user_report(profile, output_path):
    """从用户profile生成PDF报告（用于微信/网页下载）"""
    from fpdf import FPDF
    
    pdf = FPDF()
    pdf.add_page()
    
    # 中文字体
    font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
    pdf.add_font('CJK', '', font_path, uni=True)
    pdf.add_font('CJK', 'B', font_path, uni=True)
    
    name = profile.get("name", "同学")
    school = profile.get("school", "")
    score = profile.get("estimated_score", 0)
    
    # 标题
    pdf.set_font('CJK', 'B', 18)
    pdf.cell(0, 14, f"📋 {name} 升学分析报告", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CJK', '', 8)
    pdf.cell(0, 6, f"生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # 基本信息
    pdf.set_font('CJK', 'B', 12)
    pdf.cell(0, 8, "📌 基本信息", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CJK', '', 10)
    pdf.cell(0, 7, f"  姓名：{name}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  学校：{school}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  预估分数：{profile.get('estimated_score_min',0)}-{profile.get('estimated_score_max',0)}分", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"  省排名：{profile.get('estimated_province_rank_min',0)}-{profile.get('estimated_province_rank_max',0)}", new_x="LMARGIN", new_y="NEXT")
    if profile.get("family_background"):
        pdf.cell(0, 7, f"  家庭背景：{profile['family_background'][:50]}", new_x="LMARGIN", new_y="NEXT")
    if profile.get("interests"):
        pdf.cell(0, 7, f"  兴趣方向：{profile['interests'][:50]}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # 成绩表
    scores = profile.get("exam_scores", {})
    if scores:
        pdf.set_font('CJK', 'B', 12)
        pdf.cell(0, 8, "📊 各科成绩", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('CJK', '', 10)
        for subj, s in scores.items():
            if s and s > 0:
                pdf.cell(0, 6, f"  {subj}：{s}分", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
    
    # 推荐专业
    try:
        from recommend import AdmissionRecommender
        report = AdmissionRecommender(profile).generate_full_report()
        majors = report.get("majors", [])
        if majors:
            pdf.set_font('CJK', 'B', 12)
            pdf.cell(0, 8, "🎯 推荐专业与院校", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font('CJK', '', 10)
            for m in majors[:6]:
                if m.get("suitable"):
                    schools = m.get("schools", [])
                    snames = [s.get("school","")[:12] for s in schools[:2]]
                    pdf.cell(0, 7, f"  {m['priority']} {m['major']}: {'、'.join(snames)}", new_x="LMARGIN", new_y="NEXT")
        
        # 冲稳保
        cwb = report.get("chong_wen_bao", {})
        for level_key, level_label in [("chong","🚀 冲刺"), ("wen","✅ 稳妥"), ("bao","🛡️ 保底")]:
            schools = cwb.get(level_key, [])
            if schools:
                names = [s.get("school","?")[:10] for s in schools[:3]]
                pdf.cell(0, 7, f"  {level_label}：{'、'.join(names)}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
    except:
        pass
    
    # 未来趋势
    pdf.set_font('CJK', 'B', 12)
    pdf.cell(0, 8, "🔭 未来10年行业前瞻", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('CJK', '', 9)
    trends = [
        "人工智能全产业链(国产AI芯片+大模型+人形机器人)",
        "新能源与储能(光伏/风电/固态电池/氢能)",
        "半导体与先进制造(国产替代10年主线)",
        "生物医药(老龄化+基因技术)",
        "低空经济(无人机+eVTOL飞行器)"
    ]
    for t in trends:
        pdf.cell(0, 6, f"  • {t}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    pdf.set_font('CJK', '', 8)
    pdf.cell(0, 6, "— 雪峰人AI升学顾问 v2.0 —", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "数据来源：软科2026排名 / QS2026 / 广东省教育考试院", new_x="LMARGIN", new_y="NEXT")
    
    pdf.output(output_path)
    return os.path.getsize(output_path)

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. 生成PDF
    print("生成PDF...")
    pairs = [
        (os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "燃爆_详细作战方案.md"), "燃爆_详细作战方案.pdf", "🔥 燃爆专属作战方案"),
        (os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "挺饱_详细作战方案.md"), "挺饱_详细作战方案.pdf", "🍜 挺饱专属作战方案"),
    ]
    for md, pdf, title in pairs:
        size = md_to_pdf(md, os.path.join(OUTPUT_DIR, pdf), title)
        print(f"  ✅ {pdf} ({size//1024}KB)")
    
    # 2. 生成高校推荐数据
    print("生成高校推荐数据...")
    unis = generate_uni_recommendations()
    with open(os.path.join(OUTPUT_DIR, "uni_recommendations.json"), 'w') as f:
        json.dump(unis, f, ensure_ascii=False)
    print(f"  ✅ 燃爆{len(unis['ranbao'])}所 + 挺饱{len(unis['tingbao'])}所")
    
    # 3. 生成核心建议JSON
    advice = build_core_advice()
    with open(os.path.join(OUTPUT_DIR, "core_advice.json"), 'w') as f:
        json.dump(advice, f, ensure_ascii=False)
    print("  ✅ 核心建议已生成")
    
    print("全部完成")
