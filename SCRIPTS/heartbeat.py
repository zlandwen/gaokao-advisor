#!/usr/bin/env python3
"""
心跳任务：每周自动检查最新数据并更新知识库
运行方式：由cron每周触发一次
日志文件：/workspace/SCRIPTS/heartbeat.log
"""

import json, os, sys, datetime, subprocess, sqlite3

BASE = "/workspace/SCRIPTS"
LOG = os.path.join(BASE, "heartbeat.log")
DB = os.path.join(BASE, "knowledge_base.db")
UPDATES = os.path.join(BASE, "user_updates.json")

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{now}] {msg}"
    print(line)
    with open(LOG, 'a') as f:
        f.write(line + "\n")

def check_gaokao_line():
    """检查广东教育考试院是否有最新录取分数线"""
    log("📡 检查广东高考录取线更新...")
    try:
        import urllib.request
        url = "https://eea.gd.gov.cn/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        # 检查是否有"录取"关键词
        if "录取" in html and "分数" in html:
            log("  ✅ 广东省教育考试院可访问")
        else:
            log("  ⚠️ 页面结构有变化")
    except Exception as e:
        log(f"  ❌ 访问失败: {str(e)[:50]}")

def check_qiangji_policy():
    """检查阳光高考平台强基政策更新"""
    log("📡 检查强基计划政策更新...")
    try:
        import urllib.request
        url = "https://gaokao.chsi.com.cn/gkxx/qj/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        if "2027" in html:
            log("  ⚠️ 2027年强基政策已发布！需要手动更新数据库")
    except Exception as e:
        log(f"  ❌ 访问失败: {str(e)[:50]}")

def check_db_status():
    """检查数据库状态"""
    if os.path.exists(DB):
        size = os.path.getsize(DB)
        try:
            conn = sqlite3.connect(DB)
            uni_count = conn.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
            score_count = conn.execute("SELECT COUNT(*) FROM admission_scores").fetchone()[0]
            conn.close()
            log(f"  📊 数据库: {uni_count}所大学, {score_count}条录取数据, {size//1024}KB")
        except:
            log(f"  📊 数据库文件: {size//1024}KB（但结构异常）")
    else:
        log("  ❌ 数据库文件不存在!")

def check_server():
    """检查Web服务是否正常运行"""
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://127.0.0.1:8081/", timeout=5)
        log(f"  🌐 Web服务: 运行中(HTTP {resp.status})")
    except:
        log("  ❌ Web服务未运行，尝试重启...")
        subprocess.Popen(["nohup", "python3", os.path.join(BASE, "web_rec_server.py"), "&"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def check_training_data():
    """检查训练数据积累情况"""
    path = os.path.join(BASE, "training_data.jsonl")
    if os.path.exists(path):
        count = sum(1 for _ in open(path))
        log(f"  💬 训练数据: {count}条对话记录")
    path2 = os.path.join(BASE, "questions.json")
    if os.path.exists(path2):
        with open(path2) as f:
            qs = json.load(f)
        log(f"  💬 对话历史: {len(qs)}条")

if __name__ == "__main__":
    log("=" * 50)
    log("❤️  心跳任务启动")
    check_gaokao_line()
    check_qiangji_policy()
    check_db_status()
    check_server()
    check_training_data()
    log("✅ 心跳任务完成")
