#!/usr/bin/env python3
"""
企业微信客服模式 - 雪峰人AI升学顾问 v2.1
============================================
核心变化：使用企业微信「客服」API，主动轮询拉取消息
✅ 不需要回调URL（解决国内墙的问题）
✅ 沙箱只需往外连微信服务器（出站访问不受限）
✅ 用户在企业微信App里跟「客服」聊天

使用流程：
  1. 注册企业微信 → 开启客服功能
  2. 获取 CorpID + Secret + open_kfid
  3. 把这三个信息配到 wecom_config.json
  4. 运行本服务即可自动轮询 + 回复

启动：
  python3 wecom_bot.py --config wecom_config.json
"""

import os
import sys
import json
import time
import datetime
import threading
import io
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置
CORP_ID = ""
SECRET = ""
OPEN_KFID = ""  # 客服账号ID

TOKEN_CACHE = {"access_token": "", "expires_at": 0}
MSG_CURSOR = ""  # 消息游标


def get_access_token():
    """获取企业微信access_token"""
    now = time.time()
    if TOKEN_CACHE["access_token"] and TOKEN_CACHE["expires_at"] > now + 60:
        return TOKEN_CACHE["access_token"]
    
    resp = requests.get(
        "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        params={"corpid": CORP_ID, "corpsecret": SECRET},
        timeout=10
    )
    data = resp.json()
    if data.get("errcode") == 0:
        TOKEN_CACHE["access_token"] = data["access_token"]
        TOKEN_CACHE["expires_at"] = now + data["expires_in"]
        return data["access_token"]
    else:
        print(f"❌ Token获取失败: {data}")
        return None


def sync_messages():
    """轮询拉取新消息"""
    global MSG_CURSOR
    token = get_access_token()
    if not token:
        return []
    
    payload = {
        "open_kfid": OPEN_KFID,
        "token": MSG_CURSOR,
        "limit": 20
    }
    try:
        resp = requests.post(
            "https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg",
            params={"access_token": token},
            json=payload,
            timeout=10
        )
        data = resp.json()
        if data.get("errcode") != 0:
            print(f"sync_msg失败: {data}")
            return []
        
        MSG_CURSOR = data.get("next_cursor", MSG_CURSOR)
        has_more = data.get("has_more", 0)
        msg_list = data.get("msg_list", [])
        
        # 过滤出客户发的文本消息（排除系统事件、排除我们自己发的回复）
        new_msgs = []
        for msg in msg_list:
            if msg.get("msgtype") == "text" and msg.get("sender_type") == "user":
                new_msgs.append(msg)
        
        return new_msgs
    except Exception as e:
        print(f"sync_msg异常: {e}")
        return []


def send_text(open_kfid, to_user, text):
    """发送文本消息"""
    token = get_access_token()
    if not token:
        return False
    payload = {
        "open_kfid": open_kfid,
        "touser": to_user,
        "msgtype": "text",
        "text": {"content": text[:2048]}
    }
    resp = requests.post(
        "https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg",
        params={"access_token": token},
        json=payload,
        timeout=10
    )
    result = resp.json()
    if result.get("errcode") != 0:
        print(f"发送消息失败: {result}")
    return result.get("errcode") == 0


def upload_image(image_path):
    """上传图片到企业微信临时素材"""
    token = get_access_token()
    if not token:
        return None
    with open(image_path, 'rb') as f:
        resp = requests.post(
            "https://qyapi.weixin.qq.com/cgi-bin/media/upload",
            params={"access_token": token, "type": "image"},
            files={"media": f},
            timeout=30
        )
    data = resp.json()
    if data.get("errcode") == 0:
        return data.get("media_id")
    return None


def send_image(open_kfid, to_user, image_path):
    """发送图片"""
    media_id = upload_image(image_path)
    if not media_id:
        return False
    token = get_access_token()
    if not token:
        return False
    payload = {
        "open_kfid": open_kfid,
        "touser": to_user,
        "msgtype": "image",
        "image": {"media_id": media_id}
    }
    resp = requests.post(
        "https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg",
        params={"access_token": token},
        json=payload,
        timeout=10
    )
    return resp.json().get("errcode") == 0


# ============================================================
# 问答式信息收集
# ============================================================

QA_SESSIONS = {}

