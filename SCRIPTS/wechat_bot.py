#!/usr/bin/env python3
"""
微信机器人服务 - 雪峰人AI微信聊天中间件
=====================================
提供：
1. 微信消息接收与回复（支持itchat/企业微信/Webhook三种模式）
2. 问答式信息收集
3. PDF报告生成 + PDF转图片发送
4. 与现有推荐引擎对接

使用方式：
  python3 wechat_bot.py --mode itchat      # 个人微信模式（扫码登录）
  python3 wechat_bot.py --mode webhook     # Webhook模式（兼容企业微信等）
  python3 wechat_bot.py --mode api         # API模式（自定义集成）
"""

import sys
import os
import json
import io
import re
import datetime
import argparse
import tempfile
from pathlib import Path

# 确保能找到同级模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# PDF转图片工具
# ============================================================
def pdf_page_to_image(pdf_path, page_num=0, dpi=200):
    """将PDF指定页转换为PNG图片（字节流）"""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=dpi, first_page=page_num+1, last_page=page_num+1)
        if not images: return None
        buf = io.BytesIO()
        images[0].save(buf, format='PNG')
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"PDF转图片失败: {e}")
        return None

def pdf_to_images(pdf_path, dpi=150):
    """将PDF所有页转换为PNG图片列表"""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, dpi=dpi)
        bufs = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            bufs.append(buf)
        return bufs
    except Exception as e:
        print(f"PDF转图片失败: {e}")
        return []


# ============================================================
# 问答引擎（用于通过对话收集用户信息）
# ============================================================

class QuestionnaireEngine:
    """一步步收集用户信息的问答引擎"""
    
    def __init__(self):
        self.sessions = {}
    
    def get_or_create(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "step": 0,
                "data": {},
                "complete": False
            }
        return self.sessions[user_id]
    
    def reset(self, user_id):
        if user_id in self.sessions:
            self.sessions[user_id] = {"step": 0, "data": {}, "complete": False}
    
    def get_current_question(self, user_id):
        """获取当前要问的问题"""
        session = self.get_or_create(user_id)
        questions = self._get_questions()
        if session["step"] >= len(questions):
            return None
        return questions[session["step"]]
    
    def process_answer(self, user_id, answer):
        """处理用户回答，推进到下一步"""
        session = self.get_or_create(user_id)
        questions = self._get_questions()
        if session["step"] >= len(questions):
            session["complete"] = True
            return None, self._build_profile(session["data"])
        
        current_q = questions[session["step"]]
        # 保存答案
        session["data"][current_q["key"]] = answer.strip()
        session["step"] += 1
        
        # 检查是否完成
        if session["step"] >= len(questions):
            session["complete"] = True
            return None, self._build_profile(session["data"])
        
        next_q = questions[session["step"]]
        return next_q, None
    
    def _get_questions(self):
        """问题列表（按顺序，适合微信对话形式）"""
        return [
            {"key": "name", "question": "👋 你好！我是雪峰人AI升学顾问。先告诉我你叫什么名字？", "type": "text"},
            {"key": "school", "question": "📚 你在哪个高中读书？（学校名称）", "type": "text"},
            {"key": "grade", "question": "📖 你现在是高几？", "type": "choice", "options": ["高一", "高二", "高三"]},
            {"key": "subject_choice", "question": "🔬 你选的是什么科目组合？（如：物化生、物化地、历政地）", "type": "text"},
            {"key": "total_score", "question": "📊 最近一次考试总分是多少？（如：622分）", "type": "text"},
            {"key": "total_rank", "question": "📊 年级排名是多少？（如：第5名）", "type": "text"},
            {"key": "school_size", "question": "📊 你们年级总共有多少人？", "type": "text"},
            {"key": "math_score", "question": "📐 数学考了多少分？", "type": "text"},
            {"key": "chinese_score", "question": "📖 语文考了多少分？", "type": "text"},
            {"key": "english_score", "question": "🇬🇧 英语考了多少分？", "type": "text"},
            {"key": "physics_score", "question": "⚡ 物理考了多少分？（如没选物理就写0）", "type": "text"},
            {"key": "chemistry_score", "question": "🧪 化学考了多少分？（如没选化学就写0）", "type": "text"},
            {"key": "biology_score", "question": "🔬 生物考了多少分？（如没选生物就写0）", "type": "text"},
            {"key": "family", "question": "🏠 家庭情况：你父母是做什么工作的？（普通工薪、做生意、开公司等）", "type": "text"},
            {"key": "interest", "question": "💡 你未来想做什么？比如：当程序员、当老师、创业、出国留学、继承家业？", "type": "text"},
            {"key": "target", "question": "🎯 你有目标大学或专业方向吗？比如想冲浙大计算机，或者想学医？", "type": "text"},
        ]
    
    def _build_profile(self, data):
        """将收集到的数据转为推荐引擎可用的profile"""
        score = int(data.get("total_score", 0) or 0)
        rank = int(data.get("total_rank", 0) or 0)
        school_size = int(data.get("school_size", 500) or 500)
        
        # 估算省排名
        prov_rank_min = max(1, int(rank * 0.8 * (450000 / school_size))) if rank > 0 else 0
        prov_rank_max = max(1, int(rank * 1.2 * (450000 / school_size))) if rank > 0 else 0
        
        profile = {
            "name": data.get("name", "同学"),
            "school": data.get("school", ""),
            "grade": data.get("grade", "高一"),
            "elective": [],
            "estimated_score": score,
            "estimated_score_min": max(0, score - 15),
            "estimated_score_max": score + 15,
            "estimated_preovince_rank_min": prov_rank_min,
            "estimated_province_rank_max": prov_rank_max,
            "school_size": school_size,
            "exam_scores": {
                "数学": int(data.get("math_score", 0) or 0),
                "语文": int(data.get("chinese_score", 0) or 0),
                "英语": int(data.get("english_score", 0) or 0),
                "物理": int(data.get("physics_score", 0) or 0),
                "化学": int(data.get("chemistry_score", 0) or 0),
                "生物": int(data.get("biology_score", 0) or 0),
            },
            "exam_ranks": {},  # 没有单科排名数据
            "family_background": data.get("family", ""),
            "interests": data.get("interest", ""),
            "life_direction": data.get("interest", ""),
            "target": data.get("target", ""),
        }
        return profile


