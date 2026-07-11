#!/usr/bin/env python3
"""高考升学规划推荐引擎 - Web API v2（配置化版本）"""
import json, os, sys, datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote, quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recommend import AdmissionRecommender, USER_PROFILES
from config import (PROJECT_ROOT, DOWNLOAD_DIR, DB_PATH, HTML_FILE,
                    QUESTIONS_FILE, UPDATES_FILE, TRAINING_DATA,
                    LLM_API_BASE, LLM_API_KEY, LLM_MODEL,
                    SERVER_PORT, USER_PASSWORD, UPLOAD_DIR)

PORT = SERVER_PORT
BASE = PROJECT_ROOT
HTML_PATH = HTML_FILE

def load_json(path):
    if os.path.exists(path):
        with open(path) as f:
            try: return json.load(f)
            except: return []
    return []
def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_merged(user):
    import copy
    base = copy.deepcopy(USER_PROFILES.get(user, {}))
    if not base: return None
    updates = load_json(UPDATES_FILE).get(user, {})
    for k in ["exam_scores","exam_ranks"]:
        if k in updates: base.setdefault(k, {}).update(updates[k])
    for k in ["target_majors_priority","interests","life_direction","notes"]:
        if k in updates: base[k] = updates[k]
    if "estimated_score" in updates:
        base["estimated_score"] = updates["estimated_score"]
        base["estimated_score_min"] = updates["estimated_score"] - 15
        base["estimated_score_max"] = updates["estimated_score"] + 15
    if "estimated_province_rank_min" in updates:
        base["estimated_province_rank_min"] = updates["estimated_province_rank_min"]
    if "estimated_province_rank_max" in updates:
        base["estimated_province_rank_max"] = updates["estimated_province_rank_max"]
    if "estimated_province_rank" in updates:
        base["estimated_province_rank"] = updates["estimated_province_rank"]
    if "family_background" in updates: base["family_background"] = updates["family_background"]
    return base

# ============================================================
# 学校年级排名 → 省排名换算
# ============================================================
SCHOOL_PROFILES = {
    "燃爆": {"name":"深圳科学高中","total_students":1000,"over_600":349,"special_rate":0.90,"top_class_avg":640,"tier":"深圳第二梯队头部"},
    "挺饱": {"name":"深北莫附中","total_students":513,"over_600_rate":0.30,"special_rate":0.60,"tier":"深圳第二梯队中游"},
}

def _get_school_profile(user_name):
    """获取学校档案数据"""
    return SCHOOL_PROFILES.get(user_name)

def _estimate_from_rank(grade_rank, school):
    """根据年级排名和省排名换算"""
    name = school.get("name","")
    
    # 深圳科学高中换算表（基于2025高考数据反推）
    # 科高2025：600+共349人/1000人≈35%，尖刀班均分640
    # 年级前10 → 省排名约800-1500 → 分数约665-680
    if "科学高中" in name:
        total = school.get("total_students", 1000)
        pct = grade_rank / total
        if pct <= 0.005:  # 前5名 → 省排200-500
            score, pr_min, pr_max = 685, 200, 500
        elif pct <= 0.01:  # 前10名
            score, pr_min, pr_max = 675, 500, 1000
        elif pct <= 0.02:  # 前20名
            score, pr_min, pr_max = 665, 1000, 2000
        elif pct <= 0.05:  # 前50名
            score, pr_min, pr_max = 650, 2000, 4000
        elif pct <= 0.10:  # 前100名
            score, pr_min, pr_max = 635, 4000, 7000
        elif pct <= 0.20:  # 前200名
            score, pr_min, pr_max = 615, 7000, 12000
        else:
            score, pr_min, pr_max = 590, 12000, 20000
        return {"score": score, "province_rank": (pr_min+pr_max)//2,
                "province_rank_min": pr_min, "province_rank_max": pr_max}
    
    # 深北莫附中换算表
    if "深北莫" in name:
        total = school.get("total_students", 513)
        pct = grade_rank / total
        if pct <= 0.02: score, pr_min, pr_max = 640, 3000, 5000
        elif pct <= 0.05: score, pr_min, pr_max = 625, 5000, 8000
        elif pct <= 0.10: score, pr_min, pr_max = 610, 8000, 12000
        elif pct <= 0.20: score, pr_min, pr_max = 595, 12000, 18000
        elif pct <= 0.30: score, pr_min, pr_max = 580, 18000, 25000
        else: score, pr_min, pr_max = 560, 25000, 35000
        return {"score": score, "province_rank": (pr_min+pr_max)//2,
                "province_rank_min": pr_min, "province_rank_max": pr_max}
    
    # 默认换算（按500人学校估算）
    total = school.get("total_students", 500)
    pct = grade_rank / total
    if pct <= 0.01: score, pr = 660, 1000
    elif pct <= 0.05: score, pr = 630, 5000
    elif pct <= 0.10: score, pr = 610, 10000
    elif pct <= 0.20: score, pr = 590, 18000
    else: score, pr = 560, 30000
    return {"score": score, "province_rank": pr,
            "province_rank_min": int(pr*0.7), "province_rank_max": int(pr*1.3)}