QUESTIONS = [
    ("name", "👋 你叫什么名字？"),
    ("school", "📚 你在哪个高中读书？"),
    ("grade", "📖 现在高几？（高一/高二/高三）"),
    ("subjects", "🔬 选科组合是？（如：物化生、历政地）"),
    ("total_score", "📊 最近考试总分多少？"),
    ("total_rank", "📊 年级排名第几？"),
    ("school_size", "📊 年级总共有多少人？"),
    ("math", "📐 数学多少分？"),
    ("chinese", "📖 语文多少分？"),
    ("english", "🇬🇧 英语多少分？"),
    ("physics", "⚡ 物理多少分？（没选写0）"),
    ("chemistry", "🧪 化学多少分？（没选写0）"),
    ("bio_geo", "🔬 生物/地理多少分？（没选写0）"),
    ("family", "🏠 父母做什么工作？（工薪/做生意/开公司）"),
    ("interest", "💡 未来想做什么？（程序员/老师/创业/出国）"),
    ("target", "🎯 目标大学或专业？（如冲华工计算机）"),
]


def handle_message(user_id, text):
    """处理消息，返回回复内容"""
    text = text.strip()
    
    # 问答模式
    if user_id in QA_SESSIONS:
        return handle_qa(user_id, text)
    
    # 命令
    if text in ["开始", "评估", "/start"]:
        return start_qa(user_id)
    if text in ["报告", "我的报告"]:
        return generate_report(user_id)
    if text in ["帮助", "菜单", "？", "/help"]:
        return show_menu()
    
    # 默认LLM聊天
    return chat_with_llm(user_id, text)


def start_qa(user_id):
    QA_SESSIONS[user_id] = {"step": 0, "data": {}}
    q = QUESTIONS[0][1]
    return {"type": "text", "content": f"📋 开始全面评估！\n\n{q}\n\n（发送「退出」取消）"}


def handle_qa(user_id, text):
    if text in ["退出", "取消"]:
        del QA_SESSIONS[user_id]
        return {"type": "text", "content": "已退出。发送「开始」重新评估。"}
    
    session = QA_SESSIONS[user_id]
    step = session["step"]
    
    session["data"][QUESTIONS[step][0]] = text
    session["step"] += 1
    
    if session["step"] >= len(QUESTIONS):
        del QA_SESSIONS[user_id]
        return generate_full_report(session["data"])
    
    next_q = QUESTIONS[session["step"]][1]
    return {"type": "text", "content": f"📝 谢谢！接下来：\n\n{next_q}"}


def generate_full_report(data):
    """生成完整报告"""
    try:
        score = int(data.get("total_score", 0) or 0)
        rank = int(data.get("total_rank", 0) or 0)
        school_size = int(data.get("school_size", 500) or 500)
        
        prov_min = max(1, int(rank * 0.8 * (450000 / school_size))) if rank > 0 else 0
        prov_max = max(1, int(rank * 1.2 * (450000 / school_size))) if rank > 0 else 0
        
        profile = {
            "name": data.get("name", "同学"),
            "school": data.get("school", ""),
            "estimated_score": score,
            "estimated_score_min": max(0, score-15),
            "estimated_score_max": score+15,
            "estimated_province_rank_min": prov_min,
            "estimated_province_rank_max": prov_max,
            "school_size": school_size,
            "exam_scores": {
                "数学": int(data.get("math",0) or 0),
                "语文": int(data.get("chinese",0) or 0),
                "英语": int(data.get("english",0) or 0),
                "物理": int(data.get("physics",0) or 0),
                "化学": int(data.get("chemistry",0) or 0),
                "生物": int(data.get("bio_geo",0) or 0),
            },
            "family_background": data.get("family", ""),
            "interests": data.get("interest", ""),
        }
        
        from recommend import AdmissionRecommender
        report = AdmissionRecommender(profile).generate_full_report()
        name = report["user_name"]
        
        lines = [f"📋 {name} 的升学分析报告", "━━━━━━━━━━━━━━━"]
        lines.append(f"🎯 预估：{report.get('estimated_score_min',0)}-{report.get('estimated_score_max',0)}分 | {report.get('segment',{}).get('level','')}")
        lines.append("")
        
        cwb = report.get("chong_wen_bao", {})
        lines.append("🏆 院校推荐：")
        for lk, ll in [("chong","🚀 冲刺"),("wen","✅ 稳妥"),("bao","🛡️ 保底")]:
            schools = cwb.get(lk, [])
            if schools:
                names = [s.get("school","?")[:10] for s in schools[:3]]
                lines.append(f"  {ll}：{'、'.join(names)}")
        
        lines.extend(["", "🎯 推荐专业："])
        for m in report.get("majors", [])[:5]:
            if m.get("suitable"):
                lines.append(f"  {m['priority']} {m['major']}")
        
        text = "\n".join(lines)
        
        # 生成PDF转图片
        from generate_pdf import generate_user_report
        from pdf2image import convert_from_path
        pdf_path = f"/tmp/wecom_report_{user_id}.pdf"
        generate_user_report(profile, pdf_path)
        images = convert_from_path(pdf_path, dpi=150)
        if images:
            img_path = f"/tmp/wecom_report_{user_id}.png"
            images[0].save(img_path, "PNG")
            return {"type": "text_and_image", "content": text, "image": img_path}
        
        return {"type": "text", "content": text}
    except Exception as e:
        return {"type": "text", "content": f"生成报告时出错，请重试或直接提问。"}