# ============================================================
# 核心消息处理器（复用推荐引擎逻辑）
# ============================================================

class WeChatMessageHandler:
    """微信消息处理器 - 对接推荐引擎和LLM聊天"""
    
    def __init__(self):
        self.questionnaire = QuestionnaireEngine()
        self.qa_mode_users = set()  # 处于问答模式的用户
        from recommend import AdmissionRecommender
        
    def handle_message(self, user_id, msg, msg_type="text"):
        """处理微信消息，返回回复内容（文本+可选的图片路径）"""
        
        # 检查是否在问答模式
        if user_id in self.qa_mode_users:
            return self._handle_qa(user_id, msg)
        
        msg = msg.strip()
        
        # 命令检测
        if msg in ["/开始", "/问答", "咨询", "评估"]:
            self.qa_mode_users.add(user_id)
            self.questionnaire.reset(user_id)
            q = self.questionnaire.get_current_question(user_id)
            return {"text": f"📋 好的，我来给你做一次全面的升学评估！\n\n{q['question']}", "image": None}
        
        if msg in ["/报告", "报告", "我的报告"]:
            return self._generate_report(user_id, msg)
        
        if msg in ["/帮助", "帮助", "菜单"]:
            return self._show_menu()
        
        # 默认：LLM聊天
        return self._chat_with_llm(user_id, msg)
    
    def _handle_qa(self, user_id, msg):
        """处理问答模式"""
        next_q, profile = self.questionnaire.process_answer(user_id, msg)
        if next_q:
            return {"text": f"📝 谢谢！接下来：\n\n{next_q['question']}", "image": None}
        else:
            # 问答完成
            self.qa_mode_users.discard(user_id)
            # 生成报告
            report_text = self._generate_report_text(profile)
            # 也生成PDF
            pdf_path = self._generate_pdf_report(profile)
            image_path = None
            if pdf_path:
                images = pdf_to_images(pdf_path, dpi=150)
                if images:
                    # 保存第一页为图片
                    img_path = f"/tmp/wechat_report_{user_id}.png"
                    with open(img_path, 'wb') as f:
                        f.write(images[0].getvalue())
                    image_path = img_path
            return {
                "text": f"✅ 信息收集完成！以下是你的升学分析报告：\n\n{report_text}\n\n💡 发送「继续」可以继续聊天咨询，发送「/开始」可以重新评估。",
                "image": image_path
            }
    
    def _chat_with_llm(self, user_id, msg):
        """对接LLM聊天"""
        import requests
        try:
            # 调用本地API
            resp = requests.post(
                "http://localhost:8081/api/chat",
                json={"user": user_id, "message": msg},
                timeout=30
            )
            data = resp.json()
            reply = data.get("reply", "（AI暂时无法回答）")
            # 移除markdown标记，适应微信阅读
            reply = reply.replace("**", "").replace("## ", "▪️ ").replace("# ", "📌 ")
            return {"text": reply, "image": None}
        except Exception as e:
            return {"text": f"（网络错误，请稍后再试）", "image": None}
    
    def _generate_report(self, user_id, msg):
        from recommend import USER_PROFILES, AdmissionRecommender, get_merged
        if user_id not in USER_PROFILES:
            return {"text": "⚠️ 系统中没有你的信息。发送「/开始」先完成信息收集。", "image": None}
        try:
            profile = get_merged(user_id)
            report_text = self._generate_report_text(profile)
            pdf_path = self._generate_pdf_report(profile)
            image_path = None
            if pdf_path:
                images = pdf_to_images(pdf_path, dpi=150)
                if images:
                    img_path = f"/tmp/wechat_report_{user_id}.png"
                    with open(img_path, 'wb') as f:
                        f.write(images[0].getvalue())
                    image_path = img_path
            return {"text": report_text, "image": image_path}
        except Exception as e:
            return {"text": f"生成报告时出错：{e}", "image": None}
    
    def _generate_report_text(self, profile):
        """生成简版报告文本（微信友好）"""
        from recommend import AdmissionRecommender
        try:
            report = AdmissionRecommender(profile).generate_full_report()
            name = report["user_name"]
            score_min = report.get("estimated_score_min", 0)
            score_max = report.get("estimated_score_max", 0)
            segment = report.get("segment", {}).get("level", "")
            
            lines = [
                f"📋 {name} 的升学分析报告",
                f"━━━━━━━━━━━━━━━━",
                f"🎯 预估分数：{score_min}-{score_max}分 | 定位：{segment}",
                f"",
                f"🏆 冲稳保院校推荐：",
            ]
            
            # 冲稳保分析
            cwb = report.get("chong_wen_bao", {})
            for level_key, level_label in [("chong","🚀 冲刺"), ("wen","✅ 稳妥"), ("bao","🛡️ 保底")]:
                schools = cwb.get(level_key, [])
                if schools:
                    names = [s.get("school","?")[:10] for s in schools[:3]]
                    lines.append(f"  {level_label}：{'、'.join(names)}")
            
            lines.append(f"")
            lines.append(f"💡 核心建议：")
            majors = report.get("majors", [])
            for m in majors[:5]:
                if m.get("suitable"):
                    schools = m.get("schools", [])
                    school_names = [s.get("school","?")[:8] for s in schools[:2]]
                    lines.append(f"  {m['priority']} {m['major']} → {'、'.join(school_names)}")
            
            lines.append(f"")
            lines.append(f"📈 时间线：")
            tl = report.get("timeline", [])
            for t in tl[:5]:
                events = t.get("events", [])
                for e in events[:2]:
                    lines.append(f"  📅 {e}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"生成报告失败：{e}"
    
    def _generate_pdf_report(self, profile):
        """生成PDF报告"""
        try:
            from generate_pdf import generate_user_report
            from config import DOWNLOAD_DIR
            name = profile.get("name", "user")
            pdf_path = os.path.join(DOWNLOAD_DIR, f"{name}_微信报告.pdf")
            generate_user_report(profile, pdf_path)
            return pdf_path
        except Exception as e:
            print(f"PDF生成失败: {e}")
            return None
    
    def _show_menu(self):
        return {"text": f"""🤖 雪峰人AI升学顾问 - 微信版
━━━━━━━━━━━━━━━━━━
📋 发送「/开始」开始信息收集
📊 发送「/报告」查看我的报告
💬 直接输入问题与我对话
❓ 发送「/帮助」显示此菜单

💡 提示：建议先发送「/开始」
让我了解你的情况，再给出精准建议！
━━━━━━━━━━━━━━━━━━
Powered by 雪峰人AI v2.0""", "image": None}


# ============================================================
# Webhook模式（兼容企业微信/第三方平台）
# ============================================================

def run_webhook(port=9090):
    """启动Webhook API服务"""
    from flask import Flask, request, jsonify
    import requests as http_requests
    
    app = Flask(__name__)
    handler = WeChatMessageHandler()
    
    @app.route("/webhook", methods=["POST"])
    def webhook():
        data = request.json
        if not data:
            return jsonify({"error": "no data"}), 400
        
        user_id = data.get("user_id", data.get("from", "anonymous"))
        msg = data.get("message", data.get("text", ""))
        msg_type = data.get("type", "text")
        
        result = handler.handle_message(user_id, msg, msg_type)
        
        response = {"reply": result["text"]}
        if result["image"]:
            # 返回图片base64
            import base64
            with open(result["image"], "rb") as f:
                response["image_base64"] = base64.b64encode(f.read()).decode()
        
        return jsonify(response)
    
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "2.0"})
    
    print(f"🤖 微信机器人Webhook服务启动，端口: {port}")
    print(f"   POST /webhook  — 接收消息并返回回复")
    print(f"   GET  /health   — 健康检查")
    print(f"\n📌 使用方式：将企业微信群机器人的Webhook地址指向本服务")
    print(f"   或通过第三方平台（如WxPusher）将微信消息转发到此API")
    app.run(host="0.0.0.0", port=port, debug=False)