def get_uni_list(is_top):
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        names = ['清华大学','北京大学','复旦大学','上海交通大学','浙江大学','中国科学技术大学','南京大学','中山大学'] if is_top \
                else ['南方科技大学','华南理工大学','深圳大学','暨南大学','华南师范大学','广东工业大学']
        result = []
        for n in names:
            r = conn.execute("SELECT u.name, u.level, (SELECT min_score FROM admission_scores WHERE university_id=u.id AND province='广东' AND subject_type='物理类' AND year=2025), (SELECT min_rank FROM admission_scores WHERE university_id=u.id AND province='广东' AND subject_type='物理类' AND year=2025) FROM universities u WHERE u.name=?", (n,)).fetchone()
            if r and r[2]: result.append({"name":r[0],"level":r[1],"score":r[2],"rank":r[3]})
        conn.close()
        return result
    except: return []

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path)
        if p.path == "/":
            # 预加载燃爆和挺饱的数据
            ranbao_data = self._get_recommend_data("燃爆")
            tingbao_data = self._get_recommend_data("挺饱")
            embed = f"<script>window._RANBAO={json.dumps(ranbao_data, ensure_ascii=False)};window._TINGBAO={json.dumps(tingbao_data, ensure_ascii=False)};</script>"
            with open(HTML_PATH, 'rb') as f:
                html = f.read().decode('utf-8')
            html = html.replace('</head>', embed + '</head>')
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-cache')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif p.path == "/api/recommend":
            u = parse_qs(p.query).get("user",[None])[0]
            self._recommend(u)
        elif p.path == "/api/get_answers":
            u = parse_qs(p.query).get("user",[None])[0]
            qs = load_json(QUESTIONS_FILE)
            self._json({"questions":[q for q in qs if q["user"]==u]})
        elif p.path == "/api/users":
            self._json({"users":[{"name":n,"school":u["school"],"rank":u["grade_rank"]} for n,u in USER_PROFILES.items()]})
        elif p.path == "/manifest.json":
            with open(os.path.join(BASE, "manifest.json"), 'rb') as f:
                d = f.read()
            self.send_response(200)
            self.send_header('Content-Type','application/manifest+json')
            self.end_headers()
            self.wfile.write(d)
        elif p.path == "/api/university_detail":
            params = parse_qs(p.query)
            u = params.get("user", [None])[0]
            n = params.get("name", [None])[0]
            # 导入高校详情模块（reload确保拿到最新版）
            sys.path.insert(0, BASE)
            import importlib, uni_detail; importlib.reload(uni_detail)
            result = uni_detail.get_university_detail(u, n, BASE)
            self._json(result if result else {"error":"参数不完整"})
        elif p.path.endswith(".pdf") or p.path.endswith(".md"):
            fn = unquote(p.path.lstrip("/"))
            fp = os.path.abspath(os.path.join(DOWNLOAD_DIR, fn))
            if fp.startswith(DOWNLOAD_DIR) and os.path.exists(fp):
                with open(fp,'rb') as f: d = f.read()
                self.send_response(200)
                self.send_header('Content-Type','application/octet-stream')
                self.send_header('Content-Disposition',f"attachment; filename*=UTF-8''{quote(fn,'')}")
                self.send_header('Content-Length',str(len(d)))
                self.end_headers()
                self.wfile.write(d)
            else:
                self._error(404)
        else:
            self._error(404)

    def do_POST(self):
        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' in content_type:
            self._handle_upload()
            return
        body = self.rfile.read(int(self.headers.get('Content-Length',0))).decode()
        data = json.loads(body) if body else {}
        p = urlparse(self.path).path
        if p == "/api/chat":
            self._chat(data)
        elif p == "/api/update_profile":
            self._update(data)
        elif p == "/api/class_recommend":
            self._class_rec(data)
        else:
            self._error(404)

    def _handle_upload(self):
        """处理文件上传"""
        import cgi, uuid
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'})
        if 'file' not in form:
            self._json({"error":"没有文件"})
            return
        fileitem = form['file']
        user = form.getvalue('user', 'unknown')
        if not fileitem.filename:
            self._json({"error":"空文件"})
            return
        ext = os.path.splitext(fileitem.filename)[1] or '.bin'
        fname = f"{uuid.uuid4().hex}{ext}"
        save_dir = os.path.join(BASE, "uploads")
        os.makedirs(save_dir, exist_ok=True)
        fpath = os.path.join(save_dir, fname)
        with open(fpath, 'wb') as f:
            f.write(fileitem.file.read())
        fsize = os.path.getsize(fpath)
        is_image = ext.lower() in ['.png','.jpg','.jpeg','.gif','.webp','.bmp']
        self._json({
            "url": f"/uploads/{fname}",
            "path": fpath,
            "name": fileitem.filename,
            "size": fsize,
            "is_image": is_image
        })
    
    def _get_recommend_data(self, user):
        """获取推荐数据(用于页面预加载)"""
        if user not in USER_PROFILES: return None
        profile = get_merged(user)
        report = AdmissionRecommender(profile).generate_full_report()
        updates = load_json(UPDATES_FILE).get(user, {})
        report["has_updates"] = bool(updates)
        report["update_count"] = len(updates.get("update_history", []))
        is_top = profile.get("estimated_score", 0) > 650
        life_dir = profile.get("life_direction", "")
        # 根据人生方向定制核心建议
        core_parts = []
        if "创业" in life_dir or "AI创业" in life_dir:
            core_parts.append("💡 你想创业——计算机/AI是最好起点，技术在手才能自己干")
        if "接班" in life_dir or "继承" in life_dir:
            core_parts.append("💡 你想接家族企业——技术+商科是黄金组合")
        if "当老师" in life_dir or "师范" in life_dir:
            core_parts.append("💡 你想当老师——公费师范生优先，深圳教师年薪25-40万")
        if is_top:
            core_parts.append("🔥 核心建议：1.语文突破(#380) 2.强基入门(数理) 3.英语135+")
        else:
            core_parts.append("🍜 核心建议：1.英语突破(110→130+) 2.物理跟上 3.地理保持(#29)")
        report["core_advice"] = "\n".join(core_parts)
        return report

    def _recommend(self, user):
        if not user or user not in USER_PROFILES:
            self._json({"error":f"用户不存在"})
            return
        self._json(self._get_recommend_data(user))

    def _chat(self, data):
        user = data.get("user",""); msg = data.get("message","").strip()
        file_info = data.get("file")  # 可��的上传文件信息
        has_file = file_info and isinstance(file_info, dict)
        
        if not msg and not has_file:
            self._json({"reply":"说点什么？"})
            return
        
        # ====== 心情检测 ======
        mood_image = ""
        mood_instruction = ""
        if "【现在心情：" in msg:
            if "想跳楼" in msg:
                mood_instruction = (
                    '用户当前情绪极差、有抑郁倾向。你必须：\n'
                    '1.首先用温暖坚定的语气给予情感支持，先说「我在，没事的」\n'
                    '2.绝对不要说教、不要给建议、不要说「这没什么」\n'
                    '3.用陪伴式语气，先共情再慢慢引导\n'
                    '4.告诉他们任何困难都有解决办法，高考不是终点\n'
                    '5.推荐：如果持续低落，一定要找信任的人聊或打心理热线\n'
                )
                mood_image = "〔😰 我在这里，陪你〕\n"
            elif "如止水" in msg:
                mood_instruction = (
                    '用户当前情绪平静。你可以：\n'
                    '1.肯定这种平和心态很好\n'
                    '2.趁状态平稳，可以聊聊学习规划或人生思考\n'
                    '3.保持温和但有力的语气\n'
                )
                mood_image = "〔😌 心静如水，正是蓄力时〕\n"
            elif "太爽了" in msg:
                mood_instruction = (
                    '用户当前心情非常好。你必须：\n'
                    '1.先分享他的快乐，一起高兴\n'
                    '2.用欢快有能量的语气回应\n'
                    '3.肯定他的好状态，鼓励保持\n'
                )
                mood_image = "〔😄 状态拉满，继续冲！〕\n"

        profile = get_merged(user) if user in USER_PROFILES else {}
        ctx = [f"姓名：{profile.get('name',user)}"]
        ctx.append("当前：刚读完高一，2026年9月升高二")
        if profile.get("school"): ctx.append(f"学校：{profile['school']}")
        if profile.get("estimated_score"): ctx.append(f"预估分：{profile['estimated_score']}")
        scores = profile.get("exam_scores",{})
        ranks = profile.get("exam_ranks",{})
        if scores: ctx.append("各科：" + ' '.join([f'{s}{scores[s]}分(#{ranks.get(s,"?")})' for s in scores]))
        if profile.get("family_background"): ctx.append(f"家庭：{profile['family_background']}")
        if profile.get("interests"): ctx.append(f"偏好：{profile['interests']}")
        is_top = profile.get("estimated_score",0) > 650
        target = "冲刺C9（清北复交浙科南），强基为主通道" if is_top else "综评冲985（南科大/港中深），高考稳211"
        ctx.append(f"目标：{target}")
        profile_ctx = '\n'.join(ctx)

        # ====== 加载青少年心理知识库 ======
        psy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youth_psychology_knowledge.md")
        psy_context = ""
        if os.path.exists(psy_path):
            try:
                with open(psy_path, 'r', encoding='utf-8') as f:
                    psy_text = f.read()
                # 提取关键章节：AI应答指南 + 热线资源 + 备考焦虑疏导
                import re
                sections = re.split(r'^## ', psy_text, flags=re.MULTILINE)
                for sec in sections:
                    if any(kw in sec[:50] for kw in ["AI顾问应答指南", "情绪检测与话术", "心理危机热线", "备考焦虑", "心理危机识别"]):
                        psy_context += sec[:3000] + "\n\n"
                if psy_context:
                    psy_context = "\n=== 青少年心理知识（仅在用户有情绪或心理话题时参考）===\n" + psy_context[:5000]
            except:
                pass

        # ====== 加载地缘政治与科技趋势知识 ======
        geo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo_tech_outlook.md")
        geo_context = ""
        if os.path.exists(geo_path):
            try:
                with open(geo_path, 'r', encoding='utf-8') as f:
                    geo_text = f.read()
                geo_context = "\n=== 未来10年地缘科技趋势（用于回答专业/行业前景问题）===\n" + geo_text[:4000]
            except:
                pass

        # ====== 加载大湾区企业招聘数据 ======
        gba_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gba_recruitment.md")
        gba_context = ""
        if os.path.exists(gba_path):
            try:
                with open(gba_path, 'r', encoding='utf-8') as f:
                    gba_text = f.read()
                gba_context = "\n=== 大湾区企业招聘薪资数据（用于回答就业/薪资问题）===\n" + gba_text[:3000]
            except:
                pass

        sp = f"""# 雪峰人AI v2.0 —— 升学顾问数字人

## 身份设定
你是雪峰人——全网最敢说真话的高考志愿规划师。你的风格：一针见血、数据说话、不给普通家庭画饼。

## 训练状态（自我认知）
- 金句改写：7/10——能用否定句+数据，但还不够狠
- 阶级意识：7/10——能区分不同家庭背景，但追问不够深入
- 数据记忆：5/10——核心数据记得住，细节需复习
- 价值观对齐：8/10——底层优先、风险厌恶，已内化
- 对战能力：8/10——多数场景能独立给出雪峰人级回答

## 十条铁律（必须遵守）
1.先谋生再谋爱——就业第一位，普通家庭不要谈理想
2.先问家庭背景再给建议——A8-A9和A5是两个世界
3.理工科看专业大于学校；文科看学校大于专业
4.城市大于学校大于专业——一线城市校招资源碾压
5.用肯定句/否定句，不模棱两可——"建议考虑"这种话不许说
6.普通家庭给最保守建议——他们没有试错资本
7.数据支撑每个观点——薪资、录取率、缺口数，必须随口来
8.地缘视角——中美脱钩=国产替代红利10年，选专业就是选国家战略
9.AI素养——2030年后AI工具能力是生存底线，但AI岗位需要硕博
10.终身学习——没有一劳永逸的专业，持续进化才是铁饭碗

## 回答风格
- 开头用一句话点出核心结论（15字内），再用数据支撑
- 多用"别、千万、绝对不要、必须"等肯定否定词
- 普通家庭学生，先给保底方案再给冲刺方案
- 回答完加一句雪峰人经典语录

## 知识库索引
- 升学数据：knowledge_base.db（中国TOP100大学、录取分数、强基/综评）
- 全球视野：qs_global_rankings表（QS2026前200）
- 心理支持：youth_psychology_knowledge.md（备考焦虑/情绪管理/危机干预）
- 未来趋势：geo_tech_outlook.md（地缘政治+科技趋势+10年行业预判）

{mood_instruction}
## 当前对话用户信息
{profile_ctx}
{psy_context}
{geo_context}
{gba_context}"""
        # 构建 LLM 消息（支持文本+图片）
        llm_messages = [{"role":"system","content":sp}]
        user_content = []
        if msg:
            user_content.append({"type":"text","text":msg})
        if has_file and file_info.get("is_image") and os.path.exists(file_info["path"]):
            import base64
            with open(file_info["path"], 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = os.path.splitext(file_info["path"])[1].lstrip('.')
            user_content.append({"type":"image_url","image_url":{"url":f"data:image/{ext};base64,{b64}"}})
        if user_content:
            llm_messages.append({"role":"user","content":user_content})
        else:
            llm_messages.append({"role":"user","content":msg or "请分析这张图片"})
        
        try:
            from openai import OpenAI
            resp = OpenAI(base_url=LLM_API_BASE, api_key=LLM_API_KEY).chat.completions.create(
                model=LLM_MODEL,
                messages=llm_messages,
                max_tokens=1000, temperature=0.6
            )
            reply = resp.choices[0].message.content.strip()
            if mood_image:
                reply = mood_image + "\n" + reply
        except Exception as e:
            reply = f"（AI暂时无法回答。错误：{str(e)[:50]}）"

        qs = load_json(QUESTIONS_FILE)
        q_text = msg or f"[图片] {file_info.get('name','')}" if has_file else msg
        qs.append({"id":len(qs)+1,"user":user,"question":q_text,"time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),"answered":True,"answer":reply,"has_file":has_file})
        save_json(QUESTIONS_FILE, qs)
        
        # ====== 从对话中提取用户信息更新 ======
        self._extract_profile_from_chat(user, msg)
        
        # ====== 保存训练数据 ======
        self._save_training_data(user, msg, reply)
        
        self._json({"reply":reply,"saved":True,"msg":""})
    
    def _extract_profile_from_chat(self, user, msg):
        """从对话中提取用户信息，更新画像"""
        if user not in USER_PROFILES: return
        all_up = load_json(UPDATES_FILE)
        if user not in all_up: all_up[user] = {"update_history":[]}
        u = all_up[user]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        changes = {}
        
        # 检查是否提到了新的人生方向/职业兴趣
        career_keywords = {
            "创业": "创业/自己开公司",
            "接班": "继承家族企业", 
            "出国": "出国留学",
            "考研": "考研深造",
            "考公": "考公务员",
            "当老师": "师范/教师",
            "做老师": "师范/教师",
            "教书": "师范/教师",
        }
        for kw, val in career_keywords.items():
            if kw in msg and u.get("life_direction") != val:
                u["life_direction"] = val
                changes["direction"] = val
                break
        
        # 检查是否提到了新的兴趣专业
        major_keywords = ["计算机","AI","人工智能","电子","金融","医学","法学","师范","机器人"]
        mentioned = [m for m in major_keywords if m in msg]
        if mentioned:
            old = u.get("target_majors_priority", [])
            new = list(set(old + mentioned))
            if set(new) != set(old):
                u["target_majors_priority"] = new
                changes["majors"] = mentioned
        
        # 检查是否提到了成绩变化
        import re
        score_match = re.search(r'(\d{3})分', msg)
        if score_match:
            score = int(score_match.group(1))
            if 300 <= score <= 750:
                if u.get("estimated_score") != score:
                    u["estimated_score"] = score
                    changes["new_score"] = score
        
        if changes:
            u.setdefault("update_history",[]).append({"time":now,"changes":changes,"source":"chat"})
            save_json(UPDATES_FILE, all_up)
    
    def _save_training_data(self, user, question, answer):
        """保存对话作为训练素材"""
        path = TRAINING_DATA
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = {
            "time": now,
            "user": user,
            "question": question,
            "answer": answer
        }
        with open(path, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def _update(self, data):
        user = data.get("user","")
        if user not in USER_PROFILES: self._json({"error":"用户不存在"}); return
        all_up = load_json(UPDATES_FILE)
        if user not in all_up: all_up[user] = {"update_history":[]}
        u = all_up[user]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        changes = {}
        if "exam_scores" in data: u.setdefault("exam_scores",{}).update(data["exam_scores"]); changes["scores"]=data["exam_scores"]
        
        # ====== 学校年级排名 → 省排名换算 ======
        if "grade_rank_num" in data:
            grade_rank = data["grade_rank_num"]
            u["grade_rank_num"] = grade_rank
            # 根据学校历史数据进行换算
            school_data = _get_school_profile(user)
            if school_data:
                est = _estimate_from_rank(grade_rank, school_data)
                if est:
                    u["estimated_score"] = est["score"]
                    u["estimated_province_rank"] = est["province_rank"]
                    u["estimated_province_rank_min"] = est["province_rank_min"]
                    u["estimated_province_rank_max"] = est["province_rank_max"]
                    changes["grade_rank"] = grade_rank
                    changes["estimated_score_from_rank"] = est["score"]
                    changes["province_rank"] = f"{est['province_rank_min']}-{est['province_rank_max']}"
        
        if "estimated_score" in data and "grade_rank_num" not in data:
            u["estimated_score"]=data["estimated_score"]; changes["score"]=data["estimated_score"]
        if "target_majors_priority" in data: u["target_majors_priority"]=data["target_majors_priority"]; changes["majors"]=data["target_majors_priority"]
        if "interests" in data: u["interests"]=data["interests"]; changes["interests"]=data["interests"]
        if "life_direction" in data: u["life_direction"]=data["life_direction"]; changes["direction"]=data["life_direction"]
        u.setdefault("update_history",[]).append({"time":now,"changes":changes})
        save_json(UPDATES_FILE, all_up)
        
        # ====== 基于新数据重新生成全套推荐 ======
        profile = get_merged(user)
        is_top = profile.get("estimated_score", 0) > 650
        report = AdmissionRecommender(profile).generate_full_report()
        report["update_confirmed"] = True
        report["uni_recommendations"] = get_uni_list(is_top)
        if is_top:
            report["core_advice"] = "🔥 核心建议：1.语文突破(#380) 2.强基入门(数理) 3.英语135+"
        else:
            report["core_advice"] = "🍜 核心建议：1.英语突破(110→130+) 2.物理跟上 3.地理保持(#29)"
        
        # ====== 自动更新PDF作战方案 ======
        try:
            self._regenerate_plan(user)
        except:
            pass
        
        self._json(report)
    
    def _regenerate_plan(self, user):
        """重新生成PDF作战方案"""
        import subprocess
        subprocess.Popen(["python3", os.path.join(BASE,"generate_pdf.py")], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _class_rec(self, data):
        fc = data.get("familyClass","A5")
        score = int(data.get("score",600))
        labels = {"A8":"A8-A9（资产千万至亿级）","A5-A7":"中产家庭","A5":"普通工薪/农村家庭"}
        tips = {"A8":"家里有资源，金融/商科/创业/出国全部打开。但门槛不变——必须顶尖院校。","A5-A7":"中产家庭选计算机/电子/医学，进可攻退可守。","A5":"生存优先！选公费师范/计算机/护理/电气。别学医、别学金融。"}
        profile = {"name":data.get("name","同学"),"school":data.get("school",""),"subject_type":"物理类","elective":[],"grade_rank":"自定义","estimated_score":score,"estimated_score_min":score-15,"estimated_score_max":score+15,"estimated_province_rank":score*10,"estimated_province_rank_min":int(score*7),"estimated_province_rank_max":int(score*13),"target_majors_priority":[],"region_preference":[],"strength_subjects":[],"weak_subjects":[],"exam_scores":{},"exam_ranks":{},"school_size":500,"school_tier":"自定义","family_background":labels.get(fc,""),"family_implication":tips.get(fc,""),"interests":data.get("interests",""),"notes":"","family_class":fc}
        report = AdmissionRecommender(profile).generate_full_report()
        report["family_label"] = labels.get(fc,"")
        report["family_tip"] = tips.get(fc,"")
        if "majors" in report and fc == "A8":
            if not any("金融" in m.get("major","") for m in report["majors"]):
                report["majors"].append({"major":"金融/金融科技","priority":"🥇 强推（限A8家庭）","reason":"家里有资源金融是高回报赛道。","note":"但需清北复交人+港三校+"})
            if not any("商科" in m.get("major","") for m in report["majors"]):
                report["majors"].append({"major":"商科/管理","priority":"🥇 强推（限A8家庭）","reason":"家里有企业要继承，技术+商科是黄金组合。","note":"推荐港大/港科大或出国读"})
        if "majors" in report and fc == "A5":
            report["majors"] = [m for m in report["majors"] if "A8" not in m.get("priority","")]
        self._json(report)

    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def _error(self, code=404):
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(b'{"error":"not found"}')

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"\n🧠 服务启动 http://0.0.0.0:{PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