def generate_report(user_id):
    return {"type": "text", "content": "请先发送「开始」完成信息收集，再获取报告。"}


def chat_with_llm(user_id, text):
    """调用本地LLM"""
    try:
        resp = requests.post(
            "http://localhost:8081/api/chat",
            json={"user": user_id, "message": text},
            timeout=60
        )
        data = resp.json()
        reply = data.get("reply", "（暂时无法回答）")
        reply = reply.replace("**", "").replace("## ", "▪️ ").replace("# ", "")
        return {"type": "text", "content": reply[:2000]}
    except Exception as e:
        return {"type": "text", "content": f"（AI思考中请稍后，再发一次就行）"}


def show_menu():
    return {"type": "text", "content": """🤖 雪峰人AI升学顾问
━━━━━━━━━━━━━━
📋 发送「开始」→ 16步信息收集
📊 发送「报告」→ 查看报告
💬 直接输入→ 随便问
                   
💡 建议先做评估"""}


# ============================================================
# 主轮询循环
# ============================================================

def poll_loop():
    """主循环：每3秒轮询新消息并处理"""
    print("🤖 客服消息轮询已启动（每3秒）")
    while True:
        try:
            msgs = sync_messages()
            for msg in msgs:
                user_id = msg.get("external_userid", "")
                content = msg.get("text", {}).get("content", "")
                msg_id = msg.get("msgid", "")
                
                if not user_id or not content:
                    continue
                
                print(f"📩 {user_id[:8]}: {content[:50]}")
                
                # 处理消息
                result = handle_message(user_id, content)
                
                if result["type"] == "text":
                    send_text(OPEN_KFID, user_id, result["content"])
                elif result["type"] == "text_and_image":
                    send_text(OPEN_KFID, user_id, result["content"])
                    if result.get("image"):
                        time.sleep(1)
                        send_image(OPEN_KFID, user_id, result["image"])
        except Exception as e:
            print(f"轮询异常: {e}")
        
        time.sleep(3)


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="企业微信客服AI Bot")
    parser.add_argument("--config", required=True, help="配置文件JSON路径")
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        print("   格式: {\"corp_id\":\"xxx\",\"secret\":\"xxx\",\"open_kfid\":\"xxx\"}")
        sys.exit(1)
    
    with open(args.config) as f:
        cfg = json.load(f)
    
    CORP_ID = cfg.get("corp_id", "")
    SECRET = cfg.get("secret", "")
    OPEN_KFID = cfg.get("open_kfid", "")
    
    if not all([CORP_ID, SECRET, OPEN_KFID]):
        print("❌ 配置缺少必填项：corp_id / secret / open_kfid")
        sys.exit(1)
    
    print(f"""
╔══════════════════════════════════════════╗
║   🤖 雪峰人AI - 企业微信客服模式 v2.1    ║
╠══════════════════════════════════════════╣
║   ✅ 不需要回调URL                        ║
║   ✅ 沙箱主动轮询拉取消息                  ║
║   ✅ 支持PDF报告转图片发送                 ║
║                                          ║
║   CorpID : {CORP_ID[:8]}...                      ║
║   open_kfid : {OPEN_KFID[:8]}...                  ║
╚══════════════════════════════════════════╝
""")
    
    # 先验证配置
    token = get_access_token()
    if token:
        print("✅ 配置验证通过！启动轮询...")
        poll_loop()
    else:
        print("❌ 配置验证失败，请检查 CorpID 和 Secret")