# ============================================================
# itchat 模式（个人微信）
# ============================================================

def run_itchat():
    """启动个人微信机器人模式"""
    try:
        import itchat
        from itchat.content import TEXT, PICTURE
    except ImportError:
        print("❌ 需要安装 itchat：pip3 install itchat")
        print("   注意：个人微信机器人存在账号风险，建议使用Webhook模式")
        sys.exit(1)
    
    handler = WeChatMessageHandler()
    
    @itchat.msg_register(TEXT)
    def text_reply(msg):
        user_id = msg["FromUserName"]
        text = msg["Text"]
        result = handler.handle_message(user_id, text)
        
        if result["image"]:
            itchat.send_image(result["image"], user_id)
            itchat.send("@img@已发送报告图片，请查看↑", user_id)
        if result["text"]:
            itchat.send(result["text"], user_id)
    
    print("🤖 个人微信机器人启动中...")
    print("📱 请扫描二维码登录微信")
    itchat.auto_login(hotReload=True)
    itchat.run()


# ============================================================
# API模式（独立Flask服务，可被其他程序调用）
# ============================================================

def run_api(port=9091):
    """启动API模式（纯消息处理接口）"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    handler = WeChatMessageHandler()
    
    @app.route("/api/wechat/chat", methods=["POST"])
    def chat():
        data = request.json
        user_id = data.get("user_id", "anonymous")
        msg = data.get("message", "")
        result = handler.handle_message(user_id, msg)
        
        response = {"reply": result["text"]}
        if result["image"]:
            import base64
            with open(result["image"], "rb") as f:
                response["image_base64"] = base64.b64encode(f.read()).decode()
        return jsonify(response)
    
    @app.route("/api/wechat/start_qa", methods=["POST"])
    def start_qa():
        user_id = request.json.get("user_id", "anonymous")
        handler.qa_mode_users.add(user_id)
        handler.questionnaire.reset(user_id)
        q = handler.questionnaire.get_current_question(user_id)
        return jsonify({"question": q["question"], "step": 1, "total": len(handler.questionnaire._get_questions())})
    
    @app.route("/api/wechat/report", methods=["GET"])
    def get_report():
        user_id = request.args.get("user_id", "anonymous")
        result = handler._generate_report(user_id, "")
        return jsonify({"text": result["text"], "has_image": result["image"] is not None})
    
    @app.route("/api/wechat/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "version": "2.0"})
    
    print(f"🤖 微信机器人API服务启动，端口: {port}")
    print(f"   POST /api/wechat/chat      — 聊天接口")
    print(f"   POST /api/wechat/start_qa  — 开始问答")
    print(f"   GET  /api/wechat/report    — 获取报告")
    app.run(host="0.0.0.0", port=port, debug=False)


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="雪峰人微信机器人")
    parser.add_argument("--mode", choices=["itchat", "webhook", "api"], default="webhook",
                      help="运行模式：itchat(个人微信)/webhook(Webhook)/api(API服务)")
    parser.add_argument("--port", type=int, default=9090, help="服务端口（webhook/api模式）")
    args = parser.parse_args()
    
    if args.mode == "itchat":
        run_itchat()
    elif args.mode == "webhook":
        run_webhook(port=args.port)
    elif args.mode == "api":
        run_api(port=args.port)
